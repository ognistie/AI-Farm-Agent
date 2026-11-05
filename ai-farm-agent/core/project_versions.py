"""
Edicao de projeto existente com versao anterior guardada.

"faca um site" -> "troque a cor do titulo" -> "desfaz"
Cada edicao copia ANTES os arquivos que vai mudar para
<projeto>/.ai_versions/<AAAAmmdd-HHMMSS>/ e registra quais eram novos.
"desfaz" restaura a ultima versao (e apaga os arquivos que ela criou).

Caminhos vindos do modelo sao validados: relativos, dentro da pasta do
projeto, sem '..', sem tocar .ai_versions/.git.
"""

from __future__ import annotations

import json
import os
import shutil
import time
import ast
import hashlib
import tempfile
import threading
import uuid
import re
from pathlib import Path, PurePosixPath

_edit_lock = threading.RLock()

VERSIONS_DIR = ".ai_versions"
MAX_VERSIONS = 15
SKIP_DIRS = {VERSIONS_DIR, ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
             ".next", ".idea", ".vscode"}
TEXT_EXT = {".html", ".htm", ".css", ".js", ".mjs", ".ts", ".tsx", ".jsx", ".vue", ".svelte",
            ".py", ".json", ".md", ".txt", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".sql",
            ".xml", ".svg", ".sh", ".bat", ".ps1", ".env.example"}
MAX_FILES_READ = 25
MAX_CHARS_READ = 90_000
MAX_FILES_EDIT = 12


def read_project(folder: str) -> dict:
    """Arquivos de texto do projeto: {"files": {rel: conteudo}, "skipped": [rel], "truncated": bool}."""
    folder = os.path.realpath(folder)   # nome curto 8.3 (ex.: USUARI~1) quebrava os caminhos relativos
    files, skipped, total, truncated, hashes = {}, [], 0, False, {}
    for root, dirs, names in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
        for name in sorted(names):
            path = os.path.join(root, name)
            if os.path.commonpath([os.path.realpath(folder), os.path.realpath(path)]) != os.path.realpath(folder):
                skipped.append(os.path.relpath(path, folder))
                continue
            rel = os.path.relpath(path, folder).replace("\\", "/")
            if os.path.splitext(name)[1].lower() not in TEXT_EXT:
                skipped.append(rel)
                continue
            if len(files) >= MAX_FILES_READ:
                truncated = True
                skipped.append(rel)
                continue
            try:
                with open(path, 'rb') as fh:
                    raw = fh.read(MAX_CHARS_READ * 4 + 1)
                    text = raw.decode('utf-8')
            except (UnicodeDecodeError, OSError):
                skipped.append(rel)
                continue
            if total + len(text) > MAX_CHARS_READ:
                truncated = True
                skipped.append(rel)
                continue
            files[rel] = text
            hashes[rel] = hashlib.sha256(raw).hexdigest()
            total += len(text)
    return {"files": files, "skipped": skipped, "truncated": truncated, "hashes": hashes}


def safe_rel(folder: str, rel: str) -> str | None:
    """Caminho absoluto se `rel` fica dentro do projeto; senao None."""
    if not isinstance(rel, str):
        return None
    rel = rel.replace("\\", "/")
    while rel.startswith("./"):
        rel = rel[2:]
    if not rel or os.path.isabs(rel) or ":" in rel or ".." in rel.split("/"):
        return None
    if (PurePosixPath(rel).as_posix() != rel or any(part.endswith((' ', '.')) for part in rel.split('/'))
            or any(re.match(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)', part, re.I) for part in rel.split('/'))):
        return None
    if any(part.startswith('.') and part not in ('.gitignore', '.env.example') for part in rel.split('/')):
        return None
    if rel.split("/")[0] in SKIP_DIRS:
        return None
    root = os.path.realpath(folder)
    full = os.path.realpath(os.path.join(root, rel))
    return full if full.startswith(root + os.sep) else None


def validate_edit(folder: str, files: list) -> str:
    """'' se ok; senao o motivo."""
    if not folder or not os.path.isdir(folder):
        return f"pasta do projeto não existe: {folder}"
    if not isinstance(files, list) or not files:
        return "nenhum arquivo alterado"
    if len(files) > MAX_FILES_EDIT:
        return f"alterações demais ({len(files)} arquivos, máx {MAX_FILES_EDIT})"
    seen, total = set(), 0
    for f in files:
        if not isinstance(f, dict):
            return 'arquivo deve ser um objeto'
        path, content = f.get("path", ""), f.get("content")
        if not isinstance(path, str):
            return 'path deve ser texto'
        if safe_rel(folder, path) is None:
            return f"caminho fora do projeto: {path}"
        if not isinstance(content, str) or not content.strip():
            return f"conteúdo vazio para {path}"
        key = os.path.normcase(safe_rel(folder, path))
        if key in seen:
            return 'caminho duplicado'
        seen.add(key)
        total += len(content.encode('utf-8'))
        if total > 1024 * 1024:
            return 'edicao excede 1 MiB'
        if path.lower().endswith((".html", ".htm")) and "<" not in content:
            return f"{path} não parece HTML"
        try:
            if path.lower().endswith('.py'):
                ast.parse(content, filename=path)
            if path.lower().endswith('.json'):
                json.loads(content)
        except (SyntaxError, ValueError) as error:
            return f'{path}: sintaxe invalida ({type(error).__name__})'
    return ""


def apply_edit(folder: str, files: list, expected_hashes=None) -> dict:
    """Stage, publish and roll back on failure. Previous content is never silently lost."""
    with _edit_lock:
        folder = os.path.realpath(folder)
        error = validate_edit(folder, files)
        if error:
            return {"ok": False, "error": error}
        if os.path.realpath(os.path.join(folder, VERSIONS_DIR)) != os.path.join(folder, VERSIONS_DIR):
            return {'ok': False, 'error': 'Diretorio de versoes redirecionado; operacao recusada.'}
        if expected_hashes is not None:
            for entry in files:
                full = safe_rel(folder, entry['path'])
                expected = expected_hashes.get(entry['path'])
                actual = hashlib.sha256(Path(full).read_bytes()).hexdigest() if os.path.isfile(full) else None
                if actual != expected:
                    return {"ok": False, "error": "Arquivo mudou desde a leitura: " + entry['path']}
        stamp = time.strftime('%Y%m%d-%H%M%S') + f'-{time.time_ns():020d}-' + uuid.uuid4().hex[:12]
        vdir = Path(folder) / VERSIONS_DIR / stamp
        vdir.mkdir(parents=True, exist_ok=False)
        ignore = vdir.parent / '.gitignore'
        if not ignore.exists():
            ignore.write_text('*\n', encoding='utf-8')
        manifest = {'schema': 1, 'created': [], 'changed': [], 'status': 'prepared',
                    'before_hashes': {}, 'after_hashes': {}}
        staged, published = [], []
        try:
            for entry in files:
                full = safe_rel(folder, entry['path'])
                rel = os.path.relpath(full, folder).replace('\\', '/')
                if os.path.exists(full):
                    backup = vdir / rel
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(full, backup)
                    manifest['changed'].append(rel)
                    manifest['before_hashes'][rel] = hashlib.sha256(backup.read_bytes()).hexdigest()
                else:
                    manifest['created'].append(rel)
                manifest['after_hashes'][rel] = hashlib.sha256(entry['content'].encode('utf-8')).hexdigest()
                Path(full).parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='', delete=False,
                                                 dir=Path(full).parent, prefix='.ai-farm-stage-') as stream:
                    staged.append((stream.name, full, rel))
                    stream.write(entry['content'])
            (vdir / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            for source, full, rel in staged:
                os.replace(source, full)
                published.append(rel)
            for entry in files:
                if Path(safe_rel(folder, entry['path'])).read_bytes() != entry['content'].encode('utf-8'):
                    raise OSError('conteudo gravado nao confere: ' + entry['path'])
            manifest['status'] = 'committed'
            (vdir / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            _prune(folder)
            return {'ok': True, 'verified': True, 'changed': manifest['changed'] + manifest['created'], 'version': stamp}
        except OSError as failure:
            errors = []
            for rel in reversed(published):
                full = safe_rel(folder, rel)
                try:
                    if rel in manifest['changed']:
                        shutil.copy2(vdir / rel, full)
                    elif full and os.path.isfile(full):
                        os.remove(full)
                except OSError as rollback:
                    errors.append(type(rollback).__name__)
            manifest['status'] = 'rollback_failed' if errors else 'rolled_back'
            try:
                (vdir / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            except OSError:
                pass
            return {'ok': False, 'error': f'Edicao falhou: {failure}; rollback: {manifest["status"]}'}
        finally:
            for source, _, _ in staged:
                if os.path.isfile(source):
                    os.remove(source)


def _versions(folder: str) -> list[str]:
    base = os.path.join(folder, VERSIONS_DIR)
    if not os.path.isdir(base) or os.path.realpath(base) != base:
        return []
    out = []
    for d in os.listdir(base):
        path = os.path.join(base, d, "manifest.json")
        if os.path.realpath(path) != path:
            continue
        try:
            data = json.loads(Path(path).read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if data.get('status', 'committed') == 'committed':
            out.append(d)
    return sorted(out)


def _prune(folder: str) -> None:
    for old in _versions(folder)[:-MAX_VERSIONS]:
        shutil.rmtree(os.path.join(folder, VERSIONS_DIR, old), ignore_errors=True)


def revert_last(folder: str) -> dict:
    with _edit_lock:
        folder = os.path.realpath(folder)
        vs = _versions(folder)
        if not vs:
            return {"ok": False, "error": "não há versão anterior para voltar"}
        vdir = Path(folder, VERSIONS_DIR, vs[-1])
        manifest = json.loads((vdir / 'manifest.json').read_text(encoding='utf-8'))
        if (manifest.get('schema') != 1 or not isinstance(manifest.get('before_hashes'), dict)
                or not isinstance(manifest.get('after_hashes'), dict)):
            return {'ok': False, 'error': 'Versao antiga sem hashes; restaure manualmente a copia preservada.'}
        changed, created = manifest.get('changed'), manifest.get('created')
        if not isinstance(changed, list) or not isinstance(created, list):
            return {'ok': False, 'error': 'Manifesto de versao invalido.'}
        entries, staged, published = [], [], []
        try:
            # Validate EVERY precondition before touching any project file.
            for rel in changed + created:
                dst = safe_rel(folder, rel)
                if not dst or any(old[0] == dst for old in entries):
                    raise ValueError('Caminho invalido ou duplicado no manifesto.')
                current = Path(dst).read_bytes()
                if hashlib.sha256(current).hexdigest() != manifest['after_hashes'].get(rel):
                    raise ValueError('Arquivo mudou desde a edicao: ' + rel)
                previous = None
                if rel in changed:
                    src = vdir / rel
                    if src.resolve() != src:
                        raise ValueError('Backup redirecionado: ' + rel)
                    previous = src.read_bytes()
                    if hashlib.sha256(previous).hexdigest() != manifest['before_hashes'].get(rel):
                        raise ValueError('Backup alterado: ' + rel)
                entries.append((dst, current, previous, rel))
            for dst, current, previous, rel in entries:
                if previous is not None:
                    with tempfile.NamedTemporaryFile(delete=False, dir=Path(dst).parent, prefix='.ai-farm-undo-') as stream:
                        staged.append(stream.name)
                        stream.write(previous)
                    os.replace(stream.name, dst)
                else:
                    os.remove(dst)
                published.append((dst, current))
            for dst, _, previous, rel in entries:
                if (previous is None and os.path.exists(dst)) or (previous is not None and Path(dst).read_bytes() != previous):
                    raise OSError('Restauracao nao confere: ' + rel)
            manifest['status'] = 'reverted'
            (vdir / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            return {'ok': True, 'restored': [rel if previous is not None else '-' + rel for _, _, previous, rel in entries]}
        except (OSError, ValueError) as error:
            rollback_errors = []
            for dst, current in reversed(published):
                try:
                    with tempfile.NamedTemporaryFile(delete=False, dir=Path(dst).parent, prefix='.ai-farm-undo-') as stream:
                        staged.append(stream.name)
                        stream.write(current)
                    os.replace(stream.name, dst)
                except OSError as rollback:
                    rollback_errors.append(type(rollback).__name__)
            return {'ok': False, 'error': f'Desfazer recusado/falhou: {error}; rollback_errors={rollback_errors}'}
        finally:
            for source in staged:
                if os.path.isfile(source):
                    os.remove(source)
