"""
Conversa em tempo real com GPT-Live (modo Conversa).

O microfone vai direto para o GPT-Live, que ouve e fala ao mesmo tempo. As tarefas continuam
com o app: cada fala transcrita passa pelo entendimento local e pelo Maestro; o evento de
delegacao e so um sinal extra, porque o modelo as vezes diz que vai agir sem delegar. O modelo
nao tem ferramentas e so recebe resultados ja verificados.

A sessao e cobrada enquanto esta aberta, entao so existe enquanto ha conversa: fecha sem
atividade e reabre quando a deteccao local percebe fala ou quando ha resultado para contar.
Enquanto o agente fala, o microfone manda silencio (a caixa de som nao interrompe o proprio
agente), exceto se a pessoa falar por cima de verdade: a voz tem de passar bem do eco esperado
para o volume que esta tocando agora.
"""

from __future__ import annotations

import base64
import collections
import json
import logging
import os
import re
import threading
import time
import uuid
from pathlib import Path
from typing import Callable, Optional

import numpy as np

from core.voice.live import DELEGATION, MODEL, RATE, LiveConfig, LiveError, VoiceBudget, _connect, _words, provider_code
from core.voice.recorder import BARGE_BLOCKS, BARGE_MIN, is_speech
from core.voice.tts import clean_for_speech

log = logging.getLogger("voice")
STATS_PATH = Path(__file__).resolve().parents[2] / "memory" / "voice_conversation.jsonl"

BLOCK = 720                   # 30 ms a 24 kHz
RESERVE_S = 60.0              # a reserva cresce em fatias enquanto a sessao esta aberta
SEND_FRAMES = 2               # 60 ms por evento de audio
WAKE_BLOCKS = 5               # ~150 ms de fala reabrem a sessao
VOICE_PEAK = 200              # abaixo disso o chunk de saida e silencio
PREBUFFER_S = 0.2             # guarda antes de tocar: atraso de rede nao vira corte na fala
REBUFFER_S = 0.12
START_ANYWAY_S = 0.3          # frase curta nunca chega ao prebuffer: toca assim mesmo
SPEECH_GAP_S = 0.6            # silencio ate aqui ainda e pausa dentro da fala
SPEAKING_TAIL_S = 0.5         # o som ainda sai do fone/caixa depois do ultimo chunk
OUTPUT_BLOCK = 960            # 40 ms
ECHO_LEARN = 20               # ~600 ms ouvindo o proprio agente antes de aceitar interrupcao
ECHO_MARGIN = 3.0             # quantas vezes acima do eco esperado para ser voz da pessoa
BARGE_HOLD = 6                # brecha entre silabas (~180 ms) nao zera a interrupcao
CUT_BLOCKS = 24               # ~720 ms de voz por cima: cala de vez
HEADPHONE_CUT_BLOCKS = 13     # no fone o microfone so ouve a pessoa: ~400 ms bastam ("uhum" e mais curto)
HEADPHONE_HOLD = 12           # a virgula de "espera, para um pouco" nao zera a contagem
ECHO_FLOOR_RATIO = 2.5        # com o agente falando, o microfone so passa disso se ouvir a caixa de som
ECHO_AUDIBLE_MIN = 0.006
# Decidem so quando o app le a fala para ver se e tarefa. Quando falar e decisao do modelo.
USER_PAUSE_S = 0.6            # sem transcricao por esse tempo
USER_PAUSE_DELEGATED_S = 0.25 # o modelo ja entendeu como pedido
USER_PAUSE_OPEN_S = 1.6       # terminou em "mouse em": a frase provavelmente continua
USER_PAUSE_MAX_S = 3.0        # microfone ruidoso nao segura o pedido para sempre
LOCAL_QUIET_S = 1.1           # o fim da transcricao chega ~1 s depois do fim da fala: antes disso a frase sai em pedacos
LOCAL_QUIET_DELEGATED_S = 0.3
AGENT_PAUSE_S = 1.2
AGENT_PAUSE_MAX_S = 6.0
OUTBOX_MAX = 16
_LEADING_NOISE = " .,;:…-–—"     # a transcricao comeca com "... " quando pega a frase andando
_OPEN_ENDING = re.compile(r"(?:^|\s)(?:em|no|na|nos|nas|de|do|da|dos|das|o|a|os|as|um|uma|que|e|ou|mas|para|pra|"
                          r"com|por|pelo|pela|esse|essa|este|esta|meu|minha|seu|sua)[\s.,…]*$", re.I)


def _instructions(extra: str = "") -> str:
    """Modelo oficial de prompt do GPT-Live: comportamento, sem roteiro. Quem decide a hora de falar e
    o modelo, que ouve o audio; o procedimento das tarefas e as permissoes ficam no app."""
    now = time.strftime("%d/%m/%Y %H:%M")
    return ("Voce e a voz do AI Farm Agent, assistente que opera este computador Windows. "
            "Fale portugues do Brasil, de forma curta e natural. "
            "Voce nao ve a tela nem o mouse; quem age no computador e o sistema.\n"
            "Backchannel policy: Use few, brief backchannels while the user is speaking.\n"
            "Interruption policy: When the user interrupts, stop speaking right away, even in the middle of a "
            "sentence. Listen to what they say. Respond to the user's latest request. "
            "Don't resume an answer they've replaced.\n"
            "Pacing: Keep listening while the user pauses to think. Do not fill a hesitation or finish their "
            "sentence. Do not treat a cough, music, or nearby conversation as a new request.\n"
            "Delegation policy: Generate <|SpawnThinking|> before answering when the user asks for any action on "
            "the computer, in files, in the browser or in spreadsheets, or for current information from the "
            "internet. Do not generate <|SpawnThinking|> for greetings or small talk.\n"
            "Say only something brief like \"deixa comigo\" and do not guess the result while waiting. Never say "
            "something was done, opened or clicked before the system's result arrives. When it arrives, report "
            "it faithfully, without changing names or numbers. Keep talking normally while a task runs.\n"
            f"Agora: {now}." + (f"\n{extra}" if extra else ""))


class _Mic:
    """Microfone padrao em PCM16 mono 24 kHz."""

    def __enter__(self):
        import sounddevice as sd
        self.stream = sd.RawInputStream(samplerate=RATE, channels=1, dtype="int16", blocksize=BLOCK)
        self.stream.start()
        return self

    def read(self) -> bytes:
        data, _ = self.stream.read(BLOCK)
        return bytes(data)

    def __exit__(self, *exc):
        self.stream.stop()
        self.stream.close()


class PlaybackBuffer:
    """Fila entre a rede e a saida de som. Guarda um pouco antes de tocar, para atraso de rede
    nao virar corte, e guarda o trecho anterior a voz, para nao engolir o inicio da fala."""

    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._lock = threading.Lock()
        self._data = bytearray()
        self._onset = b""
        self._primed = False
        self._need = int(PREBUFFER_S * RATE) * 2
        self._waiting_since: Optional[float] = None
        self._last_voice = float("-inf")
        self._levels: collections.deque = collections.deque(maxlen=20)
        self.underruns = 0

    @property
    def speaking(self) -> bool:
        return bool(self._data) or self._clock() < self._last_voice + SPEAKING_TAIL_S

    def feed(self, raw: bytes) -> None:
        now = self._clock()
        with self._lock:
            in_speech = bool(self._data) or now < self._last_voice + SPEECH_GAP_S
            if _has_voice(raw):
                if not in_speech:
                    self._data += self._onset
                    self._waiting_since = now
                self._onset = b""
                self._last_voice = now
                self._data += raw
            elif in_speech:
                self._data += raw
            else:
                self._onset = raw         # silencio fora da fala nao acumula atraso

    def pull(self, size: int) -> bytes:
        """Chamado pela saida de som. Sem dado devolve silencio, e a saida nunca para."""
        now = self._clock()
        with self._lock:
            if not self._primed:
                late = self._waiting_since is not None and now - self._waiting_since >= START_ANYWAY_S
                if self._data and (len(self._data) >= self._need or late):
                    self._primed, self._waiting_since = True, None
                else:
                    self._levels.append((now, 0.0))
                    return bytes(size)
            out = bytes(self._data[:size])
            del self._data[:size]
            if len(out) < size:
                self._primed = False
                if now < self._last_voice + SPEECH_GAP_S:    # faltou audio no meio da fala
                    self.underruns += 1
                    self._need, self._waiting_since = int(REBUFFER_S * RATE) * 2, now
                else:
                    self._need = int(PREBUFFER_S * RATE) * 2
            samples = np.frombuffer(out[:len(out) // 2 * 2], dtype="<i2").astype(np.float32) / 32768.0
            rms = float(np.sqrt(np.mean(samples * samples))) if samples.size else 0.0
            self._levels.append((now, rms))
            return out + bytes(size - len(out))

    def level(self) -> float:
        """Volume mais alto tocado no ultimo ~0,6 s: o som leva um tempo ate voltar pelo microfone."""
        now = self._clock()
        with self._lock:
            return max((rms for at, rms in self._levels if now - at <= 0.6), default=0.0)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()
            self._onset, self._primed, self._waiting_since = b"", False, None
            self._last_voice = float("-inf")
            self._need = int(PREBUFFER_S * RATE) * 2


class _Player:
    """Saida de som continua: tambem toca silencio, porque fone Bluetooth adormece sem audio
    e corta o inicio da fala seguinte. A folga de latencia absorve o Python ocupado."""

    def __init__(self):
        self.buffer = PlaybackBuffer()
        self.stream = None
        threading.Thread(target=self._open, daemon=True, name="live-player").start()

    def _open(self) -> None:
        try:
            import sounddevice as sd
            def fill(outdata, frames, time_info, status):
                outdata[:] = self.buffer.pull(len(outdata))
            self.stream = sd.RawOutputStream(samplerate=RATE, channels=1, dtype="int16", latency="high",
                                             blocksize=OUTPUT_BLOCK, callback=fill)
            self.stream.start()
        except Exception as error:
            log.warning("saida de som da conversa: %s", type(error).__name__)

    @property
    def speaking(self) -> bool:
        # Sem saida de som nao pode parecer "falando" para sempre e calar o microfone
        return self.stream is not None and self.buffer.speaking

    @property
    def underruns(self) -> int:
        return self.buffer.underruns

    def feed(self, raw: bytes) -> None:
        self.buffer.feed(raw)

    def level(self) -> float:
        return self.buffer.level()

    def clear(self) -> None:
        self.buffer.clear()

    def close(self) -> None:
        stream, self.stream = self.stream, None
        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass


def _has_voice(raw: bytes) -> bool:
    samples = np.frombuffer(raw[:len(raw) // 2 * 2], dtype="<i2")
    return bool(samples.size and np.abs(samples.astype(np.int32)).max() >= VOICE_PEAK)


def open_ending(text: str) -> bool:
    """A frase termina em palavra que pede continuacao ("com o mouse em")."""
    return bool(_OPEN_ENDING.search(text or ""))


def same_message(spoken: str, sent: str) -> bool:
    """O modelo pode parafrasear: basta a maior parte das palavras do que foi enviado."""
    said, wanted = set(_words(spoken)), set(_words(sent))
    return bool(wanted) and len(said & wanted) / len(wanted) >= 0.5


class LiveConversation:
    """Uma conversa do inicio ao fim; pode abrir varias sessoes pagas curtas. Uso unico."""

    def __init__(self, cfg: Optional[dict] = None, *, budget=None, connect=None, mic=None, player=None,
                 barge_in: bool = True, stats_path: Optional[Path] = None,
                 keep_open: Callable[[], bool] = lambda: False,
                 context: Callable[[], str] = lambda: "",
                 extra_instructions: Callable[[], str] = lambda: "",
                 on_user_turn: Callable[[str], None] = lambda text: None,
                 on_agent_turn: Callable[[str, bool], None] = lambda text, from_result: None,
                 on_delegation: Callable[[str], None] = lambda delegation_id: None,
                 on_state: Callable[[str], None] = lambda state: None,
                 on_level: Callable[[float], None] = lambda level: None,
                 on_failed: Callable[[str], None] = lambda reason: None):
        self.cfg = LiveConfig.from_dict(cfg)
        self.budget = budget or VoiceBudget()
        self._connect = connect or _connect
        self._mic_factory = mic or _Mic
        self.player = player if player is not None else _Player()
        self.barge_in = barge_in
        self._stats_path = stats_path or STATS_PATH
        self._keep_open = keep_open
        self._session_thread: Optional[threading.Thread] = None
        self.last_turn: dict = {}     # tempos da ultima fala (para medir, sem texto)
        self._agent_voice_at: Optional[float] = None
        self._awaiting_voice = False
        self._context, self._extra = context, extra_instructions
        self._on_user_turn, self._on_agent_turn = on_user_turn, on_agent_turn
        self._on_delegation, self._on_state, self._on_level = on_delegation, on_state, on_level
        self._on_failed = on_failed
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._outbox: collections.deque = collections.deque(maxlen=OUTBOX_MAX)
        self._backlog: collections.deque = collections.deque(maxlen=int(8 * RATE / BLOCK))
        self._preroll: collections.deque = collections.deque(maxlen=20)
        self._open = False            # sessao abrindo ou aberta: o audio vai para o backlog
        self._greeting = ""
        self._state = ""
        self._results_sent: list = [] # resultados enviados cuja fala ainda nao foi transcrita
        self.last_usage: Optional[dict] = None
        self._user_at_local = float("-inf")   # ultima voz percebida pelo microfone
        self._delegated = False
        # Eco e interrupcao
        self._noise: list = []
        self._vad_run = 0
        self._echo_ratios: list = []
        self._echo_levels: list = []
        self._mic_peak = 0.0
        self._barge_pre: list = []
        self._barge_run = 0
        self._barge_quiet = 0
        self._talking_over = False
        self._barge_until = 0.0
        # O que aconteceu, sem texto: e o que permite investigar um corte depois
        self.stats = {"sessions": 0, "barge_forwarded": 0, "barge_cut": 0, "user_turns": 0, "drops": 0}

    # ── interface para o VoiceController ──────────────────────────
    def start(self, greeting: str = "") -> None:
        self._greeting = greeting
        threading.Thread(target=self._capture, daemon=True, name="live-mic").start()
        self._session_thread = threading.Thread(target=self._run, daemon=True, name="live-session")
        self._session_thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._wake.set()
        self.player.clear()

    def wait_closed(self, timeout: float) -> bool:
        """Espera a sessao paga fechar e confirmar o uso. -> False se nao deu tempo."""
        thread = self._session_thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout)
            return not thread.is_alive()
        return True

    @property
    def agent_voice_at(self) -> Optional[float]:
        return self._agent_voice_at

    @property
    def speaking(self) -> bool:
        return self.player.speaking

    def interrupt(self) -> None:
        """Atalho de calar: descarta o que falta tocar e o que ainda esta chegando desta fala."""
        self.player.clear()
        self._barge_until = time.monotonic() + 1.0

    def say(self, text: str, delegation_id: Optional[str] = None) -> None:
        """Resultado para o agente contar; reabre a sessao se ela fechou por inatividade."""
        text = clean_for_speech(text, 900)
        if text:
            self._outbox.append(("session.commentary.append", text, delegation_id))
            self._wake.set()

    def think(self, text: str, delegation_id: Optional[str] = None) -> None:
        """Contexto silencioso. Sem sessao aberta nao vale reabrir (nem pagar) so por isso."""
        text = (text or "").strip()[:900]
        if text and self._open:
            self._outbox.append(("session.thinking.append", text, delegation_id))

    # ── microfone ─────────────────────────────────────────────────
    def _capture(self) -> None:
        try:
            with self._mic_factory() as mic:
                while not self._stop.is_set():
                    self._on_frame(mic.read())
        except Exception as error:
            if not self._stop.is_set():
                log.warning("microfone da conversa: %s", type(error).__name__)
                self._fail("microfone")

    def _on_frame(self, raw: bytes) -> None:
        samples = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
        rms = float(np.sqrt(np.mean(samples * samples)) + 1e-9) if samples.size else 0.0
        self._on_level(min(1.0, rms * 18))
        self._mic_peak = max(self._mic_peak, rms)
        if not self._open:
            self._listen_for_wake(raw, rms)
        elif self.player.speaking:
            self._backlog.append(self._gate_echo(raw, rms))
        else:
            self._barge_pre, self._barge_run, self._barge_quiet, self._talking_over = [], 0, 0, False
            if is_speech(rms, self._floor()):
                self._user_at_local = time.monotonic()
                if time.monotonic() < self._barge_until:
                    self._barge_until = time.monotonic() + 0.4
            elif len(self._noise) < 30:
                self._noise.append(rms)
            self._backlog.append(raw)

    def _floor(self) -> float:
        return float(np.median(self._noise)) if self._noise else 0.004

    def _listen_for_wake(self, raw: bytes, rms: float) -> None:
        """Sessao fechada: nada sai do computador ate a deteccao local perceber fala."""
        floor = self._floor()
        speech = is_speech(rms, floor)
        if not speech and len(self._noise) < 30:
            self._noise.append(rms)
        self._preroll.append(raw)
        self._vad_run = self._vad_run + 1 if speech else 0
        if self._vad_run >= WAKE_BLOCKS:
            self._vad_run = 0
            self._backlog.extend(self._preroll)
            self._preroll.clear()
            self._open = True
            self._wake.set()

    def _gate_echo(self, raw: bytes, rms: float) -> bytes:
        """Agente falando: manda silencio, salvo voz bem acima do eco esperado para o volume
        que esta tocando. Em dois passos, porque calar por engano corta a fala: primeiro a voz
        chega ao modelo (que para por conta propria); so insistindo o audio local e descartado."""
        played = self.player.level()
        floor = self._floor()
        speech = is_speech(rms, floor)
        learned = len(self._echo_ratios) >= ECHO_LEARN
        if learned and not self._echo_audible(floor):
            # Fone: o microfone nao ouve o agente, entao nao ha o que filtrar. Silenciar aqui so
            # engolia o comeco do que a pessoa dizia. Quem decide parar de falar e o modelo.
            if speech:
                self._user_at_local = time.monotonic()
                self._barge_run += 1
                self._barge_quiet = 0
                # O modelo costuma parar sozinho. Se a pessoa insiste, o que ainda chega nao toca mais
                if self.barge_in and self._barge_run == HEADPHONE_CUT_BLOCKS:
                    self.stats["barge_cut"] += 1
                    self.interrupt()
            else:
                if played > 0.003:
                    self._learn_echo(rms, played)
                self._barge_quiet += 1
                if self._barge_quiet > HEADPHONE_HOLD:
                    self._barge_run = 0
            return raw
        expected = float(np.percentile(self._echo_ratios, 80)) * played if learned else None
        loud = self.barge_in and expected is not None and rms > max(expected * ECHO_MARGIN, floor * 3.0, BARGE_MIN)
        if not loud and played > 0.003:
            self._learn_echo(rms, played)
        if loud:
            self._barge_run += 1
            self._barge_quiet = 0
            self._user_at_local = time.monotonic()
        elif self._barge_run:
            self._barge_quiet += 1
            if self._barge_quiet > BARGE_HOLD:
                self._barge_run, self._talking_over = 0, False
        if not self._talking_over:
            self._barge_pre = (self._barge_pre + [raw])[-BARGE_BLOCKS:]
            if self._barge_run < BARGE_BLOCKS:
                return bytes(len(raw))
            self._talking_over = True
            self.stats["barge_forwarded"] += 1
            self._backlog.extend(self._barge_pre[:-1])
            self._barge_pre = []
            return raw
        if self._barge_run >= CUT_BLOCKS:
            self._barge_run, self._talking_over = 0, False
            self.stats["barge_cut"] += 1
            self.interrupt()
        return raw

    def _learn_echo(self, rms: float, played: float) -> None:
        self._echo_ratios = (self._echo_ratios + [rms / played])[-66:]
        self._echo_levels = (self._echo_levels + [rms])[-66:]

    def _echo_audible(self, floor: float) -> bool:
        return float(np.percentile(self._echo_levels, 80)) > max(floor * ECHO_FLOOR_RATIO, ECHO_AUDIBLE_MIN)

    # ── sessoes ───────────────────────────────────────────────────
    def _run(self) -> None:
        drops = 0
        first = True
        try:
            while not self._stop.is_set():
                if not first:
                    self._wake.wait()
                    if self._stop.is_set():
                        break
                self._wake.clear()
                self._open = True
                self._set_state("thinking" if first else self._state or "listening")
                outcome = self._session(self._greeting if first else "")
                first = False
                self._open = False
                self._backlog.clear()
                self._record_stats(outcome)
                if outcome == "dropped":
                    self.stats["drops"] += 1
                    drops += 1
                    if drops >= 2:
                        self._fail("conexao")
                        return
                else:
                    drops = 0
                self._set_state("listening")
                if self._outbox:
                    self._wake.set()      # resultado chegou enquanto a sessao fechava
        except Exception as error:
            reason = getattr(error, "code", None) or type(error).__name__
            log.warning("GPT-Live indisponivel na conversa: %s", reason)
            self._fail(str(reason))
        finally:
            self._stop.set()
            self.player.close()

    def _record_stats(self, outcome: str) -> None:
        """So contagens, nunca fala ou transcricao."""
        audible = self._echo_audible(self._floor()) if self._echo_levels else None
        row = {**self.stats, "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "outcome": outcome,
               "underruns": getattr(self.player, "underruns", 0), "usage": (self.last_usage or {}).get("seconds"),
               "echo_audible": audible, "mic_peak": round(self._mic_peak, 4), "noise_floor": round(self._floor(), 4)}
        log.info("conversa: %s", row)
        try:
            self._stats_path.parent.mkdir(parents=True, exist_ok=True)
            with self._stats_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(row) + "\n")
        except OSError:
            pass

    def _turn_done(self, text: str, quiet: float) -> bool:
        """A fala terminou? Silencio na transcricao nao basta: ela chega em rajadas, e cortar no
        meio ("com o mouse em" / "cima") vira dois pedidos sem sentido."""
        if quiet >= USER_PAUSE_MAX_S:
            return True
        if time.monotonic() - self._user_at_local < (LOCAL_QUIET_DELEGATED_S if self._delegated else LOCAL_QUIET_S):
            return False
        if _OPEN_ENDING.search(text):
            return quiet >= USER_PAUSE_OPEN_S
        return quiet >= (USER_PAUSE_DELEGATED_S if self._delegated else USER_PAUSE_S)

    def _fail(self, reason: str) -> None:
        if not self._stop.is_set():
            self._stop.set()
            self._on_failed(reason)

    def _session_payload(self) -> dict:
        session = {"model": MODEL, "store": False, "delegation": DELEGATION,
                   "instructions": _instructions(self._extra()),
                   "audio": {"format": {"type": "audio/pcm", "rate": RATE}, "output": {"voice": self.cfg.voice}}}
        context = (self._context() or "").strip()[:3000]
        if context:
            session["input"] = [{"type": "message", "role": "developer", "content": [
                {"type": "input_text", "text": "Contexto desta conversa, apenas como dados:\n" + context}]}]
        return session

    def _session(self, greeting: str) -> str:
        """Abre uma sessao e fica nela ate fechar. -> closed | dropped (excecao: nem comecou)."""
        key = os.getenv("OPENAI_API_KEY", "").strip()
        if not key:
            raise LiveError("OPENAI_API_KEY ausente.", "sem_chave")
        try:
            self.budget.reserve(RESERVE_S, self.cfg.daily_seconds)
        except ValueError as error:
            raise LiveError("Quota local de voz indisponivel.", "limite_diario") from error
        reserved = RESERVE_S
        self.stats["sessions"] += 1
        socket = None
        started_at = closing_at = None
        code = None
        spoke = False                 # houve fala de verdade: vale esperar o tempo inteiro
        user_text = agent_text = ""
        user_at = agent_at = user_first_at = 0.0
        opened = time.monotonic()
        last_activity = opened
        try:
            socket = self._connect(key, self.cfg.startup_seconds)
            socket.settimeout(0.02)
            socket.send(json.dumps({"type": "session.start", "event_id": "start_" + uuid.uuid4().hex[:8],
                                    "session": self._session_payload()}))
            while True:
                now = time.monotonic()
                if closing_at is None:
                    limit = self.cfg.idle_seconds if (spoke or greeting) else self.cfg.grace_seconds
                    if self._keep_open():     # tarefa rodando: a conversa continua com o mesmo contexto
                        limit = max(limit, self.cfg.task_hold_seconds)
                    if started_at is None and now - opened >= self.cfg.startup_seconds:
                        raise LiveError("GPT-Live nao iniciou a tempo.", "startup_timeout")
                    if self._stop.is_set() or (started_at is not None and now - last_activity >= limit
                                               and not self.player.speaking and not self._outbox):
                        socket.send(json.dumps({"type": "session.close"}))
                        closing_at = now
                    elif started_at is not None:
                        # Reserva antes de gastar: sem quota, encerra em vez de passar do limite
                        if now - started_at + 15 > reserved:
                            try:
                                self.budget.extend(RESERVE_S, self.cfg.daily_seconds)
                                reserved += RESERVE_S
                            except ValueError:
                                socket.send(json.dumps({"type": "session.close"}))
                                closing_at = now
                                self._fail("limite_diario")
                        if self._send_pending(socket, greeting):
                            last_activity = now       # tem o que falar: nao fecha antes da fala
                            spoke = True
                        greeting = ""
                elif now - closing_at >= self.cfg.close_seconds + 2:
                    log.warning("GPT-Live nao confirmou o encerramento; reserva mantida como gasta.")
                    return "closed"

                if user_text and self._turn_done(user_text, now - user_at):
                    self.stats["user_turns"] += 1
                    self.last_turn = {"speech_end": self._user_at_local, "first_delta": user_first_at, "flush": now,
                                      "delegated": self._delegated}
                    self._delegated = False
                    self._deliver_turn(user_text)
                    user_text = ""
                if agent_text and (now - agent_at >= AGENT_PAUSE_MAX_S
                                   or (now - agent_at >= AGENT_PAUSE_S and not self.player.speaking)):
                    self._agent_turn(agent_text)
                    agent_text = ""
                if started_at is not None:
                    self._set_state("speaking" if self.player.speaking else "listening")

                try:
                    raw = socket.recv()
                except TimeoutError:
                    continue
                except Exception as error:
                    from websocket import WebSocketConnectionClosedException, WebSocketTimeoutException
                    if isinstance(error, WebSocketTimeoutException):
                        continue
                    if isinstance(error, WebSocketConnectionClosedException) and started_at is not None:
                        break
                    raise
                if not raw:
                    if started_at is not None:
                        break
                    raise LiveError("GPT-Live encerrou antes de iniciar.", code or "encerrada")
                event = json.loads(raw)
                kind = event.get("type", "")
                if kind == "session.started":
                    started_at = last_activity = time.monotonic()
                elif kind == "session.output_audio.delta":
                    chunk = base64.b64decode(event["delta"])
                    if _has_voice(chunk):
                        last_activity = time.monotonic()
                        if self._awaiting_voice:
                            self._awaiting_voice, self._agent_voice_at = False, last_activity
                    if time.monotonic() >= self._barge_until:
                        self.player.feed(chunk)
                elif kind == "session.output_transcript.delta":
                    agent_text += event.get("delta", "")
                    agent_at = last_activity = time.monotonic()
                elif kind == "session.input_transcript.delta":
                    if not user_text:
                        user_first_at = time.monotonic()
                        self._awaiting_voice, self._agent_voice_at = True, None
                    user_text += event.get("delta", "")
                    user_at = last_activity = time.monotonic()
                    spoke = True
                elif kind == "session.delegation.created":
                    delegation_id = (event.get("delegation") or {}).get("id")
                    if delegation_id:
                        self._delegated = True
                        self._on_delegation(delegation_id)
                elif kind == "session.closed":
                    seconds = (event.get("usage") or {}).get("seconds")
                    self.budget.finish(seconds)
                    self.last_usage = {"seconds": seconds, "reason": event.get("reason", "unknown")}
                    if user_text:
                        self._deliver_turn(user_text)
                    if agent_text:
                        self._agent_turn(agent_text)
                    return "closed"
                elif kind == "error":
                    code, param = provider_code(event)
                    log.warning("GPT-Live recusou o comando: %s %s", code, param)
            # Conexao perdida com a sessao rodando: sem uso final, a reserva fica como gasta
            if user_text:
                self._deliver_turn(user_text)
            if self._stop.is_set():
                return "closed"
            log.warning("GPT-Live perdeu a conexao durante a conversa.")
            return "dropped"
        except Exception as error:
            # Recusa antes de iniciar nunca virou sessao: nao ha o que cobrar
            status = getattr(error, "status_code", None)
            if started_at is None and (code or status in (400, 401, 403, 404, 429)):
                self.budget.finish(0)
            if code and not isinstance(error, LiveError):
                raise LiveError("GPT-Live recusou a sessao.", code) from error
            raise
        finally:
            if socket is not None:
                try:
                    socket.close(timeout=0.1)
                except Exception:
                    pass

    def _deliver_turn(self, text: str) -> None:
        text = text.strip().lstrip(_LEADING_NOISE).strip()
        if text:
            self._on_user_turn(text)

    def _agent_turn(self, text: str) -> None:
        # A fala livre ("ja vou abrir") pode terminar depois de um resultado ser enviado:
        # so e fala do resultado se disser o que foi enviado.
        match = next((sent for sent in self._results_sent if same_message(text, sent)), None)
        if match is not None:
            self._results_sent.remove(match)
        self._on_agent_turn(text.strip(), match is not None)

    def _send_commentary(self, socket, text: str, delegation_id, prefix: str) -> None:
        socket.send(json.dumps({"type": "session.commentary.append", "event_id": "app_" + uuid.uuid4().hex[:8],
                                "delegation_id": delegation_id, "content": prefix + text}))
        self._results_sent = (self._results_sent + [text])[-OUTBOX_MAX:]

    def _send_pending(self, socket, greeting: str) -> bool:
        """-> True se pediu uma fala ao modelo."""
        asked = False
        if greeting:
            self._send_commentary(socket, greeting, None, "Cumprimente a pessoa dizendo: ")
            asked = True
        while self._outbox:
            kind, content, delegation_id = self._outbox.popleft()
            if kind == "session.commentary.append":
                self._send_commentary(socket, content, delegation_id, "Conte a pessoa, fielmente e curto: ")
                asked = True
            else:
                socket.send(json.dumps({"type": kind, "event_id": "app_" + uuid.uuid4().hex[:8],
                                        "delegation_id": delegation_id, "content": content}))
        frames = []
        while self._backlog and len(frames) < SEND_FRAMES:
            frames.append(self._backlog.popleft())
        if frames:
            socket.send(json.dumps({"type": "session.input_audio.append",
                                    "audio": base64.b64encode(b"".join(frames)).decode()}))
        return asked

    def _set_state(self, state: str) -> None:
        if state != self._state:
            self._state = state
            self._on_state(state)
