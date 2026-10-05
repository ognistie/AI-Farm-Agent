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
    files, skipped, total, truncated = {}, [], 0, False
    for root, dirs, names in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
        for name in sorted(names):
            path = os.path.join(root, name)
            rel = os.path.relpath(path, folder).replace("\\", "/")
            if os.path.splitext(name)[1].lower() not in TEXT_EXT:
                skipped.append(rel)
                continue
            if len(files) >= MAX_FILES_READ:
                truncated = True
                skipped.append(rel)
                continue
            try:
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
            except (UnicodeDecodeError, OSError):
                skipped.append(rel)
                continue
            if total + len(text) > MAX_CHARS_READ:
                truncated = True
                skipped.append(rel)
                continue
            files[rel] = text
            total += len(text)
    return {"files": files, "skipped": skipped, "truncated": truncated}


def safe_rel(folder: str, rel: str) -> str | None:
    """Caminho absoluto se `rel` fica dentro do projeto; senao None."""
    rel = (rel or "").replace("\\", "/").strip()
    while rel.startswith("./"):
        rel = rel[2:]
    if not rel or os.path.isabs(rel) or ":" in rel or ".." in rel.split("/"):
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
    if not files:
        return "nenhum arquivo alterado"
    if len(files) > MAX_FILES_EDIT:
        return f"alterações demais ({len(files)} arquivos, máx {MAX_FILES_EDIT})"
    for f in files:
        path, content = f.get("path", ""), f.get("content")
        if safe_rel(folder, path) is None:
            return f"caminho fora do projeto: {path}"
        if not isinstance(content, str) or not content.strip():
            return f"conteúdo vazio para {path}"
        if path.lower().endswith((".html", ".htm")) and "<" not in content:
            return f"{path} não parece HTML"
    return ""


def apply_edit(folder: str, files: list) -> dict:
    folder = os.path.realpath(folder)   # nome curto 8.3 (ex.: USUARI~1) quebrava os caminhos relativos
    err = validate_edit(folder, files)
    if err:
        return {"ok": False, "error": err}
    stamp = time.strftime("%Y%m%d-%H%M%S")
    vdir = os.path.join(folder, VERSIONS_DIR, stamp)
    os.makedirs(vdir, exist_ok=True)
    ignore = os.path.join(folder, VERSIONS_DIR, ".gitignore")
    if not os.path.exists(ignore):          # versoes do "desfaz" nunca vao para o git do projeto
        with open(ignore, "w", encoding="utf-8") as fh:
            fh.write("*\n")
    manifest = {"created": [], "changed": []}
    for f in files:
        full = safe_rel(folder, f["path"])
        rel = os.path.relpath(full, folder).replace("\\", "/")
        if os.path.exists(full):
            dst = os.path.join(vdir, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(full, dst)
            manifest["changed"].append(rel)
        else:
            manifest["created"].append(rel)
    with open(os.path.join(vdir, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
    for f in files:
        full = safe_rel(folder, f["path"])
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="") as fh:
            fh.write(f["content"])
    _prune(folder)
    return {"ok": True, "changed": manifest["changed"] + manifest["created"], "version": stamp}


def _versions(folder: str) -> list[str]:
    base = os.path.join(folder, VERSIONS_DIR)
    if not os.path.isdir(base):
        return []
    return sorted(d for d in os.listdir(base) if os.path.isfile(os.path.join(base, d, "manifest.json")))


def _prune(folder: str) -> None:
    for old in _versions(folder)[:-MAX_VERSIONS]:
        shutil.rmtree(os.path.join(folder, VERSIONS_DIR, old), ignore_errors=True)


def revert_last(folder: str) -> dict:
    folder = os.path.realpath(folder)   # nome curto 8.3 (ex.: USUARI~1) quebrava os caminhos relativos
    vs = _versions(folder)
    if not vs:
        return {"ok": False, "error": "não há versão anterior para voltar"}
    vdir = os.path.join(folder, VERSIONS_DIR, vs[-1])
    with open(os.path.join(vdir, "manifest.json"), encoding="utf-8") as fh:
        manifest = json.load(fh)
    restored = []
    for rel in manifest.get("changed", []):
        src, dst = os.path.join(vdir, rel), safe_rel(folder, rel)
        if dst and os.path.exists(src):
            shutil.copy2(src, dst)
            restored.append(rel)
    for rel in manifest.get("created", []):
        dst = safe_rel(folder, rel)
        if dst and os.path.exists(dst):
            os.remove(dst)
            restored.append(f"-{rel}")
    shutil.rmtree(vdir, ignore_errors=True)
    return {"ok": True, "restored": restored}
