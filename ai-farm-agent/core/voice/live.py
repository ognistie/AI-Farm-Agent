"""GPT-Live 1 narration with short sessions, synthetic silence and no microphone upload.

Live has no output-audio-done event. Buffer a clip, require matching transcript
and acoustic silence, finalize the session, then play locally. No paid retries.
"""
from __future__ import annotations
import base64
import difflib
import json
import logging
import math
import os
import re
import threading
import time
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

RATE = 24000
URL = 'wss://api.openai.com/v1/live/sessions'
MODEL = 'gpt-live-1'
USAGE_PATH = Path(__file__).resolve().parents[2] / 'memory' / 'voice_usage.json'
_budget_lock = threading.Lock()
# So mode client (ou responses) e aceito pela API: `delegation: null` encerra a conexao.
DELEGATION = {'type': 'client'}
log = logging.getLogger('voice')


class LiveError(ValueError):
    """Live failure. `code` is the provider's error code; never its body, the text or the key."""
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code


def provider_code(event):
    """Provider error code and parameter for diagnostics, nothing else from the event."""
    error = event.get('error') or {}
    return str(error.get('code') or error.get('type') or 'unknown'), str(error.get('param') or '')


def _bounded(value, default, low, high):
    number = float(default if value is None else value)
    if not math.isfinite(number) or not low <= number <= high:
        raise ValueError('Limite de voz fora do intervalo permitido.')
    return number


@dataclass(frozen=True)
class LiveConfig:
    voice: str = 'marin'
    session_seconds: float = 25.0
    startup_seconds: float = 10.0
    close_seconds: float = 3.0
    daily_seconds: float = 1800.0
    idle_seconds: float = 60.0
    grace_seconds: float = 12.0
    task_hold_seconds: float = 120.0

    @classmethod
    def from_dict(cls, cfg):
        cfg = cfg or {}
        voice = cfg.get('voice', 'marin')
        if voice not in ('marin', 'cedar'):
            raise ValueError('Voz Live deve ser marin ou cedar.')
        return cls(voice, _bounded(cfg.get('session_max_s'), 25, 5, 60),
                   _bounded(cfg.get('startup_timeout_s'), 10, 1, 30),
                   _bounded(cfg.get('close_timeout_s'), 3, 1, 15),
                   _bounded(cfg.get('daily_max_s'), 1800, 0, 28800),
                   _bounded(cfg.get('conversation_idle_s'), 60, 0.1, 600),
                   _bounded(cfg.get('wake_grace_s'), 12, 0.1, 60),
                   _bounded(cfg.get('conversation_task_hold_s'), 120, 0, 600))

    @property
    def reservation(self):
        return self.session_seconds + self.startup_seconds + self.close_seconds


class VoiceBudget:
    """Conservative local quota, not a provider invoice limit. Never stores speech/key.

    Missing final usage keeps the reservation counted as spent (no refund), even
    after a crash/restart, without blocking the next session: the daily quota still
    limits the total. The counter resets daily at UTC.
    """
    def __init__(self, path=USAGE_PATH):
        self.path = Path(path)

    def _read(self):
        day = datetime.now(timezone.utc).date().isoformat()
        if not self.path.exists():
            return {'day_utc': day, 'seconds': 0.0, 'pending': None}
        data = json.loads(self.path.read_text(encoding='utf-8'))
        if not isinstance(data, dict) or type(data.get('seconds')) not in (int, float) or not math.isfinite(data['seconds']) or data['seconds'] < 0:
            raise ValueError('Contabilidade de voz invalida; verificar antes de usar a API.')
        if data.get('pending'):
            return data
        return data if data.get('day_utc') == day else {'day_utc': day, 'seconds': 0.0, 'pending': None}

    def _write(self, data):
        from core.atomic_io import replace_file
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix('.tmp')
        tmp.write_text(json.dumps(data), encoding='utf-8')
        replace_file(tmp, self.path)

    def reserve(self, amount, maximum):
        with _budget_lock:
            data = self._settled(self._read())
            if data['seconds'] + amount > maximum:
                raise ValueError('Limite diario local de voz atingido; usando voz local.')
            data['seconds'] += amount
            data['pending'] = amount
            self._write(data)

    def _settled(self, data):
        """A reservation left by an earlier session stays spent; it stops being pending."""
        if data.get('pending'):
            unconfirmed = data.setdefault('unconfirmed_sessions', [])
            unconfirmed.append({'reserved_seconds': data['pending'],
                                'reason': 'No final usage from the provider; retained as spent, not refunded.'})
            del unconfirmed[:-20]
            data['pending'] = None
        today = datetime.now(timezone.utc).date().isoformat()
        return data if data.get('day_utc') == today else {'day_utc': today, 'seconds': 0.0, 'pending': None}

    def extend(self, amount, maximum):
        """Grow the running session's reservation; over the quota raises, nothing changes."""
        with _budget_lock:
            data = self._read()
            if data['seconds'] + amount > maximum:
                raise ValueError('Limite diario local de voz atingido; usando voz local.')
            data['seconds'] += amount
            data['pending'] = (data.get('pending') or 0) + amount
            self._write(data)

    def finish(self, seconds):
        if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
            return
        with _budget_lock:
            data = self._read()
            reserved = data.get('pending')
            if reserved is not None:
                data['seconds'] = max(0, data['seconds'] - reserved) + seconds
                data['pending'] = None
                self._write(data)


def _words(text):
    text = ''.join(c for c in unicodedata.normalize('NFKD', text.casefold()) if not unicodedata.combining(c))
    return re.findall(r'\w+', text)


def faithful(spoken, expected):
    """The model may paraphrase, so words need not be identical, but every number must
    survive (a changed value is a wrong answer) and most of the phrase must be there."""
    said, wanted = _words(spoken), _words(expected)
    if not said or not wanted:
        return False
    if [w for w in wanted if w.isdigit()] != [w for w in said if w.isdigit()]:
        return False
    return difflib.SequenceMatcher(None, said, wanted, autojunk=False).ratio() >= 0.75


class Clip:
    def __init__(self):
        self.data, self.transcript = bytearray(), ''
        self.speech_start = None
        self.speech_end = self.silence_samples = 0

    def append(self, encoded):
        raw = base64.b64decode(encoded, validate=True)
        if len(raw) % 2 or len(self.data) + len(raw) > RATE * 2 * 60:
            raise ValueError('Audio invalido ou acima do limite.')
        offset = len(self.data) // 2
        self.data.extend(raw)
        samples = np.frombuffer(raw, dtype='<i2')
        for begin in range(0, len(samples), 240):
            frame = samples[begin:begin + 240]
            if np.any(np.abs(frame.astype(np.int32)) >= 300):
                if self.speech_start is None:
                    self.speech_start = offset + begin
                self.speech_end = offset + begin + len(frame)
                self.silence_samples = 0
            else:
                self.silence_samples += len(frame)

    def complete(self, expected):
        return bool(self.speech_end and self.silence_samples >= RATE * 0.8 and faithful(self.transcript, expected))

    def audio(self):
        begin = max(0, (self.speech_start or 0) - int(RATE * 0.04))
        end = min(len(self.data) // 2, self.speech_end + int(RATE * 0.12))
        return np.frombuffer(bytes(self.data[begin * 2:end * 2]), dtype='<i2').copy()


def _connect(key, timeout):
    import websocket
    return websocket.create_connection(URL, header={'Authorization': 'Bearer ' + key},
        timeout=timeout, suppress_origin=True, redirect_limit=0)


class LiveNarrator:
    def __init__(self, cfg=None, *, budget=None, connect=None, clock=time.monotonic):
        self.cfg = LiveConfig.from_dict(cfg)
        self.budget, self.connect, self.clock = budget or VoiceBudget(), connect or _connect, clock
        self.last_usage = None

    def render(self, text, cancel):
        """Constructor, empty/cancelled input and idle never open a connection."""
        text = str(text).strip()
        if not text or cancel.is_set(): return None
        if len(text) > 400: raise ValueError('Fala Live excede 400 caracteres.')
        key = os.getenv('OPENAI_API_KEY', '').strip()
        if not key or any(marker in key.upper() for marker in ('COLE_SUA', 'PLACEHOLDER')):
            raise ValueError('OPENAI_API_KEY ausente; configure o .env local.')
        self.budget.reserve(self.cfg.reservation, self.cfg.daily_seconds)
        socket, started, closing, closed = None, False, None, False
        clip, failure, beginning, code = Clip(), None, self.clock(), None
        self.last_usage = {'confirmed': False, 'seconds': None, 'reason': 'incomplete'}
        try:
            socket = self.connect(key, self.cfg.startup_seconds)
            socket.settimeout(0.1)
            if cancel.is_set():
                return None
            instructions = ('Voce e apenas a voz do AI Farm Agent. Fale em portugues do Brasil. '
                'Leia uma unica vez o texto fornecido literalmente, sem saudacao, prefixo ou fatos novos. '
                'Nao use ferramentas nem solicite trabalho ao backend. Apos ler, fique em silencio. '
                'Backchannel policy: Do not produce backchannels. '
                'Interruption policy: Stop if interrupted. '
                'Delegation policy: Never generate <|SpawnThinking|>.')
            # O texto vai so no commentary: repeti-lo em `input` faz o modelo poder ler duas vezes.
            socket.send(json.dumps({'type': 'session.start', 'event_id': 'start', 'session': {
                'model': MODEL, 'store': False, 'delegation': DELEGATION, 'instructions': instructions,
                'input': [{'type': 'message', 'role': 'developer', 'content': [
                    {'type': 'input_text', 'text': 'Aguarde o texto que deve ser lido.'}]}],
                'audio': {'format': {'type': 'audio/pcm', 'rate': RATE}, 'output': {'voice': self.cfg.voice}}}}))
            next_silence = self.clock()
            while True:
                now = self.clock()
                if closing is not None:
                    if now - closing >= self.cfg.close_seconds: break
                elif cancel.is_set() or clip.complete(text) or now - beginning >= self.cfg.session_seconds:
                    failure = 'cancelled' if cancel.is_set() else (None if clip.complete(text) else 'timeout')
                    socket.send(json.dumps({'type': 'session.close'})); closing = now
                elif not started and now - beginning >= self.cfg.startup_seconds:
                    failure = 'startup_timeout'
                    socket.send(json.dumps({'type': 'session.close'})); closing = now
                if started and closing is None and now >= next_silence:
                    # Paced synthetic silence, never audio captured from the microphone.
                    socket.send(json.dumps({'type': 'session.input_audio.append',
                        'audio': base64.b64encode(bytes(RATE // 10 * 2)).decode()}))
                    next_silence = now + 0.1
                try:
                    raw = socket.recv()
                except TimeoutError:
                    continue
                except Exception as error:
                    from websocket import WebSocketTimeoutException
                    if isinstance(error, WebSocketTimeoutException): continue
                    raise
                if not raw: break
                if len(raw) > 1024 * 1024: raise ValueError('Evento Live acima do limite.')
                event = json.loads(raw)
                kind = event.get('type', '')
                if kind == 'session.started' and not started:
                    started = True
                    socket.send(json.dumps({'type': 'session.commentary.append', 'event_id': 'narrate',
                        'delegation_id': None, 'content': 'Leia literalmente, sem acrescentar nada: ' + json.dumps(text, ensure_ascii=False)}))
                elif kind == 'session.output_audio.delta' and closing is None:
                    clip.append(event['delta'])
                elif kind == 'session.output_transcript.delta' and closing is None:
                    clip.transcript += event['delta']
                    if len(clip.transcript) > 2000: raise ValueError('Transcricao Live acima do limite.')
                elif kind == 'session.closed':
                    closed = True
                    seconds = (event.get('usage') or {}).get('seconds')
                    self.budget.finish(seconds)
                    self.last_usage = {'confirmed': type(seconds) in (int, float) and math.isfinite(seconds) and seconds >= 0,
                        'seconds': seconds, 'reason': event.get('reason', 'unknown')}
                    break
                elif kind == 'error' or kind == 'response.event':
                    failure = 'provider_error'
                    if kind == 'error':
                        code, param = provider_code(event)
                        log.warning('GPT-Live recusou o comando: %s %s', code, param)
                    if closing is None:
                        socket.send(json.dumps({'type': 'session.close'})); closing = now
            if cancel.is_set(): return None
            if (failure or not closed or not clip.complete(text) or not self.last_usage['confirmed']
                    or self.last_usage['reason'] != 'close_requested'):
                raise LiveError('Narracao Live nao confirmada; usar voz local sem nova tentativa paga.', code)
            return clip.audio()
        except Exception as error:
            # A rejected handshake or session.start never became a session: nothing to
            # bill, so it must not leave an imaginary paid session in the counter.
            if socket is None and getattr(error, 'status_code', None) in (400, 401, 403, 404, 429):
                self.budget.finish(0)
                self.last_usage = {'confirmed': True, 'seconds': 0, 'reason': 'handshake_rejected'}
            elif code and not started:
                self.budget.finish(0)
                self.last_usage = {'confirmed': True, 'seconds': 0, 'reason': 'rejected_before_start'}
            if code and not isinstance(error, LiveError):
                raise LiveError('GPT-Live recusou a sessao.', code) from error
            raise
        finally:
            if socket is not None:
                try:
                    if not closed and closing is None: socket.send(json.dumps({'type': 'session.close'}))
                    socket.close(timeout=0.1)
                except Exception:
                    pass
