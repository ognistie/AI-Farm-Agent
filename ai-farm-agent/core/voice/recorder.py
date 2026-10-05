"""
Microfone -> trecho de fala.

Dois jeitos:
- manual=True  (mensagem de audio): grava tudo do clique ate `stop`; nao corta no silencio.
- manual=False (conversa ao vivo): comeca quando a energia passa do ruido de
  fundo por ~90 ms e termina apos `silence_s` de silencio. Enquanto `paused()`
  for verdadeiro (o agente esta falando) o audio e descartado, para o agente
  nao ouvir a propria voz.
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


def is_speech(rms: float, floor: float) -> bool:
    return rms > max(floor * 3.0, 0.012)


def record_utterance(stop: threading.Event,
                     on_level: Optional[Callable[[float], None]] = None,
                     start_timeout: Optional[float] = 7.0, silence_s: float = 0.9,
                     max_s: float = 25.0, manual: bool = False,
                     paused: Optional[Callable[[], bool]] = None) -> Optional[np.ndarray]:
    """-> audio float32 16 kHz mono, ou None se ninguem falou (ou cancelado)."""
    import sounddevice as sd
    frames: list = []
    pre: list = []
    noise: list = []
    started, run, silence = manual, 0, 0.0
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
            if paused and paused():
                if not manual:                       # agente falando: descarta e recomeca
                    frames, pre, started, run, silence = [], [], False, 0, 0.0
                    t0 = time.time()
                continue
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
                silence = 0.0 if rms > max(floor * 2.2, 0.009) else silence + BLOCK / SR
                if silence >= silence_s or len(frames) * BLOCK / SR >= max_s:
                    break
    if not frames or len(frames) * BLOCK / SR < MIN_SPEECH_S:
        return None
    return np.concatenate(frames).astype(np.float32)
