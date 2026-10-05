"""
Resposta falada.

Padrao: Piper (voz neural LOCAL, pt-BR, ~0,5 s por frase) tocada pelo
sounddevice, frase a frase, interrompivel. Reserva: voz do Windows (SAPI).
Tudo numa thread propria com fila: `speak` substitui a fala anterior,
`stop` cala na hora (para o usuario poder interromper falando).
"""

from __future__ import annotations

import queue
import re
import threading
import time

SVSF_ASYNC, SVSF_PURGE = 1, 2
PIPER_REPO = "rhasspy/piper-voices"


def clean_for_speech(text: str, limit: int = 240) -> str:
    """Tira o que nao se fala bem: URLs, caminhos, emojis, 'Trilha', markdown."""
    t = re.split(r"\n?Trilha( \(\d+ turnos\))?:", text or "")[0]
    t = re.sub(r"https?://\S+|www\.\S+", "", t)
    t = re.sub(r"[A-Za-z]:[\\/][^\s,;]+", "", t)
    t = re.sub(r"[\U0001F000-\U0001FAFF☀-➿️✅❌⚠️⛔↩️🌐📂🎯👁️]", "", t)
    t = re.sub(r"[*_`#>|]", "", t)
    t = re.sub(r"\s+", " ", t).strip(" -—:")
    if len(t) > limit:
        cut = t[:limit]
        t = cut[:cut.rfind(".") + 1] if "." in cut[40:] else cut.rsplit(" ", 1)[0] + "..."
    return t


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


class _Piper:
    def __init__(self, voice: str, rate: float):
        from huggingface_hub import hf_hub_download
        from piper import PiperVoice
        base = f"pt/pt_BR/{voice}/medium/pt_BR-{voice}-medium.onnx"
        model = hf_hub_download(PIPER_REPO, base)
        hf_hub_download(PIPER_REPO, base + ".json")
        self.voice = PiperVoice.load(model)
        self.sr = self.voice.config.sample_rate
        self.rate = rate
        self.name = f"Piper {voice} (pt-BR, local)"

    def audio(self, text: str):
        import numpy as np
        from piper import SynthesisConfig
        cfg = SynthesisConfig(length_scale=1.0 / max(0.5, self.rate))
        chunks = [c.audio_int16_array for c in self.voice.synthesize(text, syn_config=cfg)]
        return np.concatenate(chunks) if chunks else None


class Speaker:
    def __init__(self, engine: str = "piper", voice: str = "cadu", rate: float = 1.05):
        self.engine_name, self.voice_id, self.rate = engine, voice, rate
        self._q: "queue.Queue[tuple]" = queue.Queue()
        self._speaking = threading.Event()
        self._cut = threading.Event()
        self.voice_name = ""
        self.error = ""
        self.last_end = 0.0             # quando terminou a ultima fala (eco)
        threading.Thread(target=self._worker, daemon=True, name="tts").start()

    @property
    def speaking(self) -> bool:
        return self._speaking.is_set()

    def speak(self, text: str) -> None:
        text = clean_for_speech(text)
        if text:
            self._cut.set()                 # a fala nova substitui a anterior
            self._q.put(("say", text))

    def stop(self) -> None:
        self._cut.set()
        self._q.put(("stop", ""))

    def wait(self, timeout: float = 25.0) -> None:
        end = time.time() + timeout
        time.sleep(0.15)
        while (self._speaking.is_set() or not self._q.empty()) and time.time() < end:
            time.sleep(0.05)

    # ── worker ────────────────────────────────────────────────────
    def _init_engine(self):
        if self.engine_name == "piper":
            try:
                eng = _Piper(self.voice_id, self.rate)
                self.voice_name = eng.name
                return eng
            except Exception as e:
                self.error = f"Piper indisponível ({type(e).__name__}: {e}); usando a voz do Windows"
        import pythoncom
        import win32com.client
        pythoncom.CoInitialize()
        sapi = win32com.client.Dispatch("SAPI.SpVoice")
        for v in sapi.GetVoices():
            d = v.GetDescription()
            if "pt-BR" in d or "Portug" in d or "Maria" in d:
                sapi.Voice = v
                self.voice_name = d
                break
        return sapi

    def _play_piper(self, eng, text: str) -> None:
        import sounddevice as sd
        for sentence in _sentences(text):
            if self._cut.is_set():
                return
            audio = eng.audio(sentence)
            if audio is None or self._cut.is_set():
                continue
            sd.play(audio, eng.sr)
            dur = len(audio) / eng.sr
            end = time.time() + dur + 0.1
            while time.time() < end:
                if self._cut.is_set():
                    sd.stop()
                    return
                time.sleep(0.03)

    def _worker(self) -> None:
        try:
            eng = self._init_engine()
        except Exception as e:
            self.error = f"{type(e).__name__}: {e}"
            return
        piper = isinstance(eng, _Piper)
        while True:
            try:
                cmd, text = self._q.get(timeout=0.1)
            except queue.Empty:
                if not piper and self._speaking.is_set() and eng.WaitUntilDone(0):
                    self._speaking.clear()
                continue
            if cmd == "stop":
                if not piper:
                    eng.Speak("", SVSF_ASYNC | SVSF_PURGE)
                self._speaking.clear()
                continue
            # so a fala MAIS recente importa (as anteriores foram substituidas)
            while not self._q.empty():
                try:
                    nxt = self._q.get_nowait()
                    if nxt[0] == "say":
                        text = nxt[1]
                except queue.Empty:
                    break
            self._cut.clear()
            self._speaking.set()
            if piper:
                try:
                    self._play_piper(eng, text)
                except Exception as e:
                    self.error = f"reprodução falhou: {e}"
                self.last_end = time.time()
                self._speaking.clear()
            else:
                eng.Speak(text, SVSF_ASYNC | SVSF_PURGE)
