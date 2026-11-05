"""One paid narration at a time, with a latest-only pending slot and local feedback."""
import threading
import time
import logging
from core.voice.tts import Speaker, clean_for_speech
from core.voice.live import LiveNarrator, RATE


def _play(audio, cancel):
    import sounddevice as sd
    # Own stream: an earcon must not terminate another player's global sd.play.
    with sd.RawOutputStream(samplerate=RATE, channels=1, dtype='int16') as stream:
        for offset in range(0, len(audio), 1200):
            if cancel.is_set():
                stream.abort()
                return
            stream.write(audio[offset:offset + 1200].tobytes())


class DemandSpeaker:
    metered = True
    FAIL_LIMIT, COOL_OFF_S = 2, 300.0

    def __init__(self, cfg=None, *, narrator=None, player=None, local_factory=None):
        self.narrator = narrator or LiveNarrator(cfg)
        self.player = player or _play
        self.local_factory = local_factory or (lambda: Speaker('piper'))
        self.local = None
        self._fails, self._blocked_until = 0, 0.0
        self._condition = threading.Condition()
        self._pending, self._active_text, self._cancel = None, '', None
        self._speaking = threading.Event()
        self.ready, self.error, self.last_end = True, '', 0.0
        self.voice_name = 'GPT-Live 1 (voz de IA, sessoes sob demanda)'
        threading.Thread(target=self._worker, daemon=True, name='live-narration').start()

    @property
    def speaking(self):
        return self._speaking.is_set() or bool(self.local and self.local.speaking)

    chime = staticmethod(Speaker.chime)

    def speak(self, text, purpose='reply'):
        text = clean_for_speech(text)
        # Acknowledgments/progress stay in the UI; existing local earcons acknowledge input.
        if not text or purpose == 'feedback':
            return
        with self._condition:
            if text == self._active_text or (self._pending and self._pending[0] == text):
                return
            if self._cancel:
                self._cancel.set()
            if self.local:
                self.local.stop()
            self._pending = (text, purpose)
            self._condition.notify()

    def stop(self):
        with self._condition:
            self._pending = None
            if self._cancel:
                self._cancel.set()
            if self.local:
                self.local.stop()

    def wait(self, timeout=25.0):
        end = time.monotonic() + timeout
        with self._condition:
            while (self._pending or self._speaking.is_set()) and time.monotonic() < end:
                self._condition.wait(timeout=min(0.05, max(0.001, end - time.monotonic())))
        if self.local:
            self.local.wait(max(0, end - time.monotonic()))

    def _fallback(self, text, cancel):
        # stop() and fallback admission share the lock: cancelled speech cannot resurface.
        with self._condition:
            if cancel.is_set(): return
            if self.local is None:
                self.local = self.local_factory()
            self.local.speak(text)

    def _worker(self):
        while True:
            with self._condition:
                while self._pending is None:
                    self._condition.wait()
                text, purpose = self._pending
                self._pending, self._active_text = None, text
                cancel = self._cancel = threading.Event()
                self._speaking.set()
            try:
                # Duas falhas seguidas: voz local por um tempo, sem abrir sessao paga a cada resposta
                if purpose == 'local' or time.monotonic() < self._blocked_until:
                    self._fallback(text, cancel)
                else:
                    audio = self.narrator.render(text, cancel)
                    if audio is not None and not cancel.is_set():
                        self.player(audio, cancel)
                    self.error, self._fails = '', 0
            except Exception as error:
                # Never include request headers, provider bodies, text or key in diagnostics.
                reason = getattr(error, 'code', None) or type(error).__name__
                self.error = 'GPT-Live indisponivel (' + reason + '); usando voz local.'
                if isinstance(error, ModuleNotFoundError):
                    self.error = 'Dependencia de voz ausente: ' + str(error.name) + '. Inicie pelo iniciar.cmd do projeto.'
                logging.getLogger('voice').warning(self.error)
                self._fails += 1
                if self._fails >= self.FAIL_LIMIT:
                    self._blocked_until = time.monotonic() + self.COOL_OFF_S
                if self._fails == 1:          # avisa uma vez, nao a cada resposta
                    from desktop.event_bus import bus
                    bus.emit('voice_reply', {'text': 'A resposta usara voz local: GPT-Live indisponivel (' + reason + ').'})
                self._fallback(text, cancel)
            finally:
                with self._condition:
                    self.last_end = time.time()
                    self._active_text, self._cancel = '', None
                    self._speaking.clear()
                    self._condition.notify_all()
