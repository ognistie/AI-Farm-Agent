"""
Transcricao local (faster-whisper), em portugues, sem enviar audio para fora.

O modelo carrega uma vez (em segundo plano ao ligar a voz). A primeira vez
baixa o modelo (~480 MB no 'small') para o cache do Hugging Face.

Nota Windows: a biblioteca `av` (decodificar ARQUIVOS de audio) pode ser
bloqueada pelo Controle Inteligente de Aplicativos. Aqui o audio ja chega
como numpy do microfone, entao `av` nao e necessaria: se o import dela
falhar, registramos um modulo vazio so para o faster-whisper importar.
Nenhuma politica do Windows e alterada.
"""

from __future__ import annotations

import sys
import threading
import time
import types

import numpy as np

# Dica curta e neutra. Uma lista de apps aqui fazia o modelo "ouvir" nomes que
# ninguem disse ("... O YouTube." no fim da frase): a correcao de nomes fica
# com o dicionario (core/lexicon.py), depois da transcricao.
PROMPT = "Pedido falado em português do Brasil para um assistente no computador."

# Abaixo disso o trecho e provavelmente ruido/alucinacao e e descartado
MIN_SEG_LOGPROB = -1.0
MAX_NO_SPEECH = 0.6


def _import_whisper():
    try:
        import av  # noqa: F401
    except Exception:
        for k in [k for k in sys.modules if k == "av" or k.startswith("av.")]:
            del sys.modules[k]
        sys.modules["av"] = types.ModuleType("av")   # so decode de arquivo usa; nao usamos
    from faster_whisper import WhisperModel
    return WhisperModel


class Transcriber:
    def __init__(self, model_size: str = "small", compute_type: str = "int8"):
        self.model_size = model_size
        self.compute_type = compute_type
        self._model = None
        self._lock = threading.Lock()
        self.error = ""
        self.load_seconds = 0.0

    @property
    def ready(self) -> bool:
        return self._model is not None

    def load(self) -> bool:
        with self._lock:
            if self._model is not None:
                return True
            t = time.time()
            try:
                WhisperModel = _import_whisper()
                import os
                self._model = WhisperModel(self.model_size, device="cpu", compute_type=self.compute_type,
                                           cpu_threads=max(2, (os.cpu_count() or 4) - 1))
                self.error = ""
            except Exception as e:
                self.error = f"{type(e).__name__}: {e}"
                return False
            self.load_seconds = time.time() - t
            return True

    def preload_async(self) -> None:
        threading.Thread(target=self.load, daemon=True, name="stt-preload").start()

    def transcribe(self, audio: np.ndarray) -> dict:
        """-> {"text", "confidence" (0-1), "seconds"}"""
        if not self.load():
            return {"text": "", "confidence": 0.0, "seconds": 0.0, "error": self.error}
        t = time.time()
        segments, _info = self._model.transcribe(
            audio, language="pt", beam_size=5, temperature=0.0,
            vad_filter=True, vad_parameters={"min_silence_duration_ms": 400, "speech_pad_ms": 250},
            condition_on_previous_text=False, initial_prompt=PROMPT,
            no_repeat_ngram_size=3, repetition_penalty=1.1,
            compression_ratio_threshold=2.2, log_prob_threshold=MIN_SEG_LOGPROB,
            no_speech_threshold=MAX_NO_SPEECH, without_timestamps=True)
        segs = list(segments)
        kept = [s for s in segs if not (s.no_speech_prob > MAX_NO_SPEECH and s.avg_logprob < MIN_SEG_LOGPROB)
                and s.avg_logprob > -1.4]
        text = " ".join(s.text.strip() for s in kept).strip()
        if text.strip(" .").lower() == PROMPT.strip(" .").lower():
            text = ""                       # eco da dica em audio sem fala
        conf = float(np.exp(np.mean([s.avg_logprob for s in kept]))) if kept else 0.0
        return {"text": text, "confidence": round(conf, 2), "seconds": round(time.time() - t, 2),
                "dropped": len(segs) - len(kept)}
