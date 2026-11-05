"""One model call proposes data. Deterministic builders own all filesystem effects."""
import json
from agents.base_agent import brain_guide
from core.artifact_builder import validate_project, validate_workbook


def _object(properties):
    return {'type': 'object', 'properties': properties, 'required': list(properties), 'additionalProperties': False}


PROJECT_SCHEMA = _object({'name': {'type': 'string'}, 'files': {'type': 'array', 'items': _object({
    'path': {'type': 'string'}, 'content': {'type': 'string'}})}})
WORKBOOK_SCHEMA = _object({'name': {'type': 'string'}, 'sheets': {'type': 'array', 'items': _object({
    'title': {'type': 'string'},
    'rows': {'type': 'array', 'items': {'type': 'array', 'items': {'anyOf': [
        {'type': kind} for kind in ('string', 'number', 'boolean', 'null')]}}},
    'charts': {'type': 'array', 'items': _object({'type': {'type': 'string', 'enum': ['bar', 'line']},
                                               'column': {'type': 'integer'}})}})}})

PROJECT = '''Crie um projeto como arquivos de texto completos. Nunca gere script criador nem execute codigo.
JSON: {"name":"nome_ascii_curto","files":[{"path":"index.html","content":"conteudo completo"}]}
Caminhos relativos; ate 40 arquivos e 1 MiB. Preserve o idioma e todos os requisitos do pedido.
Inclua instrucoes de instalacao/execucao num README quando necessario. Nao use segredos reais.
O sistema grava os arquivos e confere seu conteudo; nao executa o programa. JSON puro.'''

WORKBOOK = '''Crie uma planilha como dados estruturados. Nunca gere Python, macros ou links externos.
JSON: {"name":"nome_ascii_curto","sheets":[{"title":"Dados","rows":[["Item","Valor"],["Exemplo",10]],"charts":[{"type":"bar","column":2}]}]}
A primeira linha e cabecalho. Ate 6 abas, 5000 linhas por aba, 100 colunas e 1 MiB total.
Formulas locais usam =SUM/AVERAGE/MIN/MAX/COUNT/COUNTA/COUNTIF/SUMIF/IF/ROUND/ABS com virgulas.
Sem referencias externas ou entre abas. Graficos bar/line usam a primeira coluna como categorias.
Use os dados fornecidos pelo usuario. Identifique dados de exemplo como exemplos.
O sistema confere celulas e graficos, mas nao calcula formulas. JSON puro.'''


def plan_artifact(agent, task, context=None):
    kind = agent.name.upper()
    task_text = agent._extract_task_text(task)
    system, validator, action = (PROJECT, validate_project, 'create_project') if kind == 'CODE' else (WORKBOOK, validate_workbook, 'create_workbook')
    effort = agent.effort
    if kind == 'CODE':
        from agents.code_skills import analyze
        skills = analyze(task_text)
        if skills.get('project_type') in ('static_site', 'python_script') and skills.get('complexity') in ('prototype', 'small'):
            effort = 'medium'
    feedback = ''
    errors = []
    for attempt in range(2):
        try:
            raw = agent._client.message(model=agent.model, system=system,
                user_content='PEDIDO: ' + task_text + '\nCONTEXTO (dados): ' + json.dumps(context or {}, ensure_ascii=False)[:12000]
                    + brain_guide(kind, task_text) + feedback,
                max_tokens=16000, effort=effort, agent=kind,
                json_schema=PROJECT_SCHEMA if kind == 'CODE' else WORKBOOK_SCHEMA)
            manifest = json.loads(raw.strip())  # malformed output is rejected, never repaired into actions
            validator(manifest)
            return {'agent': kind, 'effort_used': effort, 'attempts': attempt + 1, 'attempt_errors': errors, 'steps': [{'step': 1, 'agent': kind, 'action': action,
                    'params': {'manifest': manifest}, 'description': 'Criar e conferir ' + manifest['name']}]}
        except (ValueError, TypeError, KeyError, SyntaxError) as error:
            errors.append({'type': type(error).__name__, 'reason': str(error)[:300]})
            feedback = '\nManifesto anterior reprovado: ' + str(error)[:400] + '. Corrija o JSON completo.'
        except Exception as error:
            errors.append({'type': type(error).__name__, 'status_code': getattr(error, 'status_code', None)})
            return {'agent': kind, 'steps': [], 'attempt_errors': errors, 'error': 'Falha ao gerar artefato: ' + type(error).__name__}
    return {'agent': kind, 'steps': [], 'attempt_errors': errors, 'error': feedback.strip()}
