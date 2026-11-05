import base64
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.voice.live import Clip, LiveConfig, LiveError, LiveNarrator, VoiceBudget, RATE, faithful
from core.voice.demand import DemandSpeaker
from core.voice.tts import create_speaker


def audio(values):
    return {'type': 'session.output_audio.delta', 'delta': base64.b64encode(np.asarray(values, dtype='<i2').tobytes()).decode()}


class Clock:
    now = 0.0
    def __call__(self): return self.now


class Socket:
    def __init__(self, clock, events, *, final=True, cancel=None):
        self.clock, self.events = clock, list(events)
        self.sent, self.closed, self.final, self.cancel = [], False, final, cancel
    def settimeout(self, value): pass
    def send(self, text):
        event = json.loads(text); self.sent.append(event)
        if event['type'] == 'session.close' and self.final:
            self.events = [{'type': 'session.closed', 'usage': {'seconds': 5}, 'reason': 'close_requested'}]
    def recv(self):
        self.clock.now += 0.1
        if self.events:
            event = self.events.pop(0)
            if self.cancel and event['type'] == 'session.output_audio.delta': self.cancel.set()
            return json.dumps(event)
        if not self.final: return ''
        raise TimeoutError()
    def close(self, **kwargs): self.closed = True


def success_events(text='Terminei a tarefa.'):
    return [{'type': 'session.started'}, audio([1000] * 2400),
            {'type': 'session.output_transcript.delta', 'delta': text}, audio([0] * RATE)]


class LiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.budget = VoiceBudget(Path(self.tmp.name) / 'usage.json')
        self.key = patch.dict(os.environ, {'OPENAI_API_KEY': 'synthetic-unit-key'})
        self.key.start()
    def tearDown(self):
        self.key.stop(); self.tmp.cleanup()
    def narrator(self, events, **kwargs):
        clock = Clock(); socket = Socket(clock, events, **kwargs)
        connect = Mock(return_value=socket)
        obj = LiveNarrator({'session_max_s': 5, 'close_timeout_s': 1}, budget=self.budget, connect=connect, clock=clock)
        return obj, socket, connect

    def test_idle_empty_and_cancelled_never_reserve_or_connect(self):
        obj, socket, connect = self.narrator([])
        self.assertFalse(self.budget.path.exists())
        self.assertIsNone(obj.render('', threading.Event()))
        stop = threading.Event(); stop.set()
        self.assertIsNone(obj.render('Oi', stop))
        connect.assert_not_called(); self.assertFalse(self.budget.path.exists())

    def test_key_and_budget_checked_before_network(self):
        obj, _, connect = self.narrator([])
        with patch.dict(os.environ, {'OPENAI_API_KEY': ''}), self.assertRaises(ValueError):
            obj.render('Oi', threading.Event())
        obj.cfg = LiveConfig(daily_seconds=0)
        with self.assertRaises(ValueError): obj.render('Oi', threading.Event())
        connect.assert_not_called()

    def test_success_uses_exact_model_no_backend_or_microphone_and_closes(self):
        events = success_events()
        events.insert(1, {'type': 'session.usage.updated', 'usage': {'seconds': 2}})
        events.insert(2, {'type': 'session.usage.updated', 'usage': {'seconds': 4}})
        obj, socket, connect = self.narrator(events)
        result = obj.render('Terminei a tarefa.', threading.Event())
        self.assertGreater(len(result), 0)
        session = socket.sent[0]['session']
        self.assertEqual(session['model'], 'gpt-live-1')
        # A API encerra a conexao com `delegation: null`
        self.assertEqual(session['delegation'], {'type': 'client'}); self.assertFalse(session['store'])
        for event in socket.sent:
            if event['type'] == 'session.input_audio.append':
                self.assertFalse(any(base64.b64decode(event['audio'])))
        self.assertIn('session.close', [e['type'] for e in socket.sent])
        self.assertTrue(socket.closed); connect.assert_called_once()
        self.assertEqual(json.loads(self.budget.path.read_text())['seconds'], 5)
        self.assertIsNone(json.loads(self.budget.path.read_text())['pending'])

    def test_transcript_gap_or_incomplete_phrase_cannot_finish_clip(self):
        clip = Clip(); clip.append(audio([1000] * 2400)['delta']); clip.append(audio([0] * RATE)['delta'])
        clip.transcript = 'Terminei'
        self.assertFalse(clip.complete('Terminei a tarefa.'))
        clip.transcript += ' a tarefa.'
        self.assertTrue(clip.complete('Terminei a tarefa.'))

    def test_paraphrase_times_out_and_never_returns_audio_or_retries(self):
        obj, socket, connect = self.narrator(success_events('Fiz algo diferente.'))
        with self.assertRaises(ValueError): obj.render('Terminei a tarefa.', threading.Event())
        connect.assert_called_once(); self.assertTrue(socket.closed)
        self.assertEqual(len([e for e in socket.sent if e['type'] == 'session.close']), 1)

    def test_cancel_closes_and_discards_audio(self):
        stop = threading.Event()
        obj, socket, _ = self.narrator(success_events(), cancel=stop)
        self.assertIsNone(obj.render('Terminei a tarefa.', stop))
        self.assertTrue(socket.closed); self.assertTrue(obj.last_usage['confirmed'])

    def test_clip_does_not_replay_startup_silence(self):
        clip = Clip()
        clip.append(audio([0] * (RATE * 2))['delta'])
        clip.append(audio([1000] * RATE)['delta'])
        clip.append(audio([0] * RATE)['delta'])
        clip.transcript = 'Oi'
        self.assertTrue(clip.complete('Oi'))
        self.assertLessEqual(len(clip.audio()), int(RATE * 1.17))

    def test_missing_final_usage_stays_spent_without_blocking_next_call_even_after_restart(self):
        obj, socket, connect = self.narrator([{'type': 'session.started'}], final=False)
        with self.assertRaises(ValueError): obj.render('Oi', threading.Event())
        self.assertTrue(socket.closed)
        spent = json.loads(self.budget.path.read_text())['seconds']
        self.assertGreater(spent, 0)
        other = VoiceBudget(self.budget.path)
        other.reserve(10, 1000)
        data = json.loads(self.budget.path.read_text())
        self.assertEqual(data['seconds'], spent + 10)
        self.assertEqual(len(data['unconfirmed_sessions']), 1)

    def test_daily_quota_still_limits_sessions_without_final_usage(self):
        self.budget.reserve(60, 100)
        with self.assertRaises(ValueError): self.budget.reserve(60, 100)
        self.assertEqual(json.loads(self.budget.path.read_text())['seconds'], 60)

    def test_extend_grows_reservation_and_finish_replaces_it(self):
        self.budget.reserve(60, 200)
        self.budget.extend(60, 200)
        with self.assertRaises(ValueError): self.budget.extend(100, 200)
        data = json.loads(self.budget.path.read_text())
        self.assertEqual((data['seconds'], data['pending']), (120, 120))
        self.budget.finish(70)
        data = json.loads(self.budget.path.read_text())
        self.assertEqual((data['seconds'], data['pending']), (70, None))

    def test_session_rejected_before_start_exposes_code_and_costs_nothing(self):
        error = {'type': 'error', 'error': {'code': 'invalid_type', 'param': 'session.delegation', 'message': 'sensitive'}}
        obj, socket, _ = self.narrator([error], final=False)
        with self.assertRaises(LiveError) as caught: obj.render('Oi', threading.Event())
        self.assertEqual(caught.exception.code, 'invalid_type')
        self.assertNotIn('sensitive', str(caught.exception))
        data = json.loads(self.budget.path.read_text())
        self.assertEqual((data['seconds'], data['pending']), (0, None))
        self.assertEqual(obj.last_usage['reason'], 'rejected_before_start')

    def test_small_paraphrase_is_played_but_changed_number_is_not(self):
        self.assertTrue(faithful('A planilha tem doze linhas e esta pronta.', 'A planilha tem doze linhas, esta pronta.'))
        self.assertFalse(faithful('O total foi 150 reais.', 'O total foi 130 reais.'))
        self.assertFalse(faithful('Fiz algo diferente.', 'Terminei a tarefa.'))
        self.assertFalse(faithful('', 'Terminei a tarefa.'))

    def test_provider_or_delegation_error_closes_without_backend(self):
        for kind in ('error', 'session.delegation.started'):
            obj, socket, connect = self.narrator([{'type': 'session.started'}, {'type': kind}])
            with self.assertRaises(ValueError): obj.render('Oi', threading.Event())
            connect.assert_called_once(); self.assertTrue(socket.closed)

    def test_invalid_config_and_usage_fail_closed(self):
        with self.assertRaises(ValueError): LiveConfig.from_dict({'session_max_s': float('nan')})
        self.budget.reserve(10, 100)
        self.budget.finish(True)            # uso invalido nao libera a reserva: continua gasta
        self.budget.reserve(10, 100)
        self.assertEqual(json.loads(self.budget.path.read_text())['seconds'], 20)

    def test_rejected_handshake_does_not_block_correcting_the_key(self):
        from websocket import WebSocketBadStatusException
        connect = Mock(side_effect=WebSocketBadStatusException('synthetic rejected key', status_code=401))
        obj = LiveNarrator(budget=self.budget, connect=connect)
        with self.assertRaises(WebSocketBadStatusException): obj.render('Oi', threading.Event())
        data = json.loads(self.budget.path.read_text())
        self.assertEqual(data['seconds'], 0); self.assertIsNone(data['pending'])
        self.assertEqual(obj.last_usage['reason'], 'handshake_rejected')
        self.budget.path.write_text('{broken')
        with self.assertRaises(ValueError): self.budget.reserve(10, 100)


class DemandTests(unittest.TestCase):
    def local(self):
        local = Mock(); local.speaking = False
        return local

    def test_feedback_never_calls_cloud_or_local_synthesizer(self):
        narrator = Mock(); factory = Mock()
        speaker = DemandSpeaker(narrator=narrator, local_factory=factory)
        speaker.speak('Estou trabalhando.', purpose='feedback'); speaker.wait(0.1)
        narrator.render.assert_not_called(); factory.assert_not_called()

    def test_confirmation_is_local_only(self):
        narrator, local = Mock(), self.local()
        speaker = DemandSpeaker(narrator=narrator, local_factory=lambda: local)
        speaker.speak('Confirma?', purpose='local'); speaker.wait(2)
        narrator.render.assert_not_called(); local.speak.assert_called_once_with('Confirma?')

    def test_stop_discards_inflight_and_pending_audio(self):
        entered, release = threading.Event(), threading.Event()
        def render(text, stop):
            entered.set(); release.wait(2)
            return np.ones(4, dtype=np.int16)
        player = Mock()
        speaker = DemandSpeaker(narrator=Mock(render=render), player=player)
        speaker.speak('Primeira'); self.assertTrue(entered.wait(2))
        speaker.speak('Segunda'); speaker.stop(); release.set(); speaker.wait(2)
        player.assert_not_called()

    def test_only_latest_pending_request_is_rendered(self):
        entered, release = threading.Event(), threading.Event(); calls = []
        def render(text, stop):
            calls.append(text)
            if len(calls) == 1: entered.set(); release.wait(2)
            return None if stop.is_set() else np.ones(4, dtype=np.int16)
        player = Mock()
        speaker = DemandSpeaker(narrator=Mock(render=render), player=player)
        speaker.speak('Primeira'); self.assertTrue(entered.wait(2))
        speaker.speak('Segunda'); speaker.speak('Terceira'); release.set(); speaker.wait(2)
        self.assertEqual(calls, ['Primeira', 'Terceira']); player.assert_called_once()

    def test_failure_uses_local_without_leaking_error_or_retrying(self):
        local = self.local(); narrator = Mock()
        narrator.render.side_effect = ValueError('sensitive synthetic-unit-key text')
        speaker = DemandSpeaker(narrator=narrator, local_factory=lambda: local)
        speaker.speak('Resposta'); speaker.wait(2)
        narrator.render.assert_called_once(); local.speak.assert_called_once_with('Resposta')
        self.assertNotIn('synthetic-unit-key', speaker.error)

    def test_repeated_failures_stop_opening_paid_sessions_for_a_while(self):
        local = self.local(); narrator = Mock()
        narrator.render.side_effect = LiveError('falhou', 'invalid_type')
        speaker = DemandSpeaker(narrator=narrator, local_factory=lambda: local)
        with patch('desktop.event_bus.bus') as bus:
            for text in ('Um', 'Dois', 'Tres'):
                speaker.speak(text); speaker.wait(2)
        self.assertEqual(narrator.render.call_count, 2)
        self.assertEqual(local.speak.call_count, 3)
        self.assertIn('invalid_type', speaker.error)
        self.assertEqual(bus.emit.call_count, 1)        # avisa uma vez, nao a cada resposta

    def test_auto_selection_requires_key_but_never_probes_api(self):
        with patch('core.voice.tts.Speaker', return_value='local'), patch('core.voice.demand.DemandSpeaker', return_value='live') as cloud:
            with patch.dict(os.environ, {'OPENAI_API_KEY': ''}):
                self.assertEqual(create_speaker({}), 'local'); cloud.assert_not_called()
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'synthetic-unit-key'}):
                self.assertEqual(create_speaker({}), 'live')


if __name__ == '__main__': unittest.main()
