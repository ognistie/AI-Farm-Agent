"""
Smoke test do CodeAgent v26 — valida o classificador heurístico e a sintaxe
dos writer scripts SEM chamar a API Anthropic.

Roda: python scripts/smoke_code_agent.py
"""

import ast
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.code_agent import _classify_intent_heuristic, CodeAgent


def assert_eq(expected, got, label):
    status = "OK  " if expected == got else "FAIL"
    print(f"{status} | {label} | esperado={expected!r} got={got!r}")
    return expected == got


def test_intent_classifier():
    print("\n=== Intent classifier (heuristica) ===")
    cases = [
        ("crie um sistema de agendamento de salas",          "project_full"),
        ("dashboard de vendas com graficos",                 "project_full"),
        ("crie um site sobre cafe",                          "website_simple"),
        ("crie uma landing page de curso de python",         "website_simple"),
        ("crie um arquivo python que renomeia imagens",      "single_file"),
        ("escreva uma classe Calculadora em python",         "single_file"),
        ("edite o arquivo app.py adicionando rota /login",   "edit_existing"),
        ("abra o vs code na pasta meu-projeto",              "open_vscode_folder"),
        # Bug reportado pelo usuario: pediu HTML, recebeu CSS+JS extras
        ("crie um site sobre buda apenas em html",           "single_file"),
        ("pagina sobre cafe so html",                        "single_file"),
        ("landing page html simples",                        "single_file"),
    ]
    passed = 0
    for task, expected in cases:
        intent = _classify_intent_heuristic(task) or {}
        if assert_eq(expected, intent.get("mode"), task):
            passed += 1
    print(f"\n{passed}/{len(cases)} passou")
    return passed == len(cases)


def test_writer_scripts_syntax():
    """Garante que os writer scripts gerados sao Python valido."""
    print("\n=== Writer scripts (sintaxe) ===")
    # Cria a instancia sem inicializacao remota — esquiva via __new__
    agent = CodeAgent.__new__(CodeAgent)
    agent.model = "claude-sonnet-4-20250514"

    cases = [
        ("project", agent._build_writer_project(
            folder_name="projeto_teste",
            files_dict={"main.py": "print('hi')", "README.md": "# t"},
            open_browser=False, browser_file="", run_file="main.py",
            open_vscode=True,
        )),
        ("single_file", agent._build_writer_single_file(
            filename="rename_imgs.py",
            content="import os\nprint('renaming')\n",
            target_dir="Desktop", run_after=False, open_vscode=True,
        )),
        ("edit_existing", agent._build_writer_edit_existing(
            target_path_hint="app.py",
            instruction="adicionar rota /login",
            open_vscode=True,
        )),
        ("open_folder", agent._build_open_folder_script("meu-projeto")),
    ]
    passed = 0
    for label, script in cases:
        try:
            ast.parse(script)
            print(f"OK   | writer {label} | {len(script)} chars")
            passed += 1
        except SyntaxError as e:
            print(f"FAIL | writer {label} | SyntaxError: {e}")
    print(f"\n{passed}/{len(cases)} passou")
    return passed == len(cases)


def test_maestro_ambiguity_gate():
    """Cenarios A e J do briefing — prompts vagos disparam pedido de clarificacao."""
    print("\n=== Maestro ambiguity gate (cenarios A e J) ===")
    from agents.maestro import _detect_ambiguity

    # Casos onde a heuristica DEVE bloquear (cenarios A e J do briefing).
    # Greetings/saudacoes ficam fora — heuristica e intencionalmente
    # conservadora; o LLM responde a saudacao com naturalidade.
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
    # Bumps repetidos devem chegar ao limite
    for i in range(CIRCUIT_BREAKER_MAX_ATTEMPTS):
        n = agent._bump_attempt(task)
    extra = agent._bump_attempt(task)
    expected = CIRCUIT_BREAKER_MAX_ATTEMPTS + 1
    ok = extra == expected
    print(f"{'OK  ' if ok else 'FAIL'} | apos {expected} bumps consecutivos = circuito aberto")
    return ok


if __name__ == "__main__":
    ok1 = test_intent_classifier()
    ok2 = test_writer_scripts_syntax()
    ok3 = test_maestro_ambiguity_gate()
    ok4 = test_web_circuit_breaker()
    sys.exit(0 if (ok1 and ok2 and ok3 and ok4) else 1)
