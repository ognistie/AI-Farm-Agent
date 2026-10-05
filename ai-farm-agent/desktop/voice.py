"""
VoiceController — voz em cima da conversa (Session) do Controller.

Dois jeitos de falar:
- Mensagem de audio (microfone ao lado de Enviar, ou Ctrl+Alt+V): clica, fala,
  envia. Nada corta no silencio.
- Conversa ao vivo (opcao "Conversa"): o microfone fica aberto; cada fala
  (separada por pausas) vira um pedido. O agente responde na hora ("Beleza,
  abrindo o Google") e executa em FILA enquanto voce continua falando.

Cada fala: transcricao local -> entendimento (dicionario + contexto) ->
  command  -> confirma em voz alta e entra na fila
  unclear  -> pergunta UMA vez com o palpite; "sim" executa o palpite
  chat     -> responde curto
  stop     -> para a execucao e esvazia a fila
  noise    -> ignora em silencio
  answer   -> responde na hora (hora, conta, conhecimento geral), sem usar o PC
No fim de cada pedido so fala de novo se tiver algo a contar (dado lido,
falha) — sem "Pronto." repetido. Pedido demorado ganha UM aviso de progresso
("Ainda tô nisso no navegador, quase lá"). O que o agente diz vem da persona
(core/voice/persona.py, editavel no Obsidian), variando sem repetir.

Estados (evento "voice_state"): off | idle | recording | listening | thinking | speaking
"""

from __future__ import annotations

import collections
import queue
import re
import threading
import time

from desktop.event_bus import bus

STOP_LISTENING = re.compile(r"\b(?:para|pare|pode parar|parar) de (?:ouvir|escutar)\b|"
                            r"\bdesliga (?:a conversa|o microfone|a voz|o modo voz)\b")


_WHERE = {"WEB": " no navegador", "DESKTOP": " no app", "CODE": " no código", "FILE": " nos arquivos",
          "DATA": " na planilha"}


def _norm(s: str) -> str:
    from core.lexicon import norm
    return norm(s)


def _short(command: str) -> str:
    """'abrir o Spotify e tocar lofi' -> fala curta da fila (minuscula, sem ponto final)."""
    c = (command or "").strip().rstrip(".")
    c = c[:1].lower() + c[1:]
    return c if len(c) <= 60 else c[:57].rsplit(" ", 1)[0] + "..."


class VoiceController:
    def __init__(self, controller, cfg: dict | None = None):
        cfg = cfg or {}
        from core.voice.stt import Transcriber
        from core.voice.tts import Speaker
        from core.voice.persona import get_persona
        self.ctrl = controller
        self.persona = get_persona()
        self.progress_s = float(cfg.get("progress_after_s", 12))
        self.combo = cfg.get("hotkey", "ctrl+alt+v")
        self.fallbacks = [self.combo] + [c for c in ("ctrl+alt+v", "ctrl+alt+m", "ctrl+f9") if c != self.combo]
        self.stt = Transcriber(cfg.get("model", "small"), cfg.get("compute_type", "int8"))
        self.tts = Speaker(cfg.get("tts", "piper"), cfg.get("tts_voice", "cadu"), float(cfg.get("tts_rate", 1.05)))
        self.silence_s = float(cfg.get("live_pause_s", 0.8))
        self.state = "idle"
        self.live = False
        self.hotkey = None
        self._rec_stop = threading.Event()
        self._rec_cancel = False
        self._recording = False
        self._live_stop = threading.Event()
        self._audio_q: "queue.Queue[tuple]" = queue.Queue()     # falas em ordem
        self._cmd_q: collections.deque = collections.deque()     # pedidos esperando a vez
        self._inflight = False
        self._expect_reply = False      # o proximo assistant_message e de um pedido falado
        self._qlock = threading.RLock()
        self._seq = 0
        self._started: dict = {}        # seq -> a execucao comecou (phase recebida)
        self._pending_guess = ""        # palpite aguardando "sim"
        self._asked = False             # ja perguntou "nao peguei" desde o ultimo pedido entendido
        self._recent: list[str] = []    # falas recentes do agente (para nao repetir)
        self._last_level = 0.0
        self._mute_until = 0.0
        self._where = ""                # onde o pedido atual esta (para o aviso de progresso)
        threading.Thread(target=self._proc_worker, daemon=True, name="voice-proc").start()
        for ev, cb in {"error": self._on_error, "answer": self._on_answer, "cancelled": self._on_cancelled,
                       "history_changed": self._on_done, "phase": self._on_phase,
                       "assistant_message": self._on_assistant}.items():
            bus.on(ev, cb)

    # ── estado / atalho ───────────────────────────────────────────
    def _set(self, state: str, **extra) -> None:
        self.state = state
        bus.emit("voice_state", {"state": state, "live": self.live, "hotkey": self.combo,
                                 "queued": len(self._cmd_q), **extra})

    def start_hotkey(self) -> bool:
        from core.voice.hotkey import GlobalHotkey
        for combo in self.fallbacks:
            hk = GlobalHotkey(combo, self.hotkey_pressed)
            if hk.start_and_wait():
                self.hotkey, self.combo = hk, combo
                self._set(self.state)
                return True
        return False

    def line(self, situation: str, **fields) -> str:
        return self.persona.pick(situation, self._recent, **fields)

    def hotkey_pressed(self) -> None:
        """Atalho global: com o agente falando na conversa ao vivo, CALA (interromper sem
        esperar); senao liga/desliga a conversa ou grava/envia a mensagem de audio
        (gravar ja cala a fala)."""
        if self.tts.speaking and self.live:
            self.tts.stop()
            return
        if self.live:
            self.set_live(False)
        else:
            self.record_toggle()

    def _level(self, lv: float) -> None:
        now = time.time()
        if now - self._last_level > 0.08:
            self._last_level = now
            bus.emit("voice_level", {"level": round(lv, 2)})

    # ── mensagem de audio ─────────────────────────────────────────
    def record_toggle(self) -> None:
        if self._recording:
            self.record_send()
        else:
            self.record_start()

    def record_start(self) -> None:
        if self._recording or self.live:
            return
        self.stt.preload_async()
        self.tts.stop()
        self._rec_stop.clear()
        self._rec_cancel = False
        self._recording = True
        self._set("recording", started=time.time())
        threading.Thread(target=self._record_once, daemon=True, name="voice-rec").start()

    def record_send(self) -> None:
        self._rec_stop.set()

    def record_cancel(self) -> None:
        self._rec_cancel = True
        self._rec_stop.set()

    def _record_once(self) -> None:
        from core.voice.recorder import record_utterance
        try:
            audio = record_utterance(self._rec_stop, on_level=self._level, manual=True, max_s=90)
        except Exception as e:
            self._recording = False
            self._set("idle", error=f"microfone: {e}")
            self._say(self.line("mic_error"))
            return
        self._recording = False
        if self._rec_cancel or audio is None:
            self._set("idle")
            return
        self._audio_q.put((audio, "record"))

    # ── conversa ao vivo ──────────────────────────────────────────
    def set_live(self, on: bool) -> None:
        if on == self.live:
            return
        self.live = on
        if on:
            self.stt.preload_async()
            self._live_stop.clear()
            threading.Thread(target=self._live_loop, daemon=True, name="voice-live").start()
            self._say(self.line("listening_on"))
        else:
            self._live_stop.set()
            self._set("idle")

    def _paused(self) -> bool:
        """Microfone ignorado enquanto o agente fala e um instante depois (eco da caixa de som)."""
        return (self.tts.speaking or time.time() < self._mute_until
                or time.time() < getattr(self.tts, "last_end", 0) + 0.35)

    def _live_loop(self) -> None:
        from core.voice.recorder import record_utterance
        while self.live:
            if self.state not in ("thinking", "speaking"):
                self._set("listening")
            try:
                audio = record_utterance(self._live_stop, on_level=self._level, start_timeout=None,
                                         silence_s=self.silence_s, paused=self._paused)
            except Exception as e:
                self.live = False
                self._set("idle", error=f"microfone: {e}")
                self._say(self.line("mic_error"))
                return
            if not self.live:
                break
            if audio is not None:
                self._audio_q.put((audio, "live"))
        self._set("idle")

    # ── processar cada fala, na ordem ─────────────────────────────
    def _proc_worker(self) -> None:
        while True:
            audio, mode = self._audio_q.get()
            try:
                self._set("thinking")
                r = self.stt.transcribe(audio)
                if r.get("error"):
                    self._say(self.line("stt_error"))
                    continue
                self.handle_text(r.get("text", ""), r.get("confidence", 1.0), mode)
            except Exception as e:
                bus.emit("log", {"level": "ERROR", "agent": "VOZ", "msg": f"falha ao processar fala: {e}"})
            finally:
                if self.state == "thinking":
                    self._set("listening" if self.live else "idle")

    def handle_text(self, heard: str, confidence: float = 1.0, mode: str = "record",
                    understand_fn=None) -> dict:
        """Decide o que fazer com a fala transcrita (testavel sem microfone)."""
        from core.voice.understand import understand, yes_no
        heard = (heard or "").strip()
        bus.emit("voice_heard", {"text": heard, "confidence": confidence, "mode": mode})
        if not heard:
            if mode == "record":
                self._unclear(self.line("not_heard"))
            return {"kind": "noise"}

        if STOP_LISTENING.search(_norm(heard)):
            self.set_live(False)
            self._say(self.line("listening_off"))
            return {"kind": "stop_listening"}

        if self._pending_guess:
            yn = yes_no(heard)
            guess, self._pending_guess = self._pending_guess, ""
            if yn is True:
                self._asked = False
                self._enqueue(guess, heard)
                self._say(self.line("ack"))
                return {"kind": "command", "command": guess}
            if yn is False:
                self._say(self.line("retry"))
                return {"kind": "chat"}

        session = self.ctrl.session
        ctx = "" if session is None or session.empty else session.context_block(1400)
        if understand_fn is None:
            u = understand(heard, confidence, ctx, self._recent, session=session, mode=mode)
        else:
            u = understand_fn(heard, confidence, ctx, self._recent)
        kind = u["kind"]
        bus.emit("voice_understood", {"heard": heard, **u})

        if kind == "stop":
            self._cmd_q.clear()
            if self.ctrl.state.get("running"):
                self.ctrl.force_stop()
            self._say(u["reply"] or self.line("stopped"))
        elif kind in ("chat", "answer"):
            # Papo ("valeu") ou resposta direta ("são 14:05"): mensagem propria na conversa,
            # nao grudada no pedido anterior; nada e executado no PC
            bus.emit("voice_chat", {"heard": heard, "reply": u["reply"], "kind": kind})
            self._say(u["reply"], show=False)
            try:
                self.ctrl.session.add_turn(heard, heard, "chat" if kind == "chat" else "question", [], True,
                                           u["reply"] if kind == "answer" else "")
                self.ctrl.session.set_last_reply(u["reply"])
                self.ctrl.session.save()
            except Exception:
                pass
        elif kind == "unclear":
            # so guarda o palpite se a pergunta foi FEITA (um "sim" depois nao pode
            # executar algo que o usuario nunca ouviu)
            if self._unclear(u["reply"]):
                self._pending_guess = u.get("guess", "")
        elif kind == "command":
            self._asked = False
            busy = self._inflight or self.ctrl.state.get("running")
            # Entendido junto com a conversa: o controller nao precisa resolver de novo
            if u.get("via") in ("llm", "rapido") and hasattr(self.ctrl, "voice_hint"):
                self.ctrl.voice_hint(u["command"], {"kind": "continue" if u.get("target") else "new",
                                                    "target": u.get("target") or ""})
            # O pedido entra antes da fala: a confirmacao aparece no balao do pedido novo
            self._enqueue(u["command"], heard)
            if busy:
                self._say(self.line("queued", cmd=_short(u["command"])))
            else:
                self._say(u["reply"] or self.line("ack"))
        elif kind == "noise" and mode == "record":
            self._unclear(self.line("not_heard"))
        return u

    def _unclear(self, question: str) -> bool:
        """Pergunta UMA vez; se continuar sem entender, fica quieto (a fala aparece na tela)."""
        if self._asked:
            return False
        self._asked = True
        self._say(question)
        return True

    # ── fila de pedidos ───────────────────────────────────────────
    def _enqueue(self, command: str, heard: str) -> None:
        with self._qlock:
            self._cmd_q.append((command, heard, 0))
        self._dispatch()

    @staticmethod
    def _later(seconds: float, fn) -> None:
        t = threading.Timer(seconds, fn)
        t.daemon = True              # nunca segura o app aberto
        t.start()

    def _dispatch(self) -> None:
        with self._qlock:        # fila mexida pela fala, pelo fim da tarefa e por timers
            if self._inflight or not self._cmd_q or self.ctrl.state.get("running"):
                return
            command, heard, tries = self._cmd_q.popleft()
            self._inflight = True
            self._seq += 1
            seq = self._seq
            self._where = ""
        bus.emit("voice_command", {"text": command, "heard": heard})

        def progress():
            # Pedido demorado: UM aviso curto, como uma pessoa ao lado ("ainda tô nisso")
            if self._seq == seq and self._inflight and self._started.get(seq) and not self.tts.speaking:
                self._say(self.line("working", where=self._where), show=False)
        if self.progress_s > 0:
            self._later(self.progress_s, progress)

        def watchdog():
            # A tela pode ter recusado o pedido (ainda fechando o anterior): tenta de novo
            # ate 2 vezes; depois desiste e avisa, sem travar a fila.
            if self._seq != seq or not self._inflight or self._started.get(seq) \
                    or self.ctrl.state.get("running"):
                return
            self._inflight = False
            if tries < 2:
                self._cmd_q.appendleft((command, heard, tries + 1))
            else:
                self._say(self.line("start_fail"))
            self._dispatch()
        self._later(5.0, watchdog)

    def _finish(self) -> None:
        self._inflight = False
        self._started.pop(self._seq, None)
        self._later(0.6, self._dispatch)     # deixa o controller liberar o "running"

    # ── falar ─────────────────────────────────────────────────────
    def _say(self, text: str, show: bool = True) -> None:
        text = (text or "").strip()
        if not text:
            return
        self._recent = (self._recent + [text])[-6:]
        if show:
            bus.emit("voice_reply", {"text": text})
        self.tts.speak(text)
        self._mute_until = time.time() + 0.4

    def _on_phase(self, p: dict) -> None:
        if self._inflight:
            self._started[self._seq] = True
            agent = str((p or {}).get("msg", "")).split(" Agent")[0].strip().upper()
            self._where = _WHERE.get(agent, self._where)

    def _on_error(self, p: dict) -> None:
        if not self._inflight:
            return
        if p.get("kind") in ("clarification", "limitation"):
            self._say(p.get("msg", ""))
        else:
            self._say(self.line("failed", msg=str(p.get("msg", ""))[:120]))

    def _on_answer(self, p: dict) -> None:
        if self._inflight:
            self._say(p.get("msg", ""))

    def _on_cancelled(self, p: dict) -> None:
        if self._inflight:
            self._finish()

    def _on_done(self, p: dict) -> None:
        if not self._inflight:
            return
        # A resposta final vem do controller ("assistant_message"); a voz so fala
        # se ela acrescentar algo (a confirmacao ja foi dita na hora).
        self._expect_reply = True
        self._finish()

    def _on_assistant(self, p: dict) -> None:
        if not self._expect_reply:
            return
        self._expect_reply = False
        if p.get("speak") and p.get("text"):
            self._say(p["text"])
