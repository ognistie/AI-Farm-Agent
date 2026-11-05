"""
Microfone -> trecho de fala.

Dois jeitos:
- manual=True  (mensagem de audio): grava tudo do clique ate `stop`; nao corta no silencio.
- manual=False (conversa ao vivo): comeca quando a energia passa do ruido de
  fundo por ~90 ms e termina apos `silence_s` de silencio. Enquanto `paused()`
  for verdadeiro (o agente esta falando) o audio e descartado, para o agente
  nao ouvir a propria voz — EXCETO quando a pessoa fala por cima (barge-in):
  energia bem acima do eco da caixa de som por ~240 ms chama `on_barge()` (o
  agente se cala) e a fala e gravada desde o comeco.
Mantem ~300 ms antes do inicio para nao cortar a primeira silaba.
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Optional

import numpy as np

SR = 16000
BLOCK = 480                # 30 ms
MIN_SPEECH_S = 0.35        # menos que isso e estalo/tosse
BARGE_BLOCKS = 8           # ~240 ms de voz por cima do agente
BARGE_RATIO = 1.8          # quantas vezes acima do eco (p90 do ultimo ~1 s)
BARGE_MIN = 0.03           # e nunca abaixo disso (voz perto do microfone)


def is_speech(rms: float, floor: float) -> bool:
    return rms > max(floor * 3.0, 0.012)


def record_utterance(stop: threading.Event,
                     on_level: Optional[Callable[[float], None]] = None,
                     start_timeout: Optional[float] = 7.0, silence_s: float = 0.9,
                     max_s: float = 25.0, manual: bool = False,
                     paused: Optional[Callable[[], bool]] = None,
                     on_barge: Optional[Callable[[], None]] = None,
                     on_pause: Optional[Callable[[np.ndarray], None]] = None,
                     pause_s: float = 0.3) -> Optional[np.ndarray]:
    """-> audio float32 16 kHz mono, ou None se ninguem falou (ou cancelado).

    on_pause(audio_ate_aqui): chamado quando a fala faz uma pausa de `pause_s` (antes de
    `silence_s` confirmar o fim) — quem chama ja pode transcrever; se a fala continuar,
    descarta. Ganha (silence_s - pause_s) em cada fala."""
    import sounddevice as sd
    frames: list = []
    pre: list = []
    noise: list = []
    started, run, silence = manual, 0, 0.0
    echo: list = []            # energia do eco enquanto o agente fala
    bpre: list = []            # audio recente durante a fala do agente (inicio da interrupcao)
    brun, barged = 0, False
    t0 = time.time()
    with sd.InputStream(samplerate=SR, channels=1, dtype="float32", blocksize=BLOCK) as st:
        while True:
            data, _ = st.read(BLOCK)
            x = data[:, 0].copy()
            rms = float(np.sqrt(np.mean(x * x)) + 1e-9)
            if on_level:
                on_level(min(1.0, rms * 18))
            if stop.is_set():
                break
            if paused and not barged and paused():
                if not manual:
                    if on_barge is not None:
                        # pessoa falando POR CIMA do agente: bem acima do eco, por ~240 ms
                        ref = float(np.percentile(echo, 90)) if len(echo) >= 8 else 1.0
                        loud = rms > max(ref * BARGE_RATIO, BARGE_MIN)
                        if not loud:
                            echo = (echo + [rms])[-33:]   # so o eco ensina a referencia (nao a voz por cima)
                        bpre = (bpre + [x])[-12:]
                        brun = brun + 1 if loud else 0
                        if brun >= BARGE_BLOCKS:
                            barged = True
                            on_barge()
                            frames, started, silence = list(bpre), True, 0.0
                            continue
                    # agente falando: descarta e recomeca
                    frames, pre, started, run, silence = [], [], False, 0, 0.0
                    t0 = time.time()
                continue
            if echo and not barged:
                echo, bpre, brun = [], [], 0
            if manual:
                frames.append(x)
                if len(frames) * BLOCK / SR >= max_s:
                    break
                continue
            floor = float(np.median(noise)) if noise else 0.004
            if not started:
                if len(noise) < 15 and not is_speech(rms, floor):
                    noise.append(rms)
                pre = (pre + [x])[-10:]
                run = run + 1 if is_speech(rms, floor) else 0
                if run >= 3:
                    started = True
                    frames.extend(pre)
                elif start_timeout is not None and time.time() - t0 > start_timeout:
                    return None
            else:
                frames.append(x)
                was = silence
                silence = 0.0 if rms > max(floor * 2.2, 0.009) else silence + BLOCK / SR
                if (on_pause is not None and was < pause_s <= silence
                        and len(frames) * BLOCK / SR >= MIN_SPEECH_S + pause_s):
                    on_pause(np.concatenate(frames).astype(np.float32))
                if silence >= silence_s or len(frames) * BLOCK / SR >= max_s:
                    break
    if not frames or len(frames) * BLOCK / SR < MIN_SPEECH_S:
        return None
    return np.concatenate(frames).astype(np.float32)
