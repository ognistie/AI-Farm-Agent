"""
Avalia os turnos da conversa com GPT-Live: esperar nas pausas, responder, delegar e parar.

Fala sintetica (Piper, local) entra como microfone na LiveConversation real. Nada toca na caixa
de som, nada vai para o Maestro, nenhum outro modelo e chamado: so a sessao Live e cobrada.
Cenarios e criterios ficam fixos antes de comparar variantes. Toda sessao soma em
memory/eval/live_spend.jsonl, e a rodada para antes de passar do teto de gasto acumulado.

    python scripts/eval_live_turns.py --allow-live --label baseline --trials 2
    python scripts/eval_live_turns.py --compare baseline candidato
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import tempfile
import threading
import time
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))

OUT = APP / "memory" / "eval"
USD_PER_SECOND = 0.05 / 60
SESSION_RESERVE_S = 25.0        # o que uma sessao pode gastar: nao comeca se isso estourar o teto
SESSION_LIMIT_S = 24.0
BACKCHANNEL_MAX_S = 0.6         # voz curta durante a fala ou pausa e sinal de escuta, nao interrupcao
VOICE_GAP_S = 0.4
AFTER_SPEECH_S = 5.0

# Trechos falados e pausas, em ordem. expect_delegation None = tanto faz.
SCENARIOS = {
    "pausa_no_meio": {"script": ["Eu queria que você me explicasse", 3.0, "como funciona um motor elétrico."],
                      "expect_delegation": None},
    "hesitacao": {"script": ["É... deixa eu pensar", 3.0, "qual é a capital do Peru?"], "expect_delegation": None},
    "pergunta": {"script": ["Qual é a capital do Peru?"], "expect_delegation": None},
    "tarefa": {"script": ["Abre a calculadora."], "expect_delegation": True},
    "conversa": {"script": ["Hoje o dia está bonito por aqui."], "expect_delegation": False},
    "interrupcao": {"script": ["Me conta uma história bem longa sobre um gato."], "interject": "Espera, para um pouco.",
                    "expect_delegation": False},
}


# ── Criterios (sem rede, testados em tests/test_eval_live_turns.py) ──
def merge_voice(chunks: list, gap: float = VOICE_GAP_S) -> list:
    """Chunks de voz (inicio, fim) viram falas: brecha curta ainda e a mesma fala."""
    merged: list = []
    for start, end in sorted(chunks):
        if merged and start - merged[-1][1] <= gap:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def grade(trace: dict) -> dict:
    """-> o que aconteceu em uma sessao. Tempos em segundos, medidos na chegada do audio."""
    voice = merge_voice(trace["voice"])
    pauses, said = trace.get("pauses", []), trace["said"]
    end_of_speech = said[-1][1] if said else 0.0
    # Voz curta so e sinal de escuta enquanto a pessoa ainda nao terminou: depois, "Lima." e resposta
    backchannels = sum(1 for start, end in voice if end - start <= BACKCHANNEL_MAX_S and start < end_of_speech)
    interrupted = any(end - start > BACKCHANNEL_MAX_S and start < p_end and end > p_start
                      for start, end in voice for p_start, p_end in pauses)
    after = [start for start, end in voice if start >= end_of_speech]
    out = {"responded": any(end > end_of_speech for start, end in voice),
           "first_voice_s": round(after[0] - end_of_speech, 2) if after else None,
           "interrupted_pause": interrupted if pauses else None, "backchannels": backchannels,
           "delegated": trace.get("delegated_at") is not None, "usage_s": trace.get("usage_s")}
    expected = trace.get("expect_delegation")
    if expected is not None:
        out["delegation_correct"] = out["delegated"] == expected
    if trace.get("interject_at") is not None:
        ongoing = [end for start, end in voice if start <= trace["interject_at"] + 0.1 and end >= trace["interject_at"]]
        out["yield_s"] = round(max(ongoing) - trace["interject_at"], 2) if ongoing else None
    return out


def summarize(rows: list) -> dict:
    def rate(key):
        values = [r[key] for r in rows if r.get(key) is not None]
        return (sum(1 for v in values if v), len(values))

    def median(key):
        values = [r[key] for r in rows if r.get(key) is not None]
        return round(statistics.median(values), 2) if values else None
    return {"sessoes": len(rows), "interrompeu_pausa": rate("interrupted_pause"), "respondeu": rate("responded"),
            "delegacao_correta": rate("delegation_correct"), "primeira_voz_mediana_s": median("first_voice_s"),
            "parar_mediana_s": median("yield_s"),
            "pedacos_por_fala": round(sum(len(r.get("user") or []) / max(1, r.get("segments", 1)) for r in rows)
                                      / max(1, len(rows)), 2),
            "segundos_cobrados": sum(r.get("usage_s") or 0 for r in rows)}


# ── Gasto ──
def spent_usd(path: Path) -> float:
    if not path.exists():
        return 0.0
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return sum(r["usd"] for r in rows)


def record_spend(path: Path, label: str, scenario: str, seconds: float, confirmed: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "label": label, "scenario": scenario,
                                 "seconds": seconds, "confirmed": confirmed,
                                 "usd": round(seconds * USD_PER_SECOND, 5)}) + "\n")


# ── Sessao real ──
class ScriptMic:
    def __init__(self, block_bytes: int, block_s: float):
        self.block_bytes, self.block_s = block_bytes, block_s
        self.frames: list = []
        self._lock = threading.Lock()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def speak(self, pcm: bytes) -> None:
        with self._lock:
            self.frames.extend(pcm[i:i + self.block_bytes].ljust(self.block_bytes, b"\0")
                               for i in range(0, len(pcm), self.block_bytes))

    @property
    def busy(self) -> bool:
        return bool(self.frames)

    def read(self) -> bytes:
        time.sleep(self.block_s)
        with self._lock:
            return self.frames.pop(0) if self.frames else bytes(self.block_bytes)


class SilentPlayer:
    """Nao toca nada: guarda quando a voz chegou e se comporta como a saida de som."""

    def __init__(self, clock):
        self.clock = clock
        self.chunks: list = []
        self._last_voice = float("-inf")
        self.underruns = 0

    @property
    def speaking(self) -> bool:
        return self.clock() < self._last_voice + 0.5

    def feed(self, raw: bytes) -> None:
        from core.voice.live import RATE
        from core.voice.live_session import _has_voice
        if _has_voice(raw):
            now = self.clock()
            self.chunks.append((now, now + len(raw) / 2 / RATE))
            self._last_voice = now

    def level(self) -> float:
        return 0.1 if self.speaking else 0.0

    def clear(self) -> None:
        self._last_voice = float("-inf")

    def close(self) -> None:
        pass


def synthesize(texts: list) -> dict:
    import numpy as np
    from core.voice.live import RATE
    from core.voice.tts import _Piper
    piper = _Piper("cadu", 1.0)
    audio = {}
    for text in texts:
        wave = piper.audio(text)
        positions = np.arange(0, len(wave) * RATE / piper.sr) * piper.sr / RATE
        audio[text] = np.interp(positions, np.arange(len(wave)), wave).astype("<i2").tobytes()
    return audio


def run_session(scenario: dict, audio: dict, cfg: dict) -> dict:
    from core.voice.live import RATE, VoiceBudget
    from core.voice.live_session import BLOCK, LiveConversation
    t0 = time.monotonic()
    clock = lambda: time.monotonic() - t0
    mic, player = ScriptMic(BLOCK * 2, BLOCK / RATE), SilentPlayer(clock)
    trace = {"voice": player.chunks, "said": [], "pauses": [], "delegated_at": None, "user": [], "agent": [],
             "expect_delegation": scenario["expect_delegation"], "failed": None}
    ready = threading.Event()
    with tempfile.TemporaryDirectory() as tmp:
        conv = LiveConversation(
            cfg, budget=VoiceBudget(Path(tmp) / "budget.json"), mic=lambda: mic, player=player,
            stats_path=Path(tmp) / "stats.jsonl",
            on_user_turn=lambda text: trace["user"].append(text),
            on_agent_turn=lambda text, from_result: trace["agent"].append(text),
            on_delegation=lambda delegation: trace.update(delegated_at=clock()),
            on_state=lambda state: ready.set() if state != "thinking" else None,
            on_failed=lambda reason: (trace.update(failed=reason), ready.set()))
        conv.start("")
        if ready.wait(10) and not trace["failed"]:
            time.sleep(0.5)

            def say(pcm: bytes) -> tuple:
                start = clock()
                mic.speak(pcm)
                while mic.busy and clock() < SESSION_LIMIT_S:
                    time.sleep(0.01)
                return start, clock()

            for part in scenario["script"]:
                if isinstance(part, str):
                    trace["said"].append(say(audio[part]))
                else:
                    start = clock()
                    time.sleep(part)
                    trace["pauses"].append((start, clock()))
            if scenario.get("interject"):
                # Fala por cima so depois de o agente estar falando ha uns 2 s
                while clock() < SESSION_LIMIT_S - 8 and sum(end - start for start, end in player.chunks) < 2.0:
                    time.sleep(0.05)
                trace["interject_at"] = clock()
                trace["said"].append(say(audio[scenario["interject"]]))
            limit = min(SESSION_LIMIT_S, clock() + AFTER_SPEECH_S)
            while clock() < limit:
                # Ja respondeu e ficou quieto: nao paga o resto da espera
                last = player.chunks[-1][1] if player.chunks else 0
                if last > trace["said"][-1][1] and clock() - last > 1.2:
                    break
                time.sleep(0.05)
        conv.stop()
        conv.wait_closed(6)
        usage = (conv.last_usage or {}).get("seconds")
    trace["usage_s"] = usage
    trace["wall_s"] = round(clock(), 1)
    return trace


def run(args) -> int:
    from dotenv import load_dotenv
    from core.config import get_config
    load_dotenv(APP.parent / ".env")
    load_dotenv(APP / ".env")
    spend = OUT / "live_spend.jsonl"
    cfg = dict(get_config().get("voice.live", {}) or {})
    cfg["conversation_idle_s"] = 30          # quem fecha aqui e o proprio roteiro
    names = args.scenarios or list(SCENARIOS)
    texts = {p for n in names for p in SCENARIOS[n]["script"] if isinstance(p, str)} \
        | {SCENARIOS[n]["interject"] for n in names if SCENARIOS[n].get("interject")}
    audio = synthesize(sorted(texts))
    rows = []
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"live_turns-{args.label}.jsonl"
    for trial in range(args.trials):
        for name in names:
            already = spent_usd(spend)
            if already + SESSION_RESERVE_S * USD_PER_SECOND > args.spend_cap_usd:
                print(f"PARADO: teto de US$ {args.spend_cap_usd:.2f} (gasto US$ {already:.3f}).")
                print(json.dumps(summarize(rows), ensure_ascii=False))
                return 3
            trace = run_session(SCENARIOS[name], audio, cfg)
            # Sem uso confirmado, conta o tempo inteiro da sessao: errar para mais
            seconds = trace["usage_s"] if trace["usage_s"] is not None else trace["wall_s"]
            record_spend(spend, args.label, name, seconds, trace["usage_s"] is not None)
            graded = grade(trace)
            row = {"label": args.label, "scenario": name, "trial": trial, "failed": trace["failed"], **graded,
                   "segments": len(trace["said"]),
                   "user": trace["user"], "agent": trace["agent"]}
            rows.append(row)
            with out.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"{name:<14} {trial} voz {graded['first_voice_s']} pausa-int {graded['interrupted_pause']} "
                  f"delegou {graded['delegated']} parar {graded.get('yield_s')} uso {trace['usage_s']} "
                  f"falha {trace['failed']} | gasto US$ {spent_usd(spend):.3f}", flush=True)
    print(json.dumps(summarize(rows), ensure_ascii=False))
    return 0


def compare(labels: list) -> int:
    for label in labels:
        path = OUT / f"live_turns-{label}.jsonl"
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        for row in rows:
            # Rodadas antigas nao guardavam isso: vem do proprio cenario
            scenario = SCENARIOS[row["scenario"]]
            row.setdefault("segments", sum(isinstance(p, str) for p in scenario["script"]) + bool(scenario.get("interject")))
        print(label, json.dumps(summarize(rows), ensure_ascii=False))
    print("gasto total US$", round(spent_usd(OUT / "live_spend.jsonl"), 3))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--allow-live", action="store_true", help="permite sessoes cobradas pelo provedor")
    parser.add_argument("--label", default="")
    parser.add_argument("--trials", type=int, default=2)
    parser.add_argument("--scenarios", nargs="*", choices=list(SCENARIOS))
    parser.add_argument("--spend-cap-usd", type=float, default=1.0, help="teto do gasto acumulado de todas as rodadas")
    parser.add_argument("--compare", nargs="+", metavar="LABEL")
    args = parser.parse_args()
    if args.compare:
        return compare(args.compare)
    if not args.allow_live or not args.label:
        parser.error("use --allow-live e --label: cada sessao e cobrada pelo provedor")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
