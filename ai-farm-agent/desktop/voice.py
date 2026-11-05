"""
VoiceController — voz em cima da conversa (Session) do Controller.

Dois jeitos de falar:
- Mensagem de audio (microfone ao lado de Enviar, ou Ctrl+Alt+V): clica, fala,
  envia. Nada corta no silencio.
- Conversa ao vivo (opcao "Conversa"): o microfone fica aberto; cada fala
  (separada por pausas) vira um pedido. O agente responde na hora ("Beleza,
  abrindo o Google") e executa em FILA enquanto voce continua falando.

Com GPT-Live (OPENAI_API_KEY e opcao ligada) a conversa ao vivo vira tempo real: o audio vai para
o provedor, que ouve e fala; as tarefas seguem pelo mesmo entendimento, fila e Maestro. Se o
GPT-Live falhar, a conversa continua com a transcricao e a voz locais.

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
import json
import queue
import re
import threading
import time
from pathlib import Path

from desktop.event_bus import bus

STOP_LISTENING = re.compile(r"\b(?:para|pare|pode parar|parar) de (?:ouvir|escutar)\b|"
                            r"\bdesliga (?:a conversa|o microfone|a voz|o modo voz)\b")


VOICE_LATENCY_PATH = Path(__file__).resolve().parent.parent / "memory" / "voice_latency.jsonl"
REPLY_WINDOW_S = 2.5     # fala sem resposta do modelo por esse tempo: o app responde
DISPATCH_RETRY_S = 1.5   # a tela pode ter recusado o pedido (ainda fechando o anterior): tenta de novo

# O modelo disse que fez ou esta fazendo algo no PC
_CLAIMS_ACTION = re.compile(r"\b(?:deixa comigo|vou (?:abrir|clicar|fazer|fechar|entrar|tentar)|abrindo|clicando|cliquei|abri|fechei|"
                            r"fechando|entrei|pronto|ja abri|ta aberto|esta aberto)\b")

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
        from core.voice.tts import create_speaker
        from core.voice.persona import get_persona
        self.ctrl = controller
        self.persona = get_persona()
        self.progress_s = float(cfg.get("progress_after_s", 12))
        self.combo = cfg.get("hotkey", "ctrl+alt+v")
        self.fallbacks = [self.combo] + [c for c in ("ctrl+alt+v", "ctrl+alt+m", "ctrl+f9") if c != self.combo]
        self.stt = Transcriber(cfg.get("model", "small"), cfg.get("compute_type", "int8"),
                               cfg.get("beam_size", 5))
        self.tts = create_speaker(cfg)
        self.silence_s = float(cfg.get("live_pause_s", 0.8))
        # Conversa em tempo real: o microfone vai para o GPT-Live so com esta opcao ligada
        self.live_conversation = bool(cfg.get("live_conversation", True))
        self.live_cfg = cfg.get("live", {}) or {}
        self.conv = None
        self._conv_blocked_until = 0.0
        self._conv_turn_now = None      # fala em analise e a resposta que o modelo ja deu a ela
        self._conv_last_agent = ""      # ultima coisa dita pelo modelo
        self._conv_corrected_at = 0.0
        self._conv_delegation = None    # delegacao aberta pelo modelo, a espera da tarefa
        self._reply_delegation = None
        self._delegations: dict = {}    # comando -> delegacao do GPT-Live que espera o resultado
        self._turns_q: "queue.Queue[tuple]" = queue.Queue()
        self._traces: dict = {}         # comando -> tempos da fala que o pediu
        self._reply_trace = None
        # Falar por cima do agente o interrompe (como Siri/Alexa/ChatGPT voz)
        self.barge_in = bool(cfg.get("barge_in", True))
        # Sinal sonoro na hora em que a fala termina (nunca fica mudo enquanto transcreve)
        self.earcon = bool(cfg.get("earcon", True))
        self.state = "idle"
        self.live = False
        self.hotkey = None
        self._rec_stop = threading.Event()
        self._rec_cancel = False
        self._recording = False
        self._live_stop = threading.Event()
        self._audio_q: "queue.Queue[tuple]" = queue.Queue(maxsize=4)
        self._voice_epoch = 0
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
        self._spec = None               # transcricao antecipada da fala em curso
        threading.Thread(target=self._proc_worker, daemon=True, name="voice-proc").start()
        threading.Thread(target=self._turns_worker, daemon=True, name="voice-turns").start()
        for ev, cb in {"error": self._on_error, "answer": self._on_answer, "cancelled": self._on_cancelled,
                       "execution_finished": self._on_done, "phase": self._on_phase,
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
        if self.conv is not None and self.conv.speaking:
            self.conv.interrupt()
            return
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
        self._heard_cue()

    def _heard_cue(self) -> None:
        """"Ouvi": sinal curto na hora (o microfone ignora o proprio sinal)."""
        if self.earcon and not self.tts.speaking:
            self._mute_until = max(self._mute_until, time.time() + 0.3)
            self.tts.chime()

    def record_cancel(self) -> None:
        self._rec_cancel = True
        self._rec_stop.set()

    def _record_once(self) -> None:
        from core.voice.recorder import record_utterance
        epoch = self._voice_epoch
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
        self._queue_audio(audio, "record", None, epoch)

    def _queue_audio(self, audio, mode, spec, epoch):
        if epoch != self._voice_epoch:
            return
        try:
            self._audio_q.put_nowait((audio, mode, spec, epoch))
        except queue.Full:
            self._say("Estou com pedidos pendentes. Aguarde um instante e repita.")

    # ── conversa ao vivo ──────────────────────────────────────────
    def set_live(self, on: bool) -> None:
        if on == self.live:
            return
        self.live = on
        if on and self._conv_start():
            return
        if on:
            # A saudacao sai primeiro ("Como posso ajudar?"); o microfone ja abre junto
            # e quem falar por cima interrompe (barge-in)
            self._say(self.line("listening_on"), purpose='reply')
            self.stt.preload_async()
            self._live_stop.clear()
            threading.Thread(target=self._live_loop, daemon=True, name="voice-live").start()
        else:
            self._conv_stop()
            self._live_stop.set()
            self._set("idle")

    # ── conversa em tempo real (GPT-Live) ─────────────────────────
    def _conv_start(self) -> bool:
        """-> True se a conversa ficou com o GPT-Live; False segue o caminho local."""
        if not (self.live_conversation and getattr(self.tts, "metered", False)
                and time.monotonic() >= self._conv_blocked_until):
            return False
        from core.voice.live_session import LiveConversation
        self.tts.stop()
        self._conv_delegation, self._conv_turn_now = None, None
        try:
            self.conv = LiveConversation(
                self.live_cfg, barge_in=self.barge_in, context=self._conv_context, extra_instructions=self._conv_extra,
                on_user_turn=self._conv_heard_turn, on_agent_turn=self._conv_agent_turn,
                on_delegation=self._conv_delegated, on_state=self._conv_state, on_level=self._level,
                on_failed=self._conv_failed)
            self.conv.start(self.line("listening_on"))
        except Exception as e:
            self.conv = None
            bus.emit("log", {"level": "WARNING", "agent": "VOZ", "msg": f"GPT-Live indisponível: {type(e).__name__}"})
            return False
        self._set("listening")
        return True

    def _conv_stop(self) -> None:
        conv, self.conv = self.conv, None
        if conv is not None:
            conv.stop()

    def shutdown(self, timeout: float = 3.0) -> None:
        """App fechando: microfone e voz param, e a sessao paga fecha confirmando o uso."""
        self.live = False
        conv, self.conv = self.conv, None
        self._live_stop.set()
        self._rec_cancel = True
        self._rec_stop.set()
        self._cmd_q.clear()
        self.tts.stop()
        if self.hotkey is not None:
            self.hotkey.stop()
        if conv is not None:
            conv.stop()
            conv.wait_closed(timeout)

    def _conv_heard_turn(self, text: str) -> None:
        conv = self.conv
        self._turns_q.put((text, dict(conv.last_turn) if conv is not None else {}))

    def _conv_failed(self, reason: str) -> None:
        """Sem GPT-Live a conversa nao para: volta para a transcricao e a voz locais."""
        self.conv = None
        self._conv_blocked_until = time.monotonic() + 300
        bus.emit("log", {"level": "WARNING", "agent": "VOZ", "msg": f"GPT-Live indisponível na conversa: {reason}"})
        if not self.live:
            return
        bus.emit("voice_reply", {"text": f"Conversa em tempo real indisponível ({reason}). Continuo com a voz local."})
        self.stt.preload_async()
        self._live_stop.clear()
        threading.Thread(target=self._live_loop, daemon=True, name="voice-live").start()

    def _conv_context(self) -> str:
        session = self.ctrl.session
        return "" if session is None or session.empty else session.context_block(2600)

    @staticmethod
    def _conv_extra() -> str:
        extra = ""
        try:
            from core.obsidian_vaults import known_vaults
            from core.user_settings import instructions_block
            vaults = known_vaults()
            if vaults:
                extra = "Estes nomes sao cofres do Obsidian, nao redes nem outra coisa: " + ", ".join(vaults) + "."
            return "\n".join(part for part in (extra, instructions_block()) if part)
        except Exception:
            return extra

    def _conv_state(self, state: str) -> None:
        if self.live:
            self._set(state)

    def _conv_delegated(self, delegation_id: str) -> None:
        self._conv_delegation = delegation_id
        # A delegacao costuma chegar depois de o app ja ter ficado em duvida sobre a mesma fala
        if self._pending_guess:
            self._conv_run_guess()

    def _conv_run_guess(self) -> None:
        """O app tinha um palpite e o modelo tratou a fala como pedido: dois sinais independentes
        concordam. Sem isto ele dizia "deixa comigo" e nada acontecia."""
        guess, self._pending_guess = self._pending_guess, ""
        self._delegations[guess], self._conv_delegation = self._conv_delegation, None
        self._enqueue(guess, guess)
        conv = self.conv
        if conv is not None:
            conv.think("Tarefa iniciada, ainda sem resultado: " + _short(guess), self._delegations.get(guess))

    def _conv_agent_turn(self, text: str, from_result: bool) -> None:
        """Mostra o que o agente falou. Resultado de tarefa ja aparece pelo controller. A resposta
        pode chegar antes de o app decidir o que a fala era: nesse caso espera a decisao."""
        if from_result or not text:
            return
        self._recent = (self._recent + [text])[-6:]
        self._conv_last_agent = text
        turn = self._conv_turn_now
        if turn is None:
            bus.emit("voice_reply", {"text": text})
        else:
            turn["reply"] = f"{turn['reply']} {text}".strip()
            if turn["kind"] is not None:
                self._conv_close_turn()

    def _conv_decided(self, kind: str) -> None:
        turn = self._conv_turn_now
        if turn is not None:
            turn["kind"] = kind
            if turn["reply"] or kind == "command":
                self._conv_close_turn()

    def _conv_close_turn(self) -> None:
        turn, self._conv_turn_now = self._conv_turn_now, None
        heard, reply = turn["heard"], turn["reply"]
        if turn["kind"] != "command" and self._pending_guess and _CLAIMS_ACTION.search(_norm(reply)):
            turn["kind"] = "command"
            self._conv_run_guess()
        if turn["kind"] == "command":
            if reply:
                bus.emit("voice_reply", {"text": reply})
            return
        if not reply:
            return
        bus.emit("voice_chat", {"heard": heard, "reply": reply, "kind": "chat"})
        claimed = bool(_CLAIMS_ACTION.search(_norm(reply)))
        try:
            self.ctrl.session.add_turn(heard, heard, "chat", [], True, "")
            # Promessa do modelo sem tarefa nao entra no contexto: viraria "fato" no proximo pedido
            if not claimed:
                self.ctrl.session.set_last_reply(reply)
            self.ctrl.session.save()
        except Exception:
            pass
        busy = self._inflight or self.ctrl.state.get("running")
        if claimed and not busy and self.conv is not None and time.monotonic() - self._conv_corrected_at > 20:
            # O modelo disse que ia agir, mas nada foi pedido ao PC: a pessoa precisa saber
            self._conv_corrected_at = time.monotonic()
            self._say("Na verdade, ainda não fiz nada no computador. O que você quer que eu faça?", purpose='reply')

    def _conv_ensure_reply(self, turn: dict, conv, text: str) -> None:
        """Toda fala tem resposta: o modelo as vezes fica calado, e ai o app responde."""
        if self.conv is not conv or conv is None or turn["reply"] or conv.speaking or self._conv_turn_now is not turn:
            return
        self._conv_turn_now = None
        text = text or "Não entendi. Pode repetir?"
        bus.emit("voice_chat", {"heard": turn["heard"], "reply": text, "kind": "chat"})
        conv.say(text)

    def _record_latency(self, trace: dict, **fields) -> None:
        """So tempos, sem fala nem transcricao. Ver scripts/latency_report.py --voice."""
        start = trace.get("speech_end")
        first = trace.get("first_delta")
        # Voz baixa demais para a deteccao local: conta a partir da transcricao
        if start is None or (first and first - start > 5):
            start = first
        if not start or start == float("-inf"):
            return
        row = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "delegated": bool(trace.get("delegated")), **fields}
        for stage in ("first_delta", "flush", "understood", "dispatched", "started", "finished", "agent_voice"):
            if trace.get(stage):
                row[stage + "_s"] = round(trace[stage] - start, 2)
        try:
            with VOICE_LATENCY_PATH.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(row) + "\n")
        except OSError:
            pass

    def _turns_worker(self) -> None:
        while True:
            heard, trace = self._turns_q.get()
            try:
                if self.conv is not None:
                    self._conv_turn(heard, trace=trace)
            except Exception as e:
                self._conv_decided("chat")
                bus.emit("log", {"level": "ERROR", "agent": "VOZ", "msg": f"falha ao processar fala: {e}"})

    def _conv_turn(self, heard: str, understand_fn=None, trace=None) -> dict:
        """O app decide o que vira tarefa, com a mesma regra da conversa local: o modelo responde
        por conta propria e pode nao delegar, ou delegar uma fala que nao e pedido."""
        from core.voice.live_session import same_message
        from core.voice.understand import confirms, understand, yes_no
        heard = (heard or "").strip()
        bus.emit("voice_heard", {"text": heard, "confidence": 1.0, "mode": "live"})
        self._conv_turn_now = {"heard": heard, "kind": None, "reply": ""}
        if STOP_LISTENING.search(_norm(heard)):
            self.set_live(False)
            return {"kind": "stop_listening"}
        if self._pending_guess:
            guess, self._pending_guess = self._pending_guess, ""
            # O "sim" vale para o que a pessoa OUVIU: o modelo fala livre e pode nao ter perguntado
            if confirms(heard) and same_message(self._conv_last_agent, guess):
                self._delegations[guess], self._conv_delegation = self._conv_delegation, None
                self._conv_decided("command")
                self._enqueue(guess, heard)
                return {"kind": "command", "command": guess}
            if yes_no(heard) is False:
                self._conv_decided("chat")
                return {"kind": "chat"}
        session = self.ctrl.session
        epoch = self._voice_epoch
        ctx = "" if session is None or session.empty else session.context_block(2600)
        if understand_fn is None:
            u = understand(heard, 1.0, ctx, self._recent, session=session, mode="live")
        else:
            u = understand_fn(heard, 1.0, ctx, self._recent)
        if epoch != self._voice_epoch:
            self._conv_decided("noise")
            return {"kind": "noise", "reason": "cancelled_generation"}
        kind = u["kind"]
        conv = self.conv
        trace = trace if trace is not None else {}
        trace["understood"] = time.monotonic()
        trace["kind"], trace["via"] = kind, u.get("via", "")
        if kind == "unclear" and u.get("guess") and self._conv_delegation:
            # A fala chegou cortada, mas o modelo a tratou como pedido e o app tem um palpite
            kind = "command"
            u = {**u, "kind": kind, "command": u["guess"]}
        delegation, self._conv_delegation = self._conv_delegation, None
        bus.emit("voice_understood", {"heard": heard, **u})
        turn = self._conv_turn_now
        self._conv_decided(kind)
        if kind in ("chat", "answer", "unclear") and conv is not None and turn is not None:
            self._later(REPLY_WINDOW_S, lambda: self._conv_ensure_reply(turn, conv, u.get("reply", "")))
        if kind != "command":
            if conv is not None:
                trace["agent_voice"] = conv.agent_voice_at
            self._record_latency(trace, kind=trace["kind"], via=trace["via"])
        if kind == "stop":
            self._voice_epoch += 1
            self._cmd_q.clear()
            if self.ctrl.state.get("running"):
                self.ctrl.force_stop()
        elif kind == "command":
            if u.get("via") in ("llm", "rapido") and hasattr(self.ctrl, "voice_hint"):
                self.ctrl.voice_hint(u["command"], {"kind": "continue" if u.get("target") else "new",
                                                    "target": u.get("target") or ""})
            self._delegations[u["command"]] = delegation
            self._traces[u["command"]] = trace
            busy = self._inflight or self.ctrl.state.get("running")
            self._enqueue(u["command"], heard)
            if conv is not None:
                state = "Na fila, ainda nao comecou: " if busy else "Tarefa iniciada, ainda sem resultado: "
                conv.think(state + _short(u["command"]), delegation)
        elif conv is not None:
            # Nada sera executado: o modelo nao pode dar a entender o contrario
            if kind == "unclear" and u.get("guess"):
                self._pending_guess = u["guess"]
                conv.think("Nada foi executado. Pergunte se a pessoa quer isto: " + u["guess"] + ".", delegation)
            elif kind == "unclear":
                conv.think("Nada foi executado. Diga a pessoa: " + u.get("reply", ""), delegation)
            elif kind == "answer" and u.get("via") == "local":
                conv.think("Dado verificado pelo sistema: " + u.get("reply", ""), delegation)
            elif delegation:
                conv.think("Nada foi executado para esta fala. Peca a pessoa para dizer o que deseja fazer.", delegation)
        return u

    def _barge(self) -> None:
        """A pessoa comecou a falar por cima: o agente se cala na hora e escuta."""
        self.tts.stop()
        self._mute_until = 0.0
        self._set("listening")
        bus.emit("log", {"level": "INFO", "agent": "VOZ", "msg": "Interrompido pela fala do usuário"})

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
                self._spec = None
                epoch = self._voice_epoch
                audio = record_utterance(self._live_stop, on_level=self._level, start_timeout=None,
                                         silence_s=self.silence_s, paused=self._paused,
                                         on_barge=self._barge if self.barge_in else None,
                                         on_pause=self._spec_start)
            except Exception as e:
                self.live = False
                self._set("idle", error=f"microfone: {e}")
                self._say(self.line("mic_error"))
                return
            if not self.live:
                break
            if audio is not None:
                self._heard_cue()
                self._queue_audio(audio, "live", self._spec, epoch)
            self._spec = None
        self._set("idle")

    def _spec_start(self, audio) -> None:
        """Pausa na fala: ja transcreve o que foi dito enquanto o microfone confirma o fim.
        Uma de cada vez; se a pessoa continuar falando, o resultado e descartado."""
        cur = self._spec
        if cur is not None and not cur["done"].is_set():
            return
        spec = {"n": len(audio), "done": threading.Event(), "result": None}
        self._spec = spec

        def run():
            try:
                spec["result"] = self.stt.transcribe(audio)
            except Exception as e:
                spec["result"] = {"error": str(e)}
            finally:
                spec["done"].set()
        threading.Thread(target=run, daemon=True, name="stt-antecipada").start()

    # ── processar cada fala, na ordem ─────────────────────────────
    def _proc_worker(self) -> None:
        while True:
            item = self._audio_q.get()
            audio, mode = item[0], item[1]
            spec = item[2] if len(item) > 2 else None
            epoch = item[3] if len(item) > 3 else self._voice_epoch
            if epoch != self._voice_epoch:
                continue
            try:
                self._set("thinking")
                r = None
                # A transcricao antecipada vale se depois da pausa so veio silencio
                tail = len(audio) - spec["n"] if spec else -1
                if spec and 0 <= tail <= int((self.silence_s + 0.15) * 16000):
                    if spec["done"].wait(15) and spec["result"] and not spec["result"].get("error"):
                        r = spec["result"]
                if r is None:
                    r = self.stt.transcribe(audio)
                if r.get("error"):
                    self._say(self.line("stt_error"))
                    continue
                if epoch != self._voice_epoch:
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
        from core.voice.understand import confirms, understand, yes_no
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
            if confirms(heard):
                self._asked = False
                self._enqueue(guess, heard)
                self._say(self.line("ack"))
                return {"kind": "command", "command": guess}
            if yn is False:
                self._say(self.line("retry"))
                return {"kind": "chat"}

        session = self.ctrl.session
        epoch = getattr(self, "_voice_epoch", 0)
        ctx = "" if session is None or session.empty else session.context_block(2600)
        if understand_fn is None:
            u = understand(heard, confidence, ctx, self._recent, session=session, mode=mode)
        else:
            u = understand_fn(heard, confidence, ctx, self._recent)
        if epoch != getattr(self, "_voice_epoch", 0):
            return {"kind": "noise", "reason": "cancelled_generation"}
        kind = u["kind"]
        bus.emit("voice_understood", {"heard": heard, **u})

        if kind == "stop":
            self._voice_epoch = getattr(self, "_voice_epoch", 0) + 1
            self._cmd_q.clear()
            if self.ctrl.state.get("running"):
                self.ctrl.force_stop()
            self._say(u["reply"] or self.line("stopped"))
        elif kind in ("chat", "answer"):
            # Papo ("valeu") ou resposta direta ("são 14:05"): mensagem propria na conversa,
            # nao grudada no pedido anterior; nada e executado no PC
            bus.emit("voice_chat", {"heard": heard, "reply": u["reply"], "kind": kind})
            self._say(u["reply"], show=False, purpose='reply')
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

    @staticmethod
    def _act_on_guess(u: dict, session) -> bool:
        """Pedido classificado como incerto sempre pede esclarecimento antes de agir.

        Ter uma janela aberta nao confirma o alvo ou o efeito de um clique.
        Mantido como ponto de compatibilidade dos clientes de voz.
        """
        return False

    def _unclear(self, question: str) -> bool:
        """Pergunta UMA vez; se continuar sem entender, fica quieto (a fala aparece na tela)."""
        if self._asked:
            return False
        self._asked = True
        self._say(question, purpose='local')
        return True

    # ── fila de pedidos ───────────────────────────────────────────
    def _enqueue(self, command: str, heard: str) -> None:
        with self._qlock:
            if len(self._cmd_q) >= 8:
                self._say("A fila de pedidos está cheia. Aguarde e repita.")
                return
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
        # Subscribe to the reply BEFORE dispatch: deterministic agents can reply
        # before execution_finished (the reply composer runs on another thread).
        self._expect_reply = True
        self._reply_task = (command, heard)
        self._reply_run_id = getattr(self.ctrl, '_run_id', 0) + 1
        self._reply_session_id = getattr(self.ctrl.session, 'id', None)
        self._reply_delegation = self._delegations.pop(command, None)
        self._reply_trace = self._traces.pop(command, None)
        if self._reply_trace is not None:
            self._reply_trace["dispatched"] = time.monotonic()
        bus.emit("voice_command", {"text": command, "heard": heard})

        def progress():
            # Pedido demorado: UM aviso curto, como uma pessoa ao lado ("ainda tô nisso")
            speaking = self.conv.speaking if self.conv is not None else self.tts.speaking
            if self._seq == seq and self._inflight and self._started.get(seq) and not speaking:
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
                self._say(self.line("start_fail"), purpose='local')
            self._dispatch()
        self._later(DISPATCH_RETRY_S, watchdog)

    def _finish(self) -> None:
        self._inflight = False
        self._started.pop(self._seq, None)
        self._later(0.6, self._dispatch)     # deixa o controller liberar o "running"

    # ── falar ─────────────────────────────────────────────────────
    def _say(self, text: str, show: bool = True, purpose: str = 'feedback') -> None:
        text = (text or "").strip()
        if not text:
            return
        self._recent = (self._recent + [text])[-6:]
        if show:
            bus.emit("voice_reply", {"text": text})
        conv = getattr(self, "conv", None)
        if conv is not None:
            # A fala sai pelo GPT-Live, uma voz so. Confirmacao e progresso ele ja disse por conta propria.
            if purpose == 'feedback':
                conv.think(text, self._reply_delegation)
            else:
                conv.say(text, self._reply_delegation)
                self._reply_delegation = None
            return
        if getattr(self.tts, 'metered', False):
            self.tts.speak(text, purpose=purpose)
        else:
            self.tts.speak(text)
        self._mute_until = time.time() + 0.4

    def _on_phase(self, p: dict) -> None:
        if self._inflight:
            self._started[self._seq] = True
            trace = getattr(self, "_reply_trace", None)
            if trace is not None:
                trace.setdefault("started", time.monotonic())
            agent = str((p or {}).get("msg", "")).split(" Agent")[0].strip().upper()
            self._where = _WHERE.get(agent, self._where)

    def _on_error(self, p: dict) -> None:
        if not self._inflight:
            return
        if p.get("kind") in ("clarification", "limitation"):
            self._say(p.get("msg", ""), purpose='local')
        else:
            self._say(self.line("failed", msg=str(p.get("msg", ""))[:120]), purpose='local')

    def _on_answer(self, p: dict) -> None:
        if self._inflight:
            self._say(p.get("msg", ""), purpose='reply')

    def _on_cancelled(self, p: dict) -> None:
        with self._qlock:
            self._expect_reply = False
            self._voice_epoch += 1
            self._cmd_q.clear()
            self._pending_guess = ""
        if self._inflight:
            self._finish()

    def _on_done(self, p: dict) -> None:
        if not self._inflight:
            self._dispatch()
            return
        # A resposta final vem do controller ("assistant_message"); a voz so fala
        # se ela acrescentar algo (a confirmacao ja foi dita na hora).
        trace, self._reply_trace = getattr(self, "_reply_trace", None), None
        if trace is not None:
            conv = getattr(self, "conv", None)
            trace["finished"] = time.monotonic()
            trace["agent_voice"] = conv.agent_voice_at if conv is not None else None
            self._record_latency(trace, kind=trace.get("kind", ""), via=trace.get("via", ""))
        self._finish()

    def _on_assistant(self, p: dict) -> None:
        if not self._expect_reply:
            return
        for key in ('run_id', 'session_id'):
            expected_id = getattr(self, '_reply_' + key, None)
            if p.get(key) is not None and expected_id is not None and p[key] != expected_id:
                return
        expected = getattr(self, '_reply_task', ())
        if p.get('said') and expected and p['said'] not in expected:
            return
        self._expect_reply = False
        if (p.get("speak") or self.live) and p.get("text"):
            self._say(p["text"], purpose='reply')
