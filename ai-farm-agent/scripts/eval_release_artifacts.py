"""Live artifact acceptance, no generated code execution or desktop actions.

Explicit --allow-live is required because calls incur provider cost. Fixed fixtures,
three trials by default. These results do not measure general assistant capability.
"""
import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CASES = {
    'regression': {
        'CODE': {'name': 'qa_fixture', 'title': 'QA Fixture', 'heading': 'Teste de Producao'},
        'DATA': {'name': 'qa_sales', 'title': 'Dados', 'a': 10, 'b': 20}},
    'holdout': {
        'CODE': {'name': 'release_fixture', 'title': 'Release Check', 'heading': 'Validacao de Entrega'},
        'DATA': {'name': 'qa_inventory', 'title': 'Estoque', 'a': 2, 'b': 3}},
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-live', action='store_true')
    parser.add_argument('--split', choices=CASES, default='regression')
    parser.add_argument('--trials', type=int, default=3)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not args.allow_live or not 1 <= args.trials <= 5:
        parser.error('Use --allow-live e de 1 a 5 tentativas.')
    from dotenv import load_dotenv
    load_dotenv(ROOT.parent / '.env'); load_dotenv(ROOT / '.env')
    from agents.code_agent import CodeAgent
    from agents.data_agent import DataAgent
    from core.artifact_builder import build_project, build_workbook
    from core.ai_client import get_client
    from openpyxl import load_workbook
    report = {'harness': 'release-artifacts-1', 'split': args.split,
              'sdk_version': version('anthropic'), 'python': sys.version.split()[0], 'trials': []}
    for kind, agent in (('CODE', CodeAgent()), ('DATA', DataAgent())):
        case = CASES[args.split][kind]
        if kind == 'CODE':
            task = (f"Crie um site estatico de teste sem dependencias ou recursos externos. Nome {case['name']}. "
                    f"Um index.html completo com titulo exatamente {case['title']} e h1 com texto {case['heading']}; inclua README.md. Nao execute nada.")
        else:
            task = (f"Crie uma planilha de teste chamada {case['name']}. Uma aba {case['title']} com linhas exatamente "
                    f"[Item,Valor], [A,{case['a']}], [B,{case['b']}], [Total,=SUM(B2:B3)]. "
                    'Adicione um grafico de barras da coluna 2. Nao adicione dados de exemplo.')
        for trial in range(args.trials):
            start = time.monotonic()
            row = {'agent': kind, 'trial': trial + 1, 'passed': False, 'model': agent.model, 'effort': agent.effort}
            try:
                plan = agent.plan(task)
                row['effort'] = plan.get('effort_used', agent.effort)
                row['attempt_errors'] = plan.get('attempt_errors', [])
                if not plan.get('steps'):
                    row['error'] = plan.get('error', 'sem passos')
                else:
                    with tempfile.TemporaryDirectory(prefix='ai-farm-eval-') as tmp:
                        manifest = plan['steps'][0]['params']['manifest']
                        if kind == 'CODE':
                            result = build_project(manifest, tmp)
                            html = '\n'.join(e['content'] for e in manifest['files'] if e['path'].endswith('.html'))
                            row['passed'] = result['verified'] and case['title'] in html and case['heading'] in html
                        else:
                            result = build_workbook(manifest, tmp)
                            wb = load_workbook(result['artifacts']['files'][0])
                            try:
                                ws = wb[case['title']] if case['title'] in wb.sheetnames else None
                                row['passed'] = bool(result['verified'] and ws is not None and list(ws.values) == [
                                    ('Item', 'Valor'), ('A', case['a']), ('B', case['b']), ('Total', '=SUM(B2:B3)')]
                                    and len(ws._charts) == 1)
                            finally:
                                wb.close()
            except Exception as error:
                row['error'] = type(error).__name__
            row['seconds'] = round(time.monotonic() - start, 2)
            report['trials'].append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
    report['metrics'] = get_client().metrics
    report['passed'] = all(row['passed'] for row in report['trials'])
    output = args.output or ROOT / 'memory' / ('release-live-' + args.split + '.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
