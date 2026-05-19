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
    ok4 = test_code_agent_model_selection()
    sys.exit(0 if all([ok1, ok2, ok3, ok4]) else 1)
