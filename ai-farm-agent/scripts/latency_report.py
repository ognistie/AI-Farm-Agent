"""
Relatorio de latencia a partir do historico real (desktop/data/history.jsonl).

Mostra, por tipo de pedido, a mediana e o P90 do tempo total, as chamadas de
IA e, nas execucoes com `timing` (a partir da rodada 5), onde o tempo foi:
resolver, Maestro, plano do agente, passos no PC e tempo esperando o modelo.

Uso:
    python scripts/latency_report.py                 # tudo
    python scripts/latency_report.py --since 2026-10-09
    python scripts/latency_report.py --last 50
    python scripts/latency_report.py --voice         # conversa: do fim da fala ate cada etapa
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

HISTORY = Path(__file__).resolve().parent.parent / "desktop" / "data" / "history.jsonl"
VOICE = Path(__file__).resolve().parent.parent / "memory" / "voice_latency.jsonl"
VOICE_STAGES = (("first_delta_s", "transcricao chega"), ("agent_voice_s", "agente comeca a falar"),
                ("flush_s", "fala dada por encerrada"), ("understood_s", "app entende o pedido"),
                ("dispatched_s", "pedido enviado"), ("started_s", "execucao comeca"), ("finished_s", "tarefa termina"))


def voice_report(rows: list) -> str:
    """Mediana e P90 de cada etapa, em segundos desde o fim da fala."""
    lines = [f"{len(rows)} falas ({sum(1 for r in rows if r.get('kind') == 'command')} pedidos)"]
    for key, label in VOICE_STAGES:
        values = sorted(r[key] for r in rows if isinstance(r.get(key), (int, float)))
        if values:
            p90 = values[min(len(values) - 1, int(len(values) * 0.9))]
            lines.append(f"  {label:<26} mediana {statistics.median(values):5.2f} s   P90 {p90:5.2f} s   n={len(values)}")
    return "\n".join(lines)

KINDS = [
    ("abrir app/site", re.compile(r"^(?:abr[aei]r?|abrir|abre|entr[ae]|acess[ae])\b(?!.*\b(?:e|pesquis|cri|escrev|faz|fa[çc]a)\b)", re.I)),
    ("pesquisar", re.compile(r"\b(?:pesquis|procur|busc)", re.I)),
    ("planilha/dados", re.compile(r"\b(?:planilha|excel|gr[aá]fico|tabela)\b", re.I)),
    ("site/codigo", re.compile(r"\b(?:site|script|c[oó]digo|programa|landing|p[aá]gina web)\b", re.I)),
    ("escrever/ditar", re.compile(r"\b(?:escrev|anot|digit)", re.I)),
]


def kind_of(task: str) -> str:
    for name, rx in KINDS:
        if rx.search(task or ""):
            return name
    return "outros"


def pct(values: list[float], q: float) -> float:
    v = sorted(values)
    return v[min(len(v) - 1, int(round(q * (len(v) - 1))))] if v else 0.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="", help="AAAA-MM-DD")
    ap.add_argument("--last", type=int, default=0)
    ap.add_argument("--voice", action="store_true", help="tempos da conversa de voz")
    args = ap.parse_args()

    rows = [json.loads(l) for l in HISTORY.read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.voice:
        lines = VOICE.read_text(encoding="utf-8").splitlines() if VOICE.exists() else []
        voice = [r for r in map(json.loads, lines) if r.get("at", "") >= args.since]
        print(voice_report(voice[-args.last:] if args.last else voice))
        return
    rows = [r for r in rows if not r.get("dry_run") and r.get("started_at", "") >= args.since]
    if args.last:
        rows = rows[-args.last:]
    if not rows:
        print("Sem execucoes no periodo.")
        return

    groups = defaultdict(list)
    for r in rows:
        groups[kind_of(r.get("task", ""))].append(r)

    print(f"{len(rows)} execucoes  ({rows[0]['started_at'][:10]} a {rows[-1]['started_at'][:10]})\n")
    print(f"{'tipo':16} {'n':>4} {'mediana':>8} {'P90':>7} {'IA/tarefa':>9} {'sucesso':>8}")
    for name in [k for k, _ in KINDS] + ["outros"]:
        g = groups.get(name)
        if not g:
            continue
        secs = [r["duration_ms"] / 1000 for r in g]
        calls = [r.get("metrics", {}).get("api_calls", 0) for r in g]
        ok = sum(bool(r.get("success")) for r in g) / len(g)
        print(f"{name:16} {len(g):>4} {statistics.median(secs):7.1f}s {pct(secs, .9):6.1f}s "
              f"{statistics.mean(calls):9.1f} {ok:8.0%}")

    timed = [r for r in rows if r.get("timing")]
    if timed:
        print(f"\nOnde o tempo foi ({len(timed)} execucoes com medicao por fase, mediana em s):")
        phases = ["resolve", "maestro", "agent_plan", "steps"]
        print(f"{'tipo':16} " + " ".join(f"{p:>10}" for p in phases) + f" {'esperando IA':>13}")
        tg = defaultdict(list)
        for r in timed:
            tg[kind_of(r.get("task", ""))].append(r)
        for name, g in tg.items():
            cols = [statistics.median(r["timing"].get(p, 0) / 1000 for r in g) for p in phases]
            llm = statistics.median(r.get("metrics", {}).get("llm_ms", 0) / 1000 for r in g)
            print(f"{name:16} " + " ".join(f"{c:10.1f}" for c in cols) + f" {llm:13.1f}")


if __name__ == "__main__":
    main()
