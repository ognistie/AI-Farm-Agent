"""
A/B das skills do catalogo: o MESMO pedido ao Code Agent com e sem as skills no prompt.

Nada e executado: so o plano (codigo gerado) e avaliado por regras em codigo, ligadas ao
que as skills pedem (frontend-experience-engineer, premium-ui-designer, design-system-architect,
senior-software-engineer). Usa o modelo de verdade (alguns centavos por pedido).
    python scripts/eval_skills.py            # 1 rodada
    python scripts/eval_skills.py --trials 2
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT.parent / ".env")
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

TASKS = [
    "faz um site de cafeteria com html css e js",
    "cria uma landing page para um estúdio de pilates com formulário de contato",
]

# criterio -> (descricao, funcao sobre o codigo gerado)
CHECKS = {
    "semantico": ("HTML semântico (header/nav/main/footer)",
                  lambda c: sum(t in c for t in ("<header", "<nav", "<main", "<footer")) >= 3),
    "responsivo": ("media query para celular", lambda c: "@media" in c),
    "tokens": ("cores em variáveis CSS (:root --x)", lambda c: ":root" in c and re.search(r"--[\w-]+\s*:", c) is not None),
    "foco": ("foco visível para teclado", lambda c: ":focus" in c),
    "sem_placeholder": ("sem lorem ipsum / TODO", lambda c: not re.search(r"lorem ipsum|\bTODO\b|título aqui", c, re.I)),
    "form_label": ("formulário com <label> (se houver form)", lambda c: "<form" not in c or "<label" in c),
    "img_fluida": ("imagens fluidas (max-width)", lambda c: "<img" not in c or "max-width" in c),
}


def plan_code(agent, task: str) -> str:
    plan = agent.plan({"task": task, "params": {}, "original_task": task})
    return "\n".join(str((s.get("params") or {}).get("code", "")) + str(s.get("params") or "")
                     for s in plan.get("steps", []))


def main(argv):
    import core.skills as skills_mod
    from agents.code_agent import CodeAgent
    from core.ai_client import get_client
    trials = int(argv[argv.index("--trials") + 1]) if "--trials" in argv else 1
    real = skills_mod.skills_for
    c0 = get_client().metrics["total_cost_usd"]
    rows = []
    for task in TASKS:
        for variant in ("sem skills", "com skills"):
            skills_mod.skills_for = real if variant == "com skills" else (lambda *a, **k: ("", []))
            for t in range(trials):
                code = plan_code(CodeAgent(), task)
                res = {k: bool(fn(code)) for k, (_, fn) in CHECKS.items()} if code else {k: False for k in CHECKS}
                rows.append((task, variant, t, res, len(code)))
                print(f"{variant:10} | {task[:48]:48} | {sum(res.values())}/{len(res)} | "
                      + " ".join(k for k, v in res.items() if not v))
    skills_mod.skills_for = real
    print()
    for variant in ("sem skills", "com skills"):
        got = [r for r in rows if r[1] == variant]
        score = sum(sum(r[3].values()) for r in got)
        print(f"{variant}: {score}/{len(got) * len(CHECKS)} critérios")
    print(f"Custo: US$ {get_client().metrics['total_cost_usd'] - c0:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
