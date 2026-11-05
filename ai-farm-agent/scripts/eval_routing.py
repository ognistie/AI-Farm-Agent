"""
Avaliacao do roteamento do Maestro (qual agente faz o pedido) com o modelo de verdade.

Gabarito tirado do historico REAL (desktop/data/history.jsonl): pedidos que deram certo,
com os agentes que de fato resolveram. Compara configuracoes de raciocinio por tempo e
acerto. Pedidos que o atalho sem IA resolve ("abrir o YouTube") ficam de fora.

Uso:
    python scripts/eval_routing.py                    # com raciocinio x sem raciocinio
    python scripts/eval_routing.py --n 20 --trials 1
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", (t or "").lower())
    return re.sub(r"\s+", " ", "".join(c for c in t if not unicodedata.combining(c))).strip()


def load_cases(n: int) -> list[dict]:
    from agents.maestro import fast_open_plan
    rows = [json.loads(l) for l in (ROOT / "desktop/data/history.jsonl").read_text(encoding="utf-8").splitlines()
            if l.strip()]
    seen, cases = set(), []
    for r in reversed(rows):                                  # mais recentes primeiro
        m = r.get("metrics") or {}
        agents = sorted({(s.get("agent") or "").upper() for s in r.get("subtasks") or [] if s.get("agent")})
        task = (r.get("resolved") or r.get("task") or "").strip()
        if (not r.get("success") or r.get("dry_run") or not agents or "MAESTRO" not in (m.get("by_agent") or {})
                or len(task) < 8 or fast_open_plan(task)):
            continue
        key = _norm(task)[:60]
        if key in seen:
            continue
        seen.add(key)
        cases.append({"task": task, "agents": agents})
        if len(cases) >= n:
            break
    return cases


def run(cases: list[dict], thinking_off: bool, trials: int) -> dict:
    from core.config import get_config
    from core.ai_client import get_client
    from agents.maestro import Maestro
    cfg = get_config()
    cfg._data.setdefault("agent_thinking", {})["maestro"] = "off" if thinking_off else "on"
    m = Maestro.__new__(Maestro)
    m._config, m._client = cfg, get_client()
    m.model, m.effort = cfg.get_model("maestro"), cfg.get_effort("maestro")
    secs, ok, outs, misses = [], 0, 0, []
    for _ in range(trials):
        for c in cases:
            before = m._client.metrics
            t0 = time.time()
            plan = m._ask(c["task"])
            secs.append(time.time() - t0)
            outs += m._client.metrics["total_output_tokens"] - before["total_output_tokens"]
            got = sorted({(s.get("agent") or "").upper() for s in plan.get("subtasks") or []})
            if got == c["agents"]:
                ok += 1
            else:
                misses.append((c["task"][:70], c["agents"], got or plan.get("question", "")[:40]))
    n = len(cases) * trials
    return {"ok": ok, "n": n, "p50": statistics.median(secs), "p90": sorted(secs)[int(0.9 * (len(secs) - 1))],
            "out": outs / n, "misses": misses}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--trials", type=int, default=1)
    args = ap.parse_args()
    try:
        from dotenv import load_dotenv, find_dotenv
        load_dotenv(find_dotenv(usecwd=True))
    except ImportError:
        pass
    cases = load_cases(args.n)
    print(f"{len(cases)} pedidos reais do historico (gabarito: agentes que resolveram)\n")
    for label, off in (("com raciocinio (atual)", False), ("sem raciocinio", True)):
        r = run(cases, off, args.trials)
        print(f"{label:24} acerto {r['ok']}/{r['n']} · mediana {r['p50']:.2f}s · p90 {r['p90']:.2f}s · "
              f"{r['out']:.0f} tokens de saida/pedido")
        for t, want, got in r["misses"]:
            print(f"   ✗ {t} | esperado {want} | veio {got}")


if __name__ == "__main__":
    main()
