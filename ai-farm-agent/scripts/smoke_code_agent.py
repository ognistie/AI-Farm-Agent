"""
Smoke test do AI Farm Agent — valida sem chamar API:
- Maestro: ambiguity gate (cenarios A e J do briefing)
- workflow_store: quarentena automatica de arquivos corrompidos
- WebAgent: circuit-breaker (cenarios B e L do briefing)
- CodeAgent: heuristica _needs_sonnet (escolha de modelo)

Roda: python scripts/smoke_code_agent.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_maestro_ambiguity_gate():
    """Cenarios A e J do briefing — prompts vagos disparam pedido de clarificacao."""
    print("\n=== Maestro ambiguity gate (cenarios A e J) ===")
    from agents.maestro import _detect_ambiguity

    cases_ambiguous = [
        "deixa rodando",
        "deixa o projeto rodando",
        "atualiza o relatorio do mes passado",
        "manda pra ela",
        "",
    ]
    cases_clear = [
        "crie um arquivo python que renomeia imagens",
        "pesquise no google sobre Palmeiras",
        "abra o vs code na pasta meu-projeto",
        "envie 'oi' para Joao no Teams",
    ]

    passed = 0
    total = len(cases_ambiguous) + len(cases_clear)
    for task in cases_ambiguous:
        result = _detect_ambiguity(task)
        ok = result is not None
        status = "OK  " if ok else "FAIL"
        print(f"{status} | ambiguo: {task!r} | detectou={ok}")
        if ok:
            passed += 1
    for task in cases_clear:
        result = _detect_ambiguity(task)
        ok = result is None
        status = "OK  " if ok else "FAIL"
        print(f"{status} | claro:   {task!r} | passou_clean={ok}")
        if ok:
            passed += 1
    print(f"\n{passed}/{total} passou")
    return passed == total


def test_workflow_quarantine():
    """Arquivos truncados de workflow vao para .corrupted/ no primeiro turno."""
    print("\n=== workflow_store quarantine ===")
    import tempfile
    import json as _json
    from pathlib import Path
    import memory.workflow_store as ws

    with tempfile.TemporaryDirectory() as tmp:
        old_dir = ws.WORKFLOWS_DIR
        old_quarantine = ws.QUARANTINE_DIR
        try:
            ws.WORKFLOWS_DIR = Path(tmp) / "workflows"
            ws.QUARANTINE_DIR = ws.WORKFLOWS_DIR / ".corrupted"
            ws.WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)

            bad = ws.WORKFLOWS_DIR / "code_20260402_133441.json"
            bad.write_text('{"task":"x","tags":', encoding="utf-8")

            good = ws.WORKFLOWS_DIR / "code_20260518_162410.json"
            _json.dump(
                {
                    "task": "abra o vs code e crie um site profissional",
                    "agent": "CODE",
                    "steps": [],
                    "created_at": "2026-05-18T16:24:10",
                    "tags": ["site", "vscode"],
                },
                good.open("w", encoding="utf-8"),
            )

            ws._quarantine_logged_once = False
            ws.find_similar_workflow("abra o vs code")

            in_corrupted = (ws.QUARANTINE_DIR / "code_20260402_133441.json").exists()
            good_stays = good.exists()
            still_bad = bad.exists()

            print(f"{'OK  ' if in_corrupted else 'FAIL'} | arquivo truncado movido para .corrupted/")
            print(f"{'OK  ' if good_stays else 'FAIL'} | arquivo valido nao foi tocado")
            print(f"{'OK  ' if not still_bad else 'FAIL'} | arquivo truncado nao esta mais em workflows/")
            return in_corrupted and good_stays and not still_bad
        finally:
            ws.WORKFLOWS_DIR = old_dir
            ws.QUARANTINE_DIR = old_quarantine


def test_web_circuit_breaker():
    """Cenarios B e L — apos 3 tentativas, escalar."""
    print("\n=== WebAgent circuit-breaker (cenarios B e L) ===")
    from agents.web_agent import WebAgent, CIRCUIT_BREAKER_MAX_ATTEMPTS

    agent = WebAgent.__new__(WebAgent)
    agent._attempts = {}
    agent.logger = type("L", (), {
        "info": lambda *a, **k: None,
        "warning": lambda *a, **k: None,
        "error": lambda *a, **k: None,
    })()

    task = "pesquise no google sobre palmeiras"
    for _ in range(CIRCUIT_BREAKER_MAX_ATTEMPTS):
        agent._bump_attempt(task)
    extra = agent._bump_attempt(task)
    expected = CIRCUIT_BREAKER_MAX_ATTEMPTS + 1
    ok = extra == expected
    print(f"{'OK  ' if ok else 'FAIL'} | apos {expected} bumps consecutivos = circuito aberto")
    return ok


def test_auto_install_detection():
    """
    automation.py v8 deve usar AST: imports DENTRO de strings nao
    disparam pip install. So imports REAIS no topo do script.

    Caso que quebrou: o creator script do CodeAgent tem
    `main_py = '''from database.connection import X'''` e o regex antigo
    pegava 'database' como dep externa, disparando 'pip install database'.
    """
    print("\n=== Auto-installer: AST vs regex (bug Instalando database) ===")
    import ast as _ast

    # Simula creator script do CodeAgent — imports DENTRO de strings, nao no topo
    creator = '''
import os, subprocess, webbrowser
main_py = """
from database.connection import DatabaseManager
from utils.helpers import validate
"""
open("main.py", "w").write(main_py)
'''
    # Replica EXATAMENTE a logica nova do automation.py
    found = []
    tree = _ast.parse(creator)
    for node in tree.body:
        if isinstance(node, _ast.Import):
            for n in node.names:
                found.append(n.name.split(".")[0])
        elif isinstance(node, _ast.ImportFrom):
            if node.module and node.level == 0:
                found.append(node.module.split(".")[0])

    # Esperado: encontra os, subprocess, webbrowser (top-level)
    # NAO encontra: database, utils (estao DENTRO de string)
    expected = {"os", "subprocess", "webbrowser"}
    got = set(found)
    ok_found = expected.issubset(got)
    ok_skipped = "database" not in got and "utils" not in got
    print(f"{'OK  ' if ok_found else 'FAIL'} | top-level capturado: {sorted(got)}")
    print(f"{'OK  ' if ok_skipped else 'FAIL'} | database/utils dentro de string NAO foram capturados")
    return ok_found and ok_skipped


def test_code_agent_validation():
    """v20 — valida que detectamos os 3 bugs reportados pelo usuario."""
    print("\n=== CodeAgent v20 (validacao + replace os.startfile + multi-file) ===")
    from agents.code_agent import (
        _count_py_files_in_code,
        _has_startfile_html,
        _replace_startfile_with_webbrowser,
        _is_python_system_task,
    )

    passed = 0
    total = 0

    # 1. Detectar tarefa de sistema python
    total += 1
    if _is_python_system_task("crie um sistema profissional em python de agendamento"):
        print("OK   | detecta tarefa 'sistema python'")
        passed += 1
    else:
        print("FAIL | nao detectou 'sistema python'")

    total += 1
    if not _is_python_system_task("crie um site sobre buda"):
        print("OK   | NAO detecta tarefa de site como 'sistema python'")
        passed += 1
    else:
        print("FAIL | confundiu site com sistema python")

    # 2. Contar arquivos .py num creator script
    creator_multi = '''
with open(os.path.join(d, 'main.py'), 'w') as f: f.write(x)
with open(os.path.join(d, 'database.py'), 'w') as f: f.write(y)
with open(os.path.join(d, 'cli.py'), 'w') as f: f.write(z)
with open(os.path.join(d, 'models.py'), 'w') as f: f.write(w)
with open(os.path.join(d, 'utils.py'), 'w') as f: f.write(v)
'''
    creator_solo = '''
with open(os.path.join(d, 'main.py'), 'w') as f: f.write(x)
'''
    total += 1
    if _count_py_files_in_code(creator_multi) == 5:
        print("OK   | conta 5 arquivos .py num creator multi-file")
        passed += 1
    else:
        print(f"FAIL | contou {_count_py_files_in_code(creator_multi)} (esperado 5)")

    total += 1
    if _count_py_files_in_code(creator_solo) == 1:
        print("OK   | conta 1 arquivo .py num creator solo")
        passed += 1
    else:
        print(f"FAIL | contou {_count_py_files_in_code(creator_solo)} (esperado 1)")

    # 3. Detectar e substituir os.startfile(*.html)
    code_with_startfile = """
import os
target = os.path.join(d, 'index.html')
os.startfile(target)
"""
    total += 1
    if _has_startfile_html(code_with_startfile):
        print("OK   | detecta os.startfile(*.html) no creator")
        passed += 1
    else:
        print("FAIL | nao detectou os.startfile(*.html)")

    total += 1
    new_code, count = _replace_startfile_with_webbrowser(code_with_startfile)
    if count == 1 and "webbrowser.open" in new_code and "os.startfile" not in new_code:
        print("OK   | substitui os.startfile por webbrowser.open")
        passed += 1
    else:
        print(f"FAIL | substituicao falhou (count={count}, code_has_webbrowser={'webbrowser.open' in new_code})")

    # 4. Nao mexer em os.startfile que NAO aponta para .html
    code_other = """
import os
os.startfile('document.pdf')
"""
    total += 1
    _, c = _replace_startfile_with_webbrowser(code_other)
    if c == 0:
        print("OK   | nao substitui os.startfile para .pdf (so .html)")
        passed += 1
    else:
        print(f"FAIL | substituiu indevidamente os.startfile para .pdf")

    print(f"\n{passed}/{total} passou")
    return passed == total


def test_inline_program_detection():
    """v20+ detecta quando o code field e o programa em si (mainloop/app.run)
    sem file writes — caso comum em Tkinter/Flask onde LLM esquece de criar
    arquivos e responde com o programa direto."""
    print("\n=== Detector de programa inline (Tkinter/Flask) ===")
    from agents.code_agent import _looks_like_inline_program, _is_python_task

    # 1. Tkinter inline (sem file writes) — DEVE ser detectado
    tkinter_inline = """
import tkinter as tk
class App:
    def __init__(self, root):
        self.root = root
root = tk.Tk()
app = App(root)
root.mainloop()
"""
    is_inline, motivo = _looks_like_inline_program(tkinter_inline)
    passed = 0
    total = 0
    total += 1
    if is_inline and "Tkinter" in motivo:
        print(f"OK   | Tkinter inline detectado ({motivo})")
        passed += 1
    else:
        print(f"FAIL | Tkinter inline NAO detectado (is_inline={is_inline})")

    # 2. Creator script LEGITIMO (com file writes) — NAO deve disparar
    creator_legit = """
import os
project_dir = os.path.join('/tmp', 'app')
os.makedirs(project_dir, exist_ok=True)
with open(os.path.join(project_dir, 'main.py'), 'w', encoding='utf-8') as f:
    f.write('''
import tkinter as tk
root = tk.Tk()
root.mainloop()
''')
"""
    is_inline, motivo = _looks_like_inline_program(creator_legit)
    total += 1
    if not is_inline:
        print(f"OK   | Creator script com file writes NAO foi marcado como inline")
        passed += 1
    else:
        print(f"FAIL | Creator legitimo foi marcado como inline ({motivo})")

    # 3. Flask inline — DEVE ser detectado
    flask_inline = """
from flask import Flask
app = Flask(__name__)
@app.route('/')
def home():
    return 'hi'
app.run(debug=True)
"""
    is_inline, motivo = _looks_like_inline_program(flask_inline)
    total += 1
    if is_inline and "Flask" in motivo:
        print(f"OK   | Flask inline detectado ({motivo})")
        passed += 1
    else:
        print(f"FAIL | Flask inline NAO detectado (is_inline={is_inline})")

    # 4. _is_python_task: detecta varias formas
    total += 1
    if _is_python_task("crie um sistema desktop em Python com Tkinter"):
        print("OK   | detecta 'python+tkinter' como py task")
        passed += 1
    else:
        print("FAIL | nao detectou python task")

    total += 1
    if not _is_python_task("crie um site sobre cafe em HTML e CSS"):
        print("OK   | NAO detecta site como py task")
        passed += 1
    else:
        print("FAIL | confundiu site com py task")

    print(f"\n{passed}/{total} passou")
    return passed == total


def test_code_agent_model_selection():
    """CodeAgent v18: _needs_sonnet decide o modelo certo."""
    print("\n=== CodeAgent _needs_sonnet (escolha de modelo) ===")
    from agents.code_agent import _needs_sonnet

    sonnet_cases = [
        "crie um sistema profissional em python de agendamento de dentista",
        "site sobre buda com link do github.com/ognistie",
        "dashboard com secoes de relatorio",
        "plataforma de controle de pacientes",
    ]
    haiku_cases = [
        "crie um arquivo simples",
        "html basico",
        "pagina pequena",
    ]
    passed = 0
    total = len(sonnet_cases) + len(haiku_cases)
    for t in sonnet_cases:
        ok = _needs_sonnet(t)
        print(f"{'OK  ' if ok else 'FAIL'} | sonnet: {t!r}")
        if ok:
            passed += 1
    for t in haiku_cases:
        ok = not _needs_sonnet(t)
        print(f"{'OK  ' if ok else 'FAIL'} | haiku:  {t!r}")
        if ok:
            passed += 1
    print(f"\n{passed}/{total} passou")
    return passed == total


if __name__ == "__main__":
    ok1 = test_maestro_ambiguity_gate()
    ok2 = test_workflow_quarantine()
    ok3 = test_web_circuit_breaker()
    ok4 = test_auto_install_detection()
    ok5 = test_code_agent_validation()
    ok6 = test_inline_program_detection()
    ok7 = test_code_agent_model_selection()
    sys.exit(0 if all([ok1, ok2, ok3, ok4, ok5, ok6, ok7]) else 1)
