"""Build artifacts from bounded manifests. Model text is never executed.

Project files are written to a new directory. Spreadsheet manifests expose only
cells, local formulas, formatting and charts, never macros, links or Python.
"""
import ast
import hashlib
import json
import math
import os
import re
import tempfile
from pathlib import Path, PurePosixPath

MAX_FILES = 40
MAX_CONTENT = 1024 * 1024
MAX_ROWS = 5000
MAX_COLS = 100
TEXT_EXT = {'.py', '.html', '.htm', '.css', '.js', '.mjs', '.ts', '.tsx', '.jsx', '.json', '.md',
            '.txt', '.toml', '.yaml', '.yml', '.sql', '.svg', '.xml', '.ini', '.cfg', '.gitignore'}
FORMULAS = {'SUM', 'AVERAGE', 'MIN', 'MAX', 'COUNT', 'COUNTA', 'COUNTIF', 'SUMIF', 'IF', 'ROUND', 'ABS'}


def _name(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}', value):
        raise ValueError('Nome deve conter apenas letras, numeros, _ e - (ate 64 caracteres).')
    return value


def validate_project(manifest):
    if not isinstance(manifest, dict):
        raise ValueError('Manifesto deve ser um objeto.')
    _name(manifest.get('name'))
    files = manifest.get('files')
    if not isinstance(files, list) or not 1 <= len(files) <= MAX_FILES:
        raise ValueError('Projeto deve conter de 1 a 40 arquivos.')
    seen, total = set(), 0
    for entry in files:
        if not isinstance(entry, dict):
            raise ValueError('Arquivo invalido.')
        path, content = entry.get('path'), entry.get('content')
        if not isinstance(path, str) or not isinstance(content, str):
            raise ValueError('path/content devem ser texto.')
        rel = PurePosixPath(path)
        if ('\\' in path or ':' in path or rel.is_absolute() or '..' in rel.parts
                or not rel.parts or rel.as_posix() != path
                or any((p.startswith('.') and p not in ('.gitignore', '.env.example', '.github')) or p.endswith((' ', '.')) for p in rel.parts)
                or any(re.match(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)', p, re.I) for p in rel.parts)):
            raise ValueError(f'Caminho invalido: {path}')
        if rel.suffix.lower() not in TEXT_EXT and rel.name not in ('.gitignore', '.env.example'):
            raise ValueError(f'Tipo de arquivo nao suportado: {path}')
        key = path.casefold()
        if key in seen or any(key.startswith(old + '/') or old.startswith(key + '/') for old in seen):
            raise ValueError('Caminhos duplicados ou conflitantes.')
        seen.add(key)
        total += len(content.encode('utf-8'))
        if total > MAX_CONTENT:
            raise ValueError('Projeto excede 1 MiB.')
        if rel.suffix.lower() == '.py':
            ast.parse(content, filename=path)
        if rel.suffix.lower() == '.json':
            json.loads(content)
    return manifest


def _cell(value):
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, (float, int)):
        if not math.isfinite(value):
            raise ValueError('Numero invalido.')
        return
    if not isinstance(value, str) or len(value) > 10000:
        raise ValueError('Celula invalida ou longa demais.')
    if value.startswith('='):
        # Deliberately small formula grammar: no external reference, DDE or dynamic functions.
        if not re.fullmatch(r'[=A-Za-z0-9$():,+*/.<>!" _\-]+', value):
            raise ValueError('Formula contem recurso nao permitido.')
        functions = {m.upper() for m in re.findall(r'([A-Za-z_][A-Za-z_0-9]*)\s*\(', value)}
        if functions - FORMULAS:
            raise ValueError('Funcao de formula nao permitida.')
        if '!' in value or len(value) > 1000:
            raise ValueError('Formula deve usar apenas referencias da propria aba.')
    elif value.startswith(('+', '-', '@')):
        raise ValueError('Texto que pode ser interpretado como formula deve ser reformulado.')


def validate_workbook(manifest):
    if not isinstance(manifest, dict):
        raise ValueError('Manifesto deve ser objeto.')
    _name(manifest.get('name'))
    sheets = manifest.get('sheets')
    if not isinstance(sheets, list) or not 1 <= len(sheets) <= 6:
        raise ValueError('Planilha deve conter de 1 a 6 abas.')
    seen = set()
    for sheet in sheets:
        if not isinstance(sheet, dict):
            raise ValueError('Aba invalida.')
        title, rows = sheet.get('title'), sheet.get('rows')
        if (not isinstance(title, str) or not 1 <= len(title) <= 31 or re.search(r'[\\/*?:\[\]]', title)
                or title.casefold() in seen):
            raise ValueError('Titulo de aba invalido ou duplicado.')
        seen.add(title.casefold())
        if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_ROWS:
            raise ValueError('Quantidade de linhas invalida.')
        for row in rows:
            if not isinstance(row, list) or not 1 <= len(row) <= MAX_COLS:
                raise ValueError('Linha invalida.')
            for value in row:
                _cell(value)
        charts = sheet.get('charts', [])
        if not isinstance(charts, list) or len(charts) > 4:
            raise ValueError('Graficos invalidos.')
        for chart in charts:
            if not isinstance(chart, dict) or chart.get('type') not in ('bar', 'line'):
                raise ValueError('Tipo de grafico invalido.')
            col = chart.get('column')
            if type(col) is not int or not 2 <= col <= min(len(row) for row in rows):
                raise ValueError('Coluna de grafico invalida.')
    if len(json.dumps(manifest, ensure_ascii=False).encode('utf-8')) > MAX_CONTENT:
        raise ValueError('Manifesto excede 1 MiB.')
    return manifest


def _default_root():
    from core.paths import known_folder
    return Path(known_folder('Documents')) / 'AI Farm Agent'


def build_project(manifest, root=None):
    validate_project(manifest)
    root = Path(root) if root is not None else _default_root()
    root.mkdir(parents=True, exist_ok=True)
    # Unique directory prevents collisions and avoids writing to an existing user project.
    folder = Path(tempfile.mkdtemp(prefix=manifest['name'] + '-', dir=root))
    hashes = {}
    for entry in manifest['files']:
        target = folder / entry['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        data = entry['content'].encode('utf-8')
        with target.open('xb') as stream:
            stream.write(data)
        hashes[entry['path']] = hashlib.sha256(data).hexdigest()
    verified = all(hashlib.sha256((folder / path).read_bytes()).hexdigest() == digest for path, digest in hashes.items())
    return {'success': verified, 'verified': verified, 'status': 'succeeded' if verified else 'failed',
            'result': 'Arquivos criados e conteudo conferido; o programa nao foi executado.\nPasta: ' + str(folder),
            'artifacts': {'folder': str(folder), 'files': [str(folder / path) for path in hashes]},
            'evidence': {'verifier': 'filesystem', 'checks': hashes, 'scope': 'artifact_content'}}


def build_workbook(manifest, root=None):
    validate_workbook(manifest)
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Font, PatternFill
    from openpyxl.chart import BarChart, LineChart, Reference
    from openpyxl.utils import get_column_letter
    root = Path(root) if root is not None else _default_root()
    root.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix=manifest['name'] + '-', dir=root))
    path = folder / (manifest['name'] + '.xlsx')
    wb = Workbook()
    wb.remove(wb.active)
    try:
        for sheet in manifest['sheets']:
            ws = wb.create_sheet(sheet['title'])
            for row in sheet['rows']:
                ws.append(row)
            for cell in ws[1]:
                cell.font = Font(bold=True, color='FFFFFF')
                cell.fill = PatternFill('solid', fgColor='263238')
            ws.freeze_panes = 'A2'
            ws.auto_filter.ref = ws.dimensions
            for c in range(1, ws.max_column + 1):
                ws.column_dimensions[get_column_letter(c)].width = min(60, max(12, max(len(str(ws.cell(r, c).value or '')) for r in range(1, ws.max_row + 1)) + 2))
            for i, spec in enumerate(sheet.get('charts', [])):
                chart = BarChart() if spec['type'] == 'bar' else LineChart()
                chart.add_data(Reference(ws, min_col=spec['column'], max_col=spec['column'], min_row=1, max_row=ws.max_row), titles_from_data=True)
                chart.set_categories(Reference(ws, min_col=1, min_row=2, max_row=ws.max_row))
                ws.add_chart(chart, f'{get_column_letter(ws.max_column + 2)}{i * 16 + 2}')
        wb.save(path)
    finally:
        wb.close()
    checked = load_workbook(path, data_only=False)
    try:
        verified = checked.sheetnames == [s['title'] for s in manifest['sheets']]
        for sheet in manifest['sheets']:
            ws = checked[sheet['title']]
            verified = verified and len(ws._charts) == len(sheet.get('charts', []))
            for r, row in enumerate(sheet['rows'], 1):
                for c, value in enumerate(row, 1):
                    verified = verified and ws.cell(r, c).value == (None if value == '' else value)
    finally:
        checked.close()
    return {'success': verified, 'verified': verified, 'status': 'succeeded' if verified else 'failed',
            'result': 'Planilha criada; celulas, formulas e graficos conferidos. Formulas serao calculadas no Excel.\n' + str(path),
            'artifacts': {'folder': str(folder), 'files': [str(path)]},
            'evidence': {'verifier': 'filesystem', 'scope': 'workbook_structure_and_cells', 'path': str(path)}}
