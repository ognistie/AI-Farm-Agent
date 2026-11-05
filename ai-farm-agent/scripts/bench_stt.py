"""
Benchmark da transcricao de voz (local, sem API): tempo x precisao.

Gera as frases com a voz local (Piper), soma um ruido leve e transcreve com
cada configuracao. Mede o tempo de transcricao e a taxa de erro de palavras
(WER) depois de normalizar (minusculas, sem acento e pontuacao).

Uso:
    python scripts/bench_stt.py                  # beam 5 x beam 1, modelo small
    python scripts/bench_stt.py --beams 5 3 1 --reps 2
"""
from __future__ import annotations

import argparse
import statistics
import sys
import time
import unicodedata
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Pedidos reais (historico/eval_voice): abrir, pesquisar, continuar, ditar, conversar
PHRASES = [
    "abre o youtube",
    "abre o bloco de notas e escreve reunião às três",
    "pesquisa receita de pão de queijo no google",
    "agora toca o segundo vídeo",
    "abre o excel e preenche a primeira linha com produto preço e quantidade",
    "quanto é cento e vinte e oito vezes quarenta e sete",
    "abre as configurações do windows e clica em sistema",
    "cria um site para a padaria pão dourado",
    "muda a cor do título para roxo",
    "manda uma mensagem pro joão no whatsapp dizendo que eu chego às oito",
    "fecha o paint",
    "que horas são",
    "pesquisa o preço do fone jbl tune quinhentos e vinte no mercado livre",
    "organiza a pasta downloads por tipo de arquivo",
    "valeu, ficou ótimo",
    "abre o vs code na pasta do projeto",
]


def norm(t: str) -> list[str]:
    t = unicodedata.normalize("NFKD", t.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = "".join(c if c.isalnum() or c.isspace() else " " for c in t)
    return t.split()


def wer(ref: str, hyp: str) -> float:
    r, h = norm(ref), norm(hyp)
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (r[i - 1] != h[j - 1]))
            prev, d[j] = d[j], cur
    return d[len(h)] / max(1, len(r))


def synth(phrases: list[str], voice: str) -> list[np.ndarray]:
    from core.voice.tts import _Piper
    p = _Piper(voice, 1.05)
    rng = np.random.default_rng(7)
    out = []
    for text in phrases:
        a = p.audio(text).astype(np.float32) / 32768.0
        idx = np.linspace(0, len(a) - 1, int(len(a) * 16000 / p.sr))   # para 16 kHz
        a = np.interp(idx, np.arange(len(a)), a).astype(np.float32)
        a = np.concatenate([np.zeros(4000, np.float32), a, np.zeros(6000, np.float32)])
        a += rng.normal(0, 0.004, len(a)).astype(np.float32)            # ruido de fundo leve
        out.append(a)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="small")
    ap.add_argument("--beams", type=int, nargs="+", default=[5, 1])
    ap.add_argument("--voices", nargs="+", default=["cadu", "faber"])
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--chunks", type=int, nargs="+", default=[0], help="janela em s (0 = 30 s padrao)")
    args = ap.parse_args()

    from core.voice.stt import Transcriber
    audios = []
    for v in args.voices:
        audios += [(p, a) for p, a in zip(PHRASES, synth(PHRASES, v))]
    print(f"{len(audios)} falas ({len(PHRASES)} frases x {len(args.voices)} vozes), modelo {args.model}\n")

    stt = Transcriber(args.model, "int8")
    stt.load()
    stt.beam_size = args.beams[0]
    stt.transcribe(audios[0][1])                       # aquece

    rows = []
    for beam, chunk in [(b, c) for b in args.beams for c in args.chunks]:
        stt.beam_size, stt.chunk_length = beam, (chunk or None)
        stt.transcribe(audios[0][1])                   # aquece esta configuracao
        secs, errs, exact = [], [], 0
        for _ in range(args.reps):
            for ref, a in audios:
                t = time.perf_counter()
                hyp = stt.transcribe(a)["text"]
                secs.append(time.perf_counter() - t)
                e = wer(ref, hyp)
                errs.append(e)
                exact += e == 0
        n = len(errs)
        rows.append((f"{beam}/{chunk or 30}s", statistics.mean(secs), statistics.median(secs), max(secs),
                     statistics.mean(errs), exact / n))
    print("beam/janela | tempo medio | mediana | pior  | WER   | frases perfeitas")
    for b, mean, med, worst, w, ex in rows:
        print(f"{b:>11} | {mean:9.2f}s | {med:6.2f}s | {worst:4.2f}s | {w:5.1%} | {ex:6.0%}")


if __name__ == "__main__":
    main()
