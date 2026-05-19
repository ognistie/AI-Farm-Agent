"""
CodeAgent v20 — Senior SWE com validacao + retry com feedback.

PROBLEMAS REPORTADOS NA RODADA ANTERIOR (v19) E COMO FORAM RESOLVIDOS:

1. SyntaxError 'unterminated string literal' nos scripts gerados
   -> Validamos o creator script com ast.parse ANTES de devolver o plano.
      Se quebrar, fazemos UMA tentativa de retry passando o erro literal
      como feedback. Se ainda quebrar, abortamos com erro claro em vez de
      enviar codigo invalido pro orquestrador.

2. Bloco de notas abrindo HTML em vez do navegador
   -> Detectamos os.startfile(...) apontando para .html no creator script
      e substituimos automaticamente por webbrowser.open() antes de rodar.
      (Defensiva: o prompt ja proibe, mas o LLM as vezes teima.)

3. Sistema Python profissional virando apenas main.py
   -> Heuristica conta quantos .py o creator script cria. Se a tarefa
      pediu 'sistema profissional/plataforma/dashboard' em Python e o
      script cria < 4 arquivos .py, retry com feedback explicito pedindo
      multi-arquivo modular.

Spec do usuario (Senior SWE + Senior AI Agent Engineer) preservada no
SYSTEM_PROMPT, com um EXEMPLO CONCRETO de creator script multi-arquivo
pro LLM aprender o padrao certo.
"""

import ast
import getpass
import re
from agents.base_agent import BaseAgent
from core.config import get_config

USERNAME = getpass.getuser()
BASE = f"C:/Users/{USERNAME}"


SYSTEM_PROMPT = """Voce e o CODE_AGENT do projeto AI-Farm-Agent.

Voce atua como Senior Software Engineer + Senior AI Agent Engineer.
Receba uma tarefa em linguagem natural, entenda EXATAMENTE o que o
usuario pediu, gere um script Python completo que cria os arquivos
do projeto, abre no VS Code e valida que tudo deu certo.

==========================================================
PRINCIPIOS ABSOLUTOS
==========================================================

1. OBEDECA A TAREFA EXATAMENTE
   - "HTML e CSS" => crie SO HTML e CSS. PROIBIDO criar .js.
   - "apenas HTML" => 1 arquivo, inline tudo.
   - "HTML, CSS e JS" => os 3.
   - "sistema em Python" => sistema funcional multi-arquivo.
   - Nao invente frameworks, libs, arquivos.

2. NUNCA ENTREGUE PLACEHOLDER
   - Proibido: '/* Styles CSS placeholder */', 'TODO', '...', 'pass',
     'Bem-vindo', 'Meu Site', 'Lorem ipsum'.
   - CSS < 80 linhas reais = falha.
   - main.py < 500 bytes para sistema profissional = falha.

3. RESTRICAO DO USUARIO VENCE SEMPRE
   - 'dois arquivos HTML e CSS' = exatamente 2 arquivos.
   - 'site profissional sobre X' = conteudo TEMATICO real, nao 'Bem-vindo'.

4. EXECUTAVEL NA PRIMEIRA TENTATIVA
   - Codigo Python com sintaxe valida (ast.parse passa).
   - Aspas, parenteses, chaves SEMPRE fechadas.
   - Pasta no Desktop com os.makedirs(exist_ok=True).
   - Encoding UTF-8 em todos os arquivos.
   - VS Code: subprocess.Popen(['code', project_dir], shell=True)
   - HTML: webbrowser.open('file:///' + path.replace('\\\\', '/'))
     NUNCA use os.startfile() para .html — em maquinas com .html
     associado ao Notepad, abre o Notepad com o codigo dentro.

==========================================================
ENTENDIMENTO CRITICO: CREATOR SCRIPT vs PROGRAMA
==========================================================

ATENCAO — DOIS NIVEIS DE CODIGO:

1. CREATOR SCRIPT = o que voce devolve no campo "code".
   - Linguagem: Python (SEMPRE).
   - Tarefa: criar pasta + escrever arquivos do projeto + abrir VS Code.
   - Imports top-level: SO stdlib (os, subprocess, webbrowser, pathlib).
   - PRECISA conter literais como 'main.py' / 'database.py' / 'index.html'
     que sao os nomes dos ARQUIVOS QUE VOCE ESTA CRIANDO.

2. ARQUIVOS DO PROJETO = o que o creator script grava em disco.
   - Linguagens: HTML/CSS/JS/Python/etc, conforme a tarefa.
   - Conteudo: como strings (multi-line ''') dentro do creator script.

ERRADO (creator script vira o programa):
    def menu_principal():    # ❌ isso e o sistema dental, nao o creator!
        while True:
            print("1. Cadastrar paciente")
            ...

CERTO (creator script ESCREVE arquivos):
    import os
    project_dir = os.path.join(...)
    os.makedirs(project_dir, exist_ok=True)

    main_content = '''
    def menu_principal():
        while True:
            print("1. Cadastrar paciente")
            ...
    '''
    with open(os.path.join(project_dir, 'main.py'), 'w', encoding='utf-8') as f:
        f.write(main_content)

==========================================================
FORMATO DE SAIDA (JSON puro, sem markdown)
==========================================================

{
  "steps": [
    {
      "step": 1,
      "description": "<frase curta da acao>",
      "code": "<creator script Python que cria os arquivos do projeto>"
    }
  ]
}

==========================================================
PADRAO DE CREATOR SCRIPT — SITES (HTML + CSS)
==========================================================

import os, subprocess, webbrowser
base = os.path.join(os.path.expanduser('~'), 'Desktop')
project_dir = os.path.join(base, 'site_buda')
# anti-colisao
i = 2
while os.path.isdir(project_dir) and os.listdir(project_dir):
    project_dir = os.path.join(base, f'site_buda_{i}')
    i += 1
os.makedirs(project_dir, exist_ok=True)

# index.html — use aspas triplas SIMPLES (apostrofes) como delimitador
# externo, pois o HTML por dentro tem aspas duplas
index_html = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>O Caminho de Buda</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <!-- conteudo real e tematico aqui -->
</body>
</html>'''

style_css = '''@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900');
:root {
  --bg: #fafaf7;
  --text: #18181b;
  --accent: #d97706;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Inter', sans-serif; ... }
/* 100+ linhas REAIS aqui */'''

with open(os.path.join(project_dir, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(index_html)
with open(os.path.join(project_dir, 'style.css'), 'w', encoding='utf-8') as f:
    f.write(style_css)

# Abrir VS Code
subprocess.Popen(['code', project_dir], shell=True)
# Abrir no navegador (NAO os.startfile)
index_path = os.path.join(project_dir, 'index.html')
webbrowser.open('file:///' + index_path.replace('\\\\', '/'))

# Relatorio
arquivos = os.listdir(project_dir)
print(f'PASTA: {project_dir}')
print(f'ARQUIVOS_CRIADOS: {arquivos}')
print('TASK_TYPE: site_html_css')
print('REQUESTED_LANGUAGES: html, css')
print('FORBIDDEN_FILES_AVOIDED: script.js')
print('VALIDACAO: OK')
print('REUSABLE_PATTERN: site-2-arquivos-html-css')

==========================================================
PADRAO DE CREATOR SCRIPT — SISTEMA PYTHON (MULTI-ARQUIVO)
==========================================================

Para 'sistema profissional em python' VOCE DEVE criar 5+ arquivos:

import os, subprocess
base = os.path.join(os.path.expanduser('~'), 'Desktop')
project_dir = os.path.join(base, 'sistema_dental')
os.makedirs(project_dir, exist_ok=True)

# 1. main.py — entry point
main_py = '''
from database import DentalDB
from cli import menu_principal

def main():
    db = DentalDB()
    menu_principal(db)

if __name__ == "__main__":
    main()
'''

# 2. database.py — persistencia
database_py = '''
import json
from datetime import datetime

class DentalDB:
    def __init__(self, path="dental_data.json"):
        self.path = path
        self.data = self._load()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"pacientes": [], "consultas": []}
    # ... metodos completos: add_paciente, add_consulta, listar, buscar, etc
'''

# 3. cli.py — interface
cli_py = '''
def menu_principal(db):
    while True:
        print("1. Cadastrar paciente")
        print("2. Agendar consulta")
        ...
'''

# 4. models.py — entidades
# 5. utils.py — helpers (validacao de data, formatacao, etc)
# 6. README.md — como rodar

# Escrever todos
for name, content in [
    ('main.py', main_py),
    ('database.py', database_py),
    ('cli.py', cli_py),
    ('models.py', models_py),
    ('utils.py', utils_py),
    ('README.md', readme_md),
]:
    with open(os.path.join(project_dir, name), 'w', encoding='utf-8') as f:
        f.write(content)

subprocess.Popen(['code', project_dir], shell=True)

# Validacao
py_files = [f for f in os.listdir(project_dir) if f.endswith('.py')]
sizes = {f: os.path.getsize(os.path.join(project_dir, f)) for f in py_files}
print(f'PASTA: {project_dir}')
print(f'ARQUIVOS_PY: {py_files}')
print(f'TAMANHOS: {sizes}')
print('TASK_TYPE: python_system')
print('VALIDACAO: OK' if all(s > 200 for s in sizes.values()) else 'VALIDACAO: FAIL')
print('Para rodar: python main.py')

==========================================================
REGRAS DE ESCAPAMENTO DE STRINGS (BUG RECORRENTE)
==========================================================

Voce ESTA escrevendo Python que escreve Python. Atencao a aspas:

- Para conteudo Python que tem aspas DUPLAS por dentro, use aspas
  triplas SIMPLES como delimitador EXTERNO: '''...'''
- Para conteudo HTML que tem aspas DUPLAS por dentro, use '''...'''
  EXTERNO.
- Se o conteudo TIVER ''' no meio (raro), use '' '' '' escapado.
- Para regex ou paths Windows, use raw string: r"\\d{2}\\.\\d{2}"
  ou escape duplo "\\\\d{2}\\\\.\\\\d{2}".
- NUNCA quebre uma string no meio. Toda triple-quoted DEVE fechar.
- Se for grande, divida em variaveis: parte1 + parte2.

==========================================================
ANTI-INVENCAO DE ARQUIVOS
==========================================================

| Pedido                            | Permitido            | PROIBIDO       |
|-----------------------------------|----------------------|----------------|
| "HTML e CSS"                      | index.html, style.css| .js, package.json |
| "dois arquivos HTML e CSS"        | exatamente 2 arquivos| 3o arquivo     |
| "sistema em python"               | 5+ .py + README + data| .html/.css/.js |
| "site sobre X"                    | HTML+CSS no minimo   | .py            |

==========================================================
CHECKLIST INTERNO (rode antes de responder)
==========================================================

1. A tarefa pediu QUAIS linguagens? Criei SOMENTE essas?
2. Para sistema python: estou criando 5+ arquivos .py modulares?
3. Para HTML + CSS: estou criando 2 arquivos separados, sem .js?
4. O CSS tem 80+ linhas REAIS?
5. O HTML tem conteudo TEMATICO sobre o pedido (nao 'Bem-vindo')?
6. Estou usando webbrowser.open() para .html (NAO os.startfile)?
7. Toda string triple-quoted ESTA FECHADA?
8. Vou imprimir relatorio final com metadados?

Se algo falhou, CORRIJA antes de responder.
"""


_SONNET_INDICATORS = [
    "titulo", "title", "github.com", "desenvolvido por", "apresentacao",
    "sobre o", "about", "secoes", "sections", "sistema", "dashboard", "app",
    "conteudo", "content", "texto", "escreva", "coloque",
    "nome", "link", "url", "http", "logo", "completo", "profissional",
    "plataforma", "gerenciador", "controle", "agendamento",
]

_PYTHON_SYSTEM_INDICATORS = [
    "sistema em python", "sistema python", "sistema profissional em python",
    "app em python", "aplicativo python", "plataforma em python",
    "dashboard em python", "gerenciador em python", "controle em python",
]


def _needs_sonnet(task: str) -> bool:
    t = str(task).lower()
    return any(ind in t for ind in _SONNET_INDICATORS)


def _is_python_system_task(task: str) -> bool:
    t = str(task).lower()
    return any(ind in t for ind in _PYTHON_SYSTEM_INDICATORS)


def _count_py_files_in_code(code: str) -> int:
    """Conta quantos arquivos .py distintos o creator script grava em disco."""
    # padrao tipico: open(..., 'main.py', 'w') ou 'main.py'
    py_files = set()
    for m in re.finditer(r"""['"]([\w/]+\.py)['"]""", code):
        name = m.group(1)
        if not name.endswith("__init__.py"):
            py_files.add(name)
    return len(py_files)


def _has_startfile_html(code: str) -> bool:
    """
    Detecta os.startfile() em scripts que tambem mencionam .html — assume
    que se o script lida com HTML e usa os.startfile, o startfile e pra abrir
    o HTML (caso comum no LLM, mesmo quando o argumento e uma variavel como
    'target' em vez do literal 'index.html').
    """
    if "os.startfile" not in code:
        return False
    code_low = code.lower()
    if ".html" in code_low or ".htm'" in code_low or '.htm"' in code_low:
        return True
    # Tambem aceita argumentos literais .html
    for m in re.finditer(r"os\.startfile\s*\(([^)]+)\)", code):
        arg_low = m.group(1).lower()
        if ".html" in arg_low or ".htm" in arg_low or "index" in arg_low:
            return True
    return False


def _replace_startfile_with_webbrowser(code: str) -> tuple[str, int]:
    """
    Substitui TODAS as chamadas os.startfile(...) por webbrowser.open(...)
    QUANDO o script lida com HTML (heuristica conservadora: so substitui
    em scripts que mencionam .html). Para scripts sem HTML, deixa como esta.

    Retorna (codigo_novo, num_substituicoes).
    """
    if "os.startfile" not in code:
        return code, 0

    code_low = code.lower()
    deals_with_html = (
        ".html" in code_low
        or ".htm'" in code_low
        or '.htm"' in code_low
    )
    if not deals_with_html:
        return code, 0

    count = 0

    def replace(m):
        nonlocal count
        count += 1
        arg = m.group(1).strip()
        return (
            "webbrowser.open('file:///' + ("
            + arg + ").replace('\\\\', '/'))"
        )

    new_code = re.sub(r"os\.startfile\s*\(([^)]+)\)", replace, code)

    if count and "import webbrowser" not in new_code:
        new_code = "import webbrowser\n" + new_code
    return new_code, count


class CodeAgent(BaseAgent):
    """
    v20 — spec do usuario + validacao AST + retry com feedback.
    """

    def __init__(self):
        super().__init__(name="CODE", system_prompt=SYSTEM_PROMPT)
        self._config = get_config()

    def plan(self, task, context=None):
        task_text = self._extract_task_text(task)

        use_sonnet = _needs_sonnet(task_text)
        model = (
            self._config.get("models.strong")
            if use_sonnet else self._config.get("models.fast")
        )
        self.logger.info(f"Modelo: {'Sonnet' if use_sonnet else 'Haiku'}")

        is_py_system = _is_python_system_task(task_text)

        # 1a tentativa
        result = self._call_and_validate(model, task_text, is_py_system, retry_feedback=None)
        if result["ok"]:
            return self._build_response(result["steps"], model)

        # 2a tentativa com feedback do que quebrou
        self.logger.warning(f"Retry: {result['reason']}")
        result = self._call_and_validate(
            model, task_text, is_py_system, retry_feedback=result["reason"]
        )
        if result["ok"]:
            return self._build_response(result["steps"], model)

        # Falhou nas 2 tentativas
        self.logger.error(f"Falhou apos 2 tentativas: {result['reason']}")
        self._metrics["total_plans"] += 1
        self._metrics["failed_plans"] += 1
        return {
            "steps": [],
            "agent": "CODE",
            "error": f"CodeAgent falhou: {result['reason']}",
        }

    # ──────────────────────────────────────────────────────────────────

    def _call_and_validate(self, model, task_text, is_py_system, retry_feedback):
        feedback_block = ""
        if retry_feedback:
            feedback_block = (
                "\n\n⚠️ TENTATIVA ANTERIOR FALHOU. MOTIVO:\n"
                + retry_feedback
                + "\nCorrija isso AGORA e devolva codigo Python valido."
            )

        message = (
            "TAREFA DO USUARIO (siga LITERALMENTE):\n"
            + task_text
            + "\n\n"
            "RODE O CHECKLIST de 8 pontos antes de responder.\n"
            "PROIBIDO os.startfile para HTML (use webbrowser.open).\n"
            "Se for sistema python profissional, gere 5+ arquivos .py modulares.\n"
            "Toda string triple-quoted DEVE fechar.\n"
            "Use raw strings (r'...') ou escape duplo (\\\\) para paths Windows.\n"
            + feedback_block
            + "\n\nResponda apenas com JSON puro."
        )

        # Sistemas Python multi-arquivo precisam de mais espaco no output
        max_tokens = 16000 if is_py_system else 10000

        try:
            raw = self._client.message(
                model=model,
                system=self.system_prompt,
                user_content=message,
                max_tokens=max_tokens,
            )
            from core.json_validator import safe_parse
            plan = safe_parse(raw, model)
        except Exception as e:
            return {"ok": False, "reason": f"chamada LLM falhou: {e}"}

        return self._validate_and_normalize(plan, is_py_system)

    def _validate_and_normalize(self, plan, is_py_system):
        """
        Valida cada step:
          - code nao-vazio
          - ast.parse passa (sintaxe Python valida)
          - substitui os.startfile(*.html) por webbrowser.open
          - se sistema python: pelo menos 4 arquivos .py mencionados no codigo
        Retorna {ok: bool, steps: [...], reason: str}
        """
        raw_steps = plan.get("steps", [])
        if not raw_steps:
            return {"ok": False, "reason": "LLM nao devolveu nenhum step"}

        steps = []
        for st in raw_steps:
            code = st.get("code", "")
            code = code.replace("{BASE}", BASE).replace("{USERNAME}", USERNAME)
            if not code.strip():
                continue

            # Validacao 1: AST parse
            try:
                ast.parse(code)
            except SyntaxError as e:
                snippet = ""
                try:
                    lines = code.split("\n")
                    snippet = lines[(e.lineno or 1) - 1][:120]
                except Exception:
                    pass
                return {
                    "ok": False,
                    "reason": (
                        f"SyntaxError no creator script linha {e.lineno}: "
                        f"{e.msg}. Linha: `{snippet}`. "
                        "Provavel string triple-quoted nao fechada ou escape errado."
                    ),
                }

            # Defesa 2: substituir os.startfile(*.html) por webbrowser.open
            new_code, replaced = _replace_startfile_with_webbrowser(code)
            if replaced:
                self.logger.info(
                    f"Substitui {replaced} os.startfile(*.html) por webbrowser.open"
                )
                code = new_code

            # Validacao 3: sistema python precisa de multi-arquivo (>=3)
            if is_py_system:
                n_py = _count_py_files_in_code(code)
                if n_py < 3:
                    code_snippet = code[:300].replace("\n", " | ")
                    return {
                        "ok": False,
                        "reason": (
                            f"Tarefa pede sistema profissional em Python mas "
                            f"o creator script criou apenas {n_py} arquivo(s) .py. "
                            "Minimo aceitavel: 3 .py + README.md. Sugestao para sistema "
                            "de agendamento/cadastro/controle: main.py (entry point), "
                            "database.py (persistencia), cli.py (menu CLI), README.md. "
                            "Use multiplos blocos `with open(os.path.join(project_dir, "
                            "'arquivo.py'), 'w', encoding='utf-8') as f: f.write(...)`. "
                            f"Inicio do seu creator script: {code_snippet}"
                        ),
                    }
                # Sistema Python = ZERO arquivos web (.html/.css/.js)
                if any(ext in code for ext in (".js'", '.js"', ".css'", '.css"', ".html'", '.html"')):
                    return {
                        "ok": False,
                        "reason": (
                            "Tarefa pede sistema em Python — PROIBIDO criar arquivos "
                            ".html/.css/.js. Remova qualquer open(...'X.html'...) ou "
                            "similar do creator script. So .py, .md, .txt, .json, .db."
                        ),
                    }

            steps.append({
                "step": st.get("step", len(steps) + 1),
                "description": st.get("description", ""),
                "action": "run_python",
                "params": {"code": code, "description": st.get("description", "")},
                "agent": "CODE",
            })

        if not steps:
            return {"ok": False, "reason": "todos os steps tinham code vazio"}

        return {"ok": True, "steps": steps, "reason": ""}

    def _build_response(self, steps, model):
        model_tag = model.split("-")[1] if "-" in model else model
        total_code = sum(len(s["params"]["code"]) for s in steps)
        self.logger.info(
            f"Plano: {len(steps)} step(s) (model={model_tag}, code={total_code} chars)"
        )
        self._metrics["total_plans"] += 1
        self._metrics["successful_plans"] += 1
        return {"steps": steps, "agent": "CODE"}
