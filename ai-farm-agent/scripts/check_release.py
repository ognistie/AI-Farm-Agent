"""Local release gate. Reports code validation separately from publication readiness.

No Git mutations, network, model calls or personal desktop actions. A passing code
gate is not a certification of production behavior across arbitrary apps/audio.
"""
import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
REPO = APP.parent
sys.path.insert(0, str(APP))


def source_digest():
    digest = hashlib.sha256()
    for base in ('agents', 'core', 'desktop', 'scripts', 'tests'):
        for path in sorted((APP / base).rglob('*')):
            if path.is_file() and path.suffix in ('.py', '.qml'):
                digest.update(path.relative_to(APP).as_posix().encode())
                digest.update(path.read_bytes())
    for path in (REPO / 'config.yaml', APP / 'main.py', APP / 'requirements.txt',
                 APP / 'requirements-windows-py311.lock.txt', REPO / 'scripts' / 'setup.ps1',
                 REPO / '.github' / 'workflows' / 'ci.yml'):
        digest.update(path.read_bytes())
    vault = REPO / 'AI-Farm-agents'
    for base in ('00 Maestro', '05 Inbox', '10 Agentes', '20 Politicas', '30 Skills',
                 '30 Tarefas de referencia', '60 Aprendizados', '70 Dicionario', '90 Sistema'):
        for path in sorted((vault / base).rglob('*.md')):
            digest.update(path.relative_to(REPO).as_posix().encode())
            digest.update(path.read_bytes())
    curation = REPO / 'docs' / 'research' / 'vault-curation.json'
    if curation.exists():
        digest.update(curation.read_bytes())
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--code-only', action='store_true', help='exit status covers code checks only')
    parser.add_argument('--output', type=Path, default=APP / 'memory' / 'release-check.json')
    args = parser.parse_args()
    logs = APP / 'memory' / 'release-check'
    logs.mkdir(parents=True, exist_ok=True)
    tmp = APP / 'memory' / 'test_tmp'; tmp.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, 'TMP': str(tmp), 'TEMP': str(tmp), 'PYTHONIOENCODING': 'utf-8'}
    report = {'schema': 1, 'python': sys.version.split()[0], 'source_digest': source_digest(), 'checks': []}
    commands = [
        ('dependencies', [sys.executable, '-m', 'pip', 'check']),
        ('compile', [sys.executable, '-m', 'compileall', '-q', *[str(APP / name) for name in ('agents', 'core', 'desktop', 'scripts', 'tests', 'main.py')]]),
        ('regressions', [sys.executable, '-m', 'unittest', 'discover', '-s', str(APP / 'tests'), '-v']),
        ('smoke', [sys.executable, str(APP / 'scripts' / 'smoke_code_agent.py')]),
        ('qml', [sys.executable, str(APP / 'scripts' / 'smoke_ui.py')]),
        ('vault', [sys.executable, str(APP / 'scripts' / 'check_vault.py')]),
        ('whitespace', ['git', 'diff', '--check']),
    ]
    for name, command in commands:
        started = time.monotonic()
        with (logs / (name + '.txt')).open('w', encoding='utf-8') as log:
            try:
                process = subprocess.run(command, cwd=REPO, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=300)
                passed, code = process.returncode == 0, process.returncode
            except subprocess.TimeoutExpired:
                passed, code = False, 'timeout'
        row = {'name': name, 'passed': passed, 'exit_code': code, 'seconds': round(time.monotonic() - started, 2)}
        report['checks'].append(row)
        print(json.dumps(row), flush=True)
    deleted = subprocess.check_output(['git', 'diff', 'HEAD', '--name-only', '--diff-filter=D', '-z'], cwd=REPO).decode('utf-8').split('\0')
    deleted = [path for path in deleted if path.startswith('AI-Farm-agents/')]
    report['vault_deletions'] = len(deleted)
    report['curation_errors'] = []
    try:
        from core.vault_curation import review_deletions
        queries = ''.join('HEAD:' + path + '\n' for path in deleted)
        if any('\n' in path for path in deleted):
            raise ValueError('Nome de arquivo invalido para a auditoria.')
        blobs = subprocess.check_output(['git', 'cat-file', '--batch'], input=queries.encode('utf-8'), cwd=REPO)
        stream, hashes = io.BytesIO(blobs), {}
        for path in deleted:
            header = stream.readline().split()
            if len(header) != 3 or header[1] != b'blob':
                raise ValueError('Baseline ausente: ' + path)
            hashes[path] = hashlib.sha256(stream.read(int(header[2]))).hexdigest()
            stream.read(1)
        review = review_deletions(REPO / 'AI-Farm-agents', hashes)
        report['reviewed_vault_deletions'] = len(review['reviewed'])
        report['pending_vault_deletions'] = len(review['pending'])
    except (OSError, ValueError) as error:
        report['curation_errors'].append(str(error))
        report['reviewed_vault_deletions'] = 0
        report['pending_vault_deletions'] = len(deleted)
    candidates = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=REPO).decode('utf-8').split('\0')
    secret_files = []
    token = re.compile(r'sk-ant-[A-Za-z0-9_\-]{24,}')
    for relative in candidates:
        path = REPO / relative
        if not relative or not path.is_file() or path.suffix.lower() not in ('.py', '.md', '.json', '.yaml', '.yml', '.txt', '.example', '.env'):
            continue
        if path.stat().st_size > 2 * 1024 * 1024:
            continue
        text = path.read_text(encoding='utf-8', errors='replace')
        matches = token.findall(text)
        if any(not any(word in match.lower() for word in ('fake', 'test', 'example', 'placeholder', 'cole_sua', 'synthetic')) for match in matches):
            secret_files.append(relative)
    report['suspected_secret_files'] = secret_files  # never print matched values
    report['source_unchanged'] = report['source_digest'] == source_digest()
    report['code_ready'] = all(row['passed'] for row in report['checks']) and not secret_files and report['source_unchanged']
    report['main_ready'] = report['code_ready'] and report['pending_vault_deletions'] == 0 and not report['curation_errors']
    report['production_ready'] = False
    report['production_pending'] = [
        'representative native-app end-to-end coverage',
        'human audio and interruption evaluation',
        'consequential GUI effect authorization',
        'historical credential revocation confirmation',
        'release scope and data review',
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('CODE_READY', report['code_ready'], 'MAIN_READY', report['main_ready'], 'PENDING_VAULT_DELETIONS', report['pending_vault_deletions'])
    return 0 if (report['code_ready'] if args.code_only else report['main_ready']) else 1


if __name__ == '__main__': raise SystemExit(main())
