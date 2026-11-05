import base64
import json
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.voice.live import VoiceBudget
from core.voice.live_session import BLOCK, ECHO_LEARN, RESERVE_S, LiveConversation, PlaybackBuffer, RATE, same_message
from desktop.voice import VoiceController


QUIET = bytes(BLOCK * 2)
LOUD = np.full(BLOCK, 12000, dtype='<i2').tobytes()
ECHO = np.full(BLOCK, 1500, dtype='<i2').tobytes()
FAST = {'conversation_idle_s': 0.3, 'wake_grace_s': 0.2, 'close_timeout_s': 1}


def voice_delta(level=9000, samples=2400):
    return {'type': 'session.output_audio.delta',
            'delta': base64.b64encode(np.full(samples, level, dtype='<i2').tobytes()).decode()}


class Mic:
    """Quiet microphone by default; `speak` queues frames, as real speech would arrive."""
    def __init__(self):
        self.frames = []
    def __enter__(self): return self
    def __exit__(self, *exc): pass
    def speak(self, frame, count): self.frames.extend([frame] * count)
    def read(self):
        time.sleep(0.003)
        return self.frames.pop(0) if self.frames else QUIET


class Player:
    def __init__(self):
        self.played, self.speaking, self.cleared, self.volume = [], False, 0, 0.0
    def feed(self, raw): self.played.append(raw)
    def level(self): return self.volume
    def clear(self): self.cleared += 1
    def close(self): pass


class Socket:
    def __init__(self, events, *, usage=7.0, drop=False):
        self.events = list(events)
        self.sent, self.closed = [], False
        self.usage, self.drop = usage, drop
    def settimeout(self, value): pass
    def send(self, text):
        event = json.loads(text)
        self.sent.append(event)
        if event['type'] == 'session.close':
            self.events.append({'type': 'session.closed', 'reason': 'close_requested', 'usage': {'seconds': self.usage}})
    def recv(self):
        if self.events:
            return json.dumps(self.events.pop(0))
        if self.drop:
            return ''
        time.sleep(0.002)
        raise TimeoutError()
    def close(self, **kwargs): self.closed = True
    def types(self): return [e['type'] for e in self.sent]


def wait_for(condition, seconds=3.0):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if condition():
            return True
        time.sleep(0.005)
    return False


class ConversationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.budget = VoiceBudget(Path(self.tmp.name) / 'usage.json')
        self.key = patch.dict(os.environ, {'OPENAI_API_KEY': 'synthetic-unit-key'})
        self.key.start()
        self.mic, self.player = Mic(), Player()
        self.failed, self.turns, self.agent, self.delegated = [], [], [], []

    def tearDown(self):
        self.conv.stop()
        time.sleep(0.03)
        self.key.stop()
        self.tmp.cleanup()

    def start(self, *sockets, cfg=None, greeting='Como posso ajudar?'):
        self.connect = Mock(side_effect=list(sockets))
        self.conv = LiveConversation({**FAST, **(cfg or {})}, budget=self.budget, connect=self.connect,
                                     stats_path=Path(self.tmp.name) / 'stats.jsonl',
                                     mic=lambda: self.mic, player=self.player,
                                     on_user_turn=self.turns.append,
                                     on_agent_turn=lambda text, result: self.agent.append((text, result)),
                                     on_delegation=self.delegated.append, on_failed=self.failed.append)
        self.conv.start(greeting)
        return self.conv

    def usage(self):
        return json.loads(self.budget.path.read_text())

    def test_session_uses_client_delegation_and_greets_once(self):
        # A API encerra a conexao com `delegation: null`: esta e a regressao do erro real.
        socket = Socket([{'type': 'session.started'}])
        self.start(socket)
        self.assertTrue(wait_for(lambda: 'session.commentary.append' in socket.types()))
        session = socket.sent[0]['session']
        self.assertEqual(session['delegation'], {'type': 'client'})
        self.assertEqual(session['model'], 'gpt-live-1')
        self.assertFalse(session['store'])
        self.assertEqual(socket.types().count('session.commentary.append'), 1)

    def test_nothing_is_sent_before_session_started(self):
        socket = Socket([])
        self.start(socket)
        self.mic.speak(LOUD, 10)
        time.sleep(0.1)
        self.assertEqual(socket.types(), ['session.start'])

    def test_microphone_audio_reaches_the_session(self):
        socket = Socket([{'type': 'session.started'}])
        self.start(socket)
        self.mic.speak(LOUD, 6)
        def heard():
            return any(e['type'] == 'session.input_audio.append' and any(base64.b64decode(e['audio']))
                       for e in socket.sent)
        self.assertTrue(wait_for(heard))

    def agent_speaking(self, socket):
        self.start(socket, cfg={'conversation_idle_s': 30})
        self.player.speaking = True
        self.assertTrue(wait_for(lambda: self.conv._open and len(socket.sent) >= 2))

    def hears(self, frame, count, volume=0.2):
        """O microfone recebe estes quadros enquanto o agente toca neste volume."""
        self.mic.speak(frame, count)
        self.player.volume = volume
        self.assertTrue(wait_for(lambda: not self.mic.frames, 5))
        time.sleep(0.03)

    @staticmethod
    def real_audio(socket):
        return [e for e in list(socket.sent) if e['type'] == 'session.input_audio.append'
                and any(base64.b64decode(e['audio']))]

    def test_speakers_echo_is_replaced_by_silence_while_agent_speaks(self):
        socket = Socket([{'type': 'session.started'}])
        self.agent_speaking(socket)
        self.hears(ECHO, 90)
        self.assertEqual(self.real_audio(socket), [])
        self.assertEqual(self.player.cleared, 0)

    def test_louder_agent_phrase_is_not_taken_for_the_person(self):
        # A referencia antiga era o eco recente: uma silaba mais forte parecia interrupcao e cortava a fala.
        socket = Socket([{'type': 'session.started'}])
        self.agent_speaking(socket)
        self.hears(np.full(BLOCK, 800, dtype='<i2').tobytes(), ECHO_LEARN + 15, volume=0.05)
        self.hears(np.full(BLOCK, 6400, dtype='<i2').tobytes(), 40, volume=0.4)    # 8x mais alto, o eco acompanha
        self.assertEqual(self.real_audio(socket), [])
        self.assertEqual(self.player.cleared, 0)
        self.assertEqual(self.conv.stats['barge_forwarded'], 0)

    def test_no_interruption_before_learning_the_echo(self):
        socket = Socket([{'type': 'session.started'}])
        self.agent_speaking(socket)
        self.hears(LOUD, ECHO_LEARN - 5)
        self.assertEqual(self.conv.stats['barge_forwarded'], 0)

    def test_talking_over_first_reaches_the_model_then_silences_local_audio(self):
        socket = Socket([{'type': 'session.started'}])
        self.agent_speaking(socket)
        self.hears(ECHO, ECHO_LEARN + 15)
        self.hears(LOUD, 12)                     # curto: chega ao modelo, sem cortar o audio local
        self.assertTrue(wait_for(lambda: self.real_audio(socket)))
        self.assertEqual(self.player.cleared, 0)
        self.assertEqual(self.conv.stats['barge_forwarded'], 1)
        self.hears(LOUD, 30)                     # insistiu: e interrupcao de verdade
        self.assertTrue(wait_for(lambda: self.player.cleared >= 1))
        self.assertEqual(self.conv.stats['barge_cut'], 1)

    def test_beginning_of_the_interruption_is_not_lost(self):
        socket = Socket([{'type': 'session.started'}])
        self.agent_speaking(socket)
        self.hears(ECHO, ECHO_LEARN + 15)
        self.hears(LOUD, 12)
        sent = b''.join(base64.b64decode(e['audio']) for e in self.real_audio(socket))
        self.assertGreaterEqual(len(sent), BLOCK * 2 * 8)    # os ~240 ms ate decidir tambem vao

    def test_headphones_never_silence_the_person(self):
        # Evidencia real: fone Bluetooth, zero interrupcoes e frases chegando sem o comeco ("... Rede Aurora")
        socket = Socket([{'type': 'session.started'}])
        self.agent_speaking(socket)
        self.hears(QUIET, ECHO_LEARN + 15)       # o microfone nao ouve o agente
        socket.sent.clear()
        soft_voice = np.full(BLOCK, 700, dtype='<i2').tobytes()      # abaixo do antigo limite fixo de 0,03
        self.hears(soft_voice, 3)                # nenhuma espera: desde o primeiro quadro
        self.assertTrue(self.real_audio(socket))
        self.assertEqual(self.player.cleared, 0)

    def test_insisting_over_headphones_silences_what_is_still_arriving(self):
        # Sem threads: quadro a quadro, para o tempo nao decidir o resultado
        self.conv = LiveConversation({**FAST}, budget=self.budget, connect=Mock(), mic=lambda: self.mic, player=self.player,
                                     stats_path=Path(self.tmp.name) / 'stats.jsonl')
        self.player.speaking, self.player.volume = True, 0.2
        for _ in range(ECHO_LEARN + 5):
            self.conv._gate_echo(QUIET, 0.0)      # o microfone nao ouve o agente: e fone
        self.assertEqual(self.player.cleared, 0)
        for _ in range(8):
            self.assertEqual(self.conv._gate_echo(LOUD, 0.36), LOUD)     # a voz sempre passa
        self.assertEqual(self.player.cleared, 0)  # "uhum" curto nao corta
        for _ in range(8):
            self.conv._gate_echo(QUIET, 0.0)      # a virgula nao zera a contagem
        for _ in range(5):
            self.conv._gate_echo(LOUD, 0.36)
        self.assertEqual(self.player.cleared, 1)
        self.assertEqual(self.conv.stats['barge_cut'], 1)

    def test_short_sounds_far_apart_never_add_up_to_a_cut(self):
        self.conv = LiveConversation({**FAST}, budget=self.budget, connect=Mock(), mic=lambda: self.mic, player=self.player,
                                     stats_path=Path(self.tmp.name) / 'stats.jsonl')
        self.player.speaking, self.player.volume = True, 0.2
        for _ in range(ECHO_LEARN + 5):
            self.conv._gate_echo(QUIET, 0.0)
        for _ in range(4):
            for _ in range(5):
                self.conv._gate_echo(LOUD, 0.36)
            for _ in range(20):
                self.conv._gate_echo(QUIET, 0.0)
        self.assertEqual(self.player.cleared, 0)

    def test_voice_above_a_low_speaker_echo_counts_as_interruption(self):
        socket = Socket([{'type': 'session.started'}])
        self.agent_speaking(socket)
        self.hears(np.full(BLOCK, 400, dtype='<i2').tobytes(), ECHO_LEARN + 15, volume=0.3)
        self.hears(np.full(BLOCK, 1600, dtype='<i2').tobytes(), 12, volume=0.3)
        self.assertEqual(self.conv.stats['barge_forwarded'], 1)

    def test_microphone_with_agent_quiet_keeps_person_voice(self):
        socket = Socket([{'type': 'session.started'}])
        self.start(socket, cfg={'conversation_idle_s': 30})
        self.mic.speak(LOUD, 6)
        self.assertTrue(wait_for(lambda: self.real_audio(socket)))

    def test_user_turn_is_delivered_once_after_pause(self):
        socket = Socket([{'type': 'session.started'},
                         {'type': 'session.input_transcript.delta', 'delta': 'abre a '},
                         {'type': 'session.input_transcript.delta', 'delta': 'calculadora'}])
        self.start(socket, cfg={'conversation_idle_s': 5})
        self.assertTrue(wait_for(lambda: self.turns))
        time.sleep(0.05)
        self.assertEqual(self.turns, ['abre a calculadora'])

    def test_sentence_ending_in_open_word_waits_for_the_rest(self):
        # Visto em uso real: "...com o mouse em" e "cima" viraram dois pedidos
        socket = Socket([{'type': 'session.started'},
                         {'type': 'session.input_transcript.delta', 'delta': 'esse que voce ta com o mouse em'}])
        self.start(socket, cfg={'conversation_idle_s': 9})
        time.sleep(1.4)
        self.assertEqual(self.turns, [])
        socket.events.append({'type': 'session.input_transcript.delta', 'delta': ' cima'})
        self.assertTrue(wait_for(lambda: self.turns, 3))
        self.assertEqual(self.turns, ['esse que voce ta com o mouse em cima'])

    def test_person_still_speaking_holds_the_turn(self):
        socket = Socket([{'type': 'session.started'},
                         {'type': 'session.input_transcript.delta', 'delta': 'abre a calculadora'}])
        self.start(socket, cfg={'conversation_idle_s': 9})
        self.mic.speak(LOUD, 150)          # ~0,5 s de voz local depois da transcricao
        time.sleep(1.2)                    # calou ha pouco: o fim da transcricao ainda pode chegar
        self.assertEqual(self.turns, [])
        self.assertTrue(wait_for(lambda: self.turns, 3.5))

    def test_transcript_tail_arriving_late_stays_in_the_same_turn(self):
        # Medido na API real: "Eu queria que voce me" + "explicasse" viravam dois pedidos
        socket = Socket([{'type': 'session.started'},
                         {'type': 'session.input_transcript.delta', 'delta': 'Eu queria que voce me'}])
        self.start(socket, cfg={'conversation_idle_s': 9})
        self.mic.speak(LOUD, 100)
        time.sleep(0.8)
        socket.events.append({'type': 'session.input_transcript.delta', 'delta': ' explicasse'})
        self.assertTrue(wait_for(lambda: self.turns, 3))
        self.assertEqual(self.turns, ['Eu queria que voce me explicasse'])

    def test_session_stays_open_while_a_task_runs_and_closes_after(self):
        socket = Socket([{'type': 'session.started'}])
        busy = [True]
        self.connect = Mock(side_effect=[socket])
        self.conv = LiveConversation({**FAST, 'conversation_task_hold_s': 30}, budget=self.budget, connect=self.connect,
                                     stats_path=Path(self.tmp.name) / 'stats.jsonl', mic=lambda: self.mic,
                                     player=self.player, keep_open=lambda: busy[0])
        self.conv.start('')
        time.sleep(0.6)                    # passou do prazo de quem nao falou
        self.assertNotIn('session.close', socket.types())
        busy[0] = False
        self.assertTrue(wait_for(lambda: 'session.close' in socket.types()))

    def test_task_hold_has_a_limit(self):
        socket = Socket([{'type': 'session.started'}])
        self.connect = Mock(side_effect=[socket])
        self.conv = LiveConversation({**FAST, 'conversation_task_hold_s': 0.3}, budget=self.budget, connect=self.connect,
                                     stats_path=Path(self.tmp.name) / 'stats.jsonl', mic=lambda: self.mic,
                                     player=self.player, keep_open=lambda: True)
        self.conv.start('')
        self.assertTrue(wait_for(lambda: 'session.close' in socket.types()))

    def test_prompt_uses_the_official_policies_and_lets_the_person_think(self):
        from core.voice.live_session import _instructions
        text = _instructions()
        for label in ('Backchannel policy:', 'Interruption policy:', 'Delegation policy:'):
            self.assertIn(label, text)
        self.assertIn('Keep listening while the user pauses to think', text)
        self.assertNotIn('Do not produce backchannels', text)
        self.conv = Mock()                 # este teste nao abre conversa

    def test_cut_beginning_marks_are_removed_from_the_turn(self):
        socket = Socket([{'type': 'session.started'},
                         {'type': 'session.input_transcript.delta', 'delta': '... Rede Aurora'}])
        self.start(socket, cfg={'conversation_idle_s': 9})
        self.assertTrue(wait_for(lambda: self.turns, 3))
        self.assertEqual(self.turns, ['Rede Aurora'])

    def test_turn_records_when_each_stage_happened(self):
        socket = Socket([{'type': 'session.started'},
                         {'type': 'session.input_transcript.delta', 'delta': 'abre a calculadora'},
                         voice_delta()])
        self.start(socket, cfg={'conversation_idle_s': 9}, greeting='')
        self.assertTrue(wait_for(lambda: self.turns, 3))
        timing = self.conv.last_turn
        self.assertLessEqual(timing['first_delta'], timing['flush'])
        self.assertIsNotNone(self.conv.agent_voice_at)

    def test_statistics_go_only_to_the_given_file_and_carry_no_text(self):
        socket = Socket([{'type': 'session.started'},
                         {'type': 'session.input_transcript.delta', 'delta': 'segredo falado'}], usage=2.0)
        self.start(socket, greeting='')
        self.assertTrue(wait_for(lambda: socket.closed))
        self.assertTrue(wait_for(lambda: (Path(self.tmp.name) / 'stats.jsonl').exists()))
        self.assertNotIn('segredo', (Path(self.tmp.name) / 'stats.jsonl').read_text(encoding='utf-8'))

    def test_wait_closed_confirms_usage_before_the_app_exits(self):
        socket = Socket([{'type': 'session.started'}], usage=3.0)
        self.start(socket, cfg={'conversation_idle_s': 30}, greeting='')
        self.assertTrue(wait_for(lambda: len(socket.sent) >= 1 and self.conv._open))
        time.sleep(0.05)
        self.conv.stop()
        self.assertTrue(self.conv.wait_closed(3))
        self.assertTrue(socket.closed)
        data = self.usage()
        self.assertEqual((data['seconds'], data['pending']), (3.0, None))

    def test_delegation_shortens_the_wait_for_the_turn(self):
        socket = Socket([{'type': 'session.started'},
                         {'type': 'session.input_transcript.delta', 'delta': 'abre a calculadora'},
                         {'type': 'session.delegation.created', 'delegation': {'id': 'item_1'}}])
        self.start(socket, cfg={'conversation_idle_s': 9})
        self.assertTrue(wait_for(lambda: self.turns, 0.55))

    def test_agent_text_waits_for_the_end_of_its_speech(self):
        socket = Socket([{'type': 'session.started'},
                         {'type': 'session.output_transcript.delta', 'delta': 'Ainda estou'}])
        self.start(socket, cfg={'conversation_idle_s': 9}, greeting='')
        self.player.speaking = True
        time.sleep(1.4)
        self.assertEqual(self.agent, [])
        socket.events.append({'type': 'session.output_transcript.delta', 'delta': ' verificando.'})
        time.sleep(0.1)
        self.player.speaking = False
        self.assertTrue(wait_for(lambda: self.agent, 3))
        self.assertEqual(self.agent, [('Ainda estou verificando.', False)])

    def test_delegation_is_reported_without_running_anything(self):
        socket = Socket([{'type': 'session.started'},
                         {'type': 'session.delegation.created', 'offset_ms': 1,
                          'delegation': {'id': 'item_1', 'type': 'delegation', 'target': 'client'}}])
        self.start(socket)
        self.assertTrue(wait_for(lambda: self.delegated))
        self.assertEqual(self.delegated, ['item_1'])

    def test_result_goes_as_commentary_with_its_delegation_and_is_not_shown_twice(self):
        socket = Socket([{'type': 'session.started'}])
        self.start(socket, greeting='', cfg={'conversation_idle_s': 5})
        self.conv.say('A calculadora esta aberta.', 'item_1')
        self.assertTrue(wait_for(lambda: 'session.commentary.append' in socket.types()))
        event = next(e for e in socket.sent if e['type'] == 'session.commentary.append')
        self.assertEqual(event['delegation_id'], 'item_1')
        self.assertIn('A calculadora esta aberta.', event['content'])
        socket.events.append({'type': 'session.output_transcript.delta', 'delta': 'A calculadora ja esta aberta.'})
        self.assertTrue(wait_for(lambda: self.agent, 4))
        self.assertEqual(self.agent, [('A calculadora ja esta aberta.', True)])

    def test_free_speech_finishing_after_result_is_sent_is_not_taken_as_the_result(self):
        # Visto na API real: "Ja vou abrir." terminou de transcrever depois do envio do resultado
        socket = Socket([{'type': 'session.started'}])
        self.start(socket, greeting='', cfg={'conversation_idle_s': 5})
        self.conv.say('A calculadora esta aberta.')
        self.assertTrue(wait_for(lambda: 'session.commentary.append' in socket.types()))
        socket.events.append({'type': 'session.output_transcript.delta', 'delta': 'Ja vou abrir.'})
        self.assertTrue(wait_for(lambda: self.agent, 4))
        self.assertEqual(self.agent, [('Ja vou abrir.', False)])
        self.assertTrue(same_message('A calculadora ja esta aberta', 'A calculadora esta aberta.'))

    def test_sending_a_result_renews_the_idle_time(self):
        socket = Socket([{'type': 'session.started'}])
        self.start(socket, greeting='', cfg={'wake_grace_s': 0.4, 'conversation_idle_s': 0.6})
        time.sleep(0.3)
        self.conv.say('Terminei a planilha.')
        self.assertTrue(wait_for(lambda: 'session.commentary.append' in socket.types()))
        time.sleep(0.35)      # passou do prazo de quem nao falou, ainda dentro do renovado
        self.assertNotIn('session.close', socket.types())

    def test_idle_session_closes_confirms_usage_and_refunds_the_rest(self):
        socket = Socket([{'type': 'session.started'}], usage=2.0)
        self.start(socket)
        self.assertTrue(wait_for(lambda: socket.closed))
        data = self.usage()
        self.assertEqual(data['seconds'], 2.0)
        self.assertIsNone(data['pending'])
        self.assertIn('session.close', socket.types())
        self.assertEqual(self.failed, [])

    def test_closed_session_reopens_on_local_speech_with_its_beginning(self):
        first, second = Socket([{'type': 'session.started'}]), Socket([{'type': 'session.started'}])
        self.start(first, second, greeting='')
        self.assertTrue(wait_for(lambda: first.closed))
        self.assertEqual(self.connect.call_count, 1)
        self.mic.speak(QUIET, 15)
        time.sleep(0.05)
        self.assertEqual(self.connect.call_count, 1)        # silencio nao abre sessao paga
        self.mic.speak(LOUD, 8)
        self.assertTrue(wait_for(lambda: self.connect.call_count == 2))
        def heard():
            return any(e['type'] == 'session.input_audio.append' and any(base64.b64decode(e['audio']))
                       for e in list(second.sent))
        self.assertTrue(wait_for(heard))

    def test_result_after_idle_close_reopens_session(self):
        first, second = Socket([{'type': 'session.started'}]), Socket([{'type': 'session.started'}])
        self.start(first, second, greeting='')
        self.assertTrue(wait_for(lambda: first.closed))
        self.conv.say('Terminei a planilha.')
        self.assertTrue(wait_for(lambda: 'session.commentary.append' in second.types()))

    def test_think_without_session_does_not_reopen(self):
        first = Socket([{'type': 'session.started'}])
        self.start(first, greeting='')
        self.assertTrue(wait_for(lambda: first.closed))
        self.conv.think('Ainda trabalhando.')
        time.sleep(0.05)
        self.assertEqual(self.connect.call_count, 1)

    def test_rejected_session_reports_provider_code_and_costs_nothing(self):
        socket = Socket([{'type': 'error', 'error': {'code': 'invalid_type', 'param': 'session.delegation'}}], drop=True)
        self.start(socket)
        self.assertTrue(wait_for(lambda: self.failed))
        self.assertEqual(self.failed, ['invalid_type'])
        self.assertEqual(self.usage()['seconds'], 0)
        self.assertIsNone(self.usage()['pending'])
        self.connect.assert_called_once()

    def test_rejected_handshake_reports_failure_without_retry(self):
        from websocket import WebSocketBadStatusException
        self.start(WebSocketBadStatusException('synthetic rejected key', status_code=403))
        self.assertTrue(wait_for(lambda: self.failed))
        self.assertEqual(self.failed, ['WebSocketBadStatusException'])
        self.assertEqual(self.usage()['seconds'], 0)
        self.connect.assert_called_once()

    def test_dropped_session_keeps_reservation_and_second_drop_gives_up(self):
        first = Socket([{'type': 'session.started'}], drop=True)
        second = Socket([{'type': 'session.started'}], drop=True)
        self.start(first, second)
        self.assertTrue(wait_for(lambda: first.closed))
        self.assertEqual(self.failed, [])
        self.assertEqual(self.usage()['pending'], RESERVE_S)
        self.mic.speak(LOUD, 8)
        self.assertTrue(wait_for(lambda: self.failed))
        self.assertEqual(self.failed, ['conexao'])
        self.assertEqual(self.connect.call_count, 2)
        self.assertEqual(self.usage()['seconds'], 2 * RESERVE_S)   # sem uso final: conta como gasto

    def test_daily_quota_is_checked_before_connecting(self):
        self.start(cfg={'daily_max_s': 10})
        self.assertTrue(wait_for(lambda: self.failed))
        self.assertEqual(self.failed, ['limite_diario'])
        self.connect.assert_not_called()

    def test_missing_key_never_connects(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': ''}):
            self.start()
            self.assertTrue(wait_for(lambda: self.failed))
        self.assertEqual(self.failed, ['sem_chave'])
        self.connect.assert_not_called()

    def test_stop_closes_session_and_never_reports_failure(self):
        socket = Socket([{'type': 'session.started'}])
        self.start(socket, cfg={'conversation_idle_s': 30})
        self.assertTrue(wait_for(lambda: len(socket.sent) >= 2))
        self.conv.stop()
        self.assertTrue(wait_for(lambda: socket.closed))
        self.assertIn('session.close', socket.types())
        self.assertEqual(self.failed, [])

    def test_output_audio_is_played_as_it_arrives(self):
        socket = Socket([{'type': 'session.started'}, voice_delta()])
        self.start(socket)
        self.assertTrue(wait_for(lambda: self.player.played))


class PlaybackTests(unittest.TestCase):
    class Clock:
        now = 100.0
        def __call__(self): return self.now

    def buffer(self):
        self.clock = self.Clock()
        return PlaybackBuffer(clock=self.clock)

    @staticmethod
    def pcm(level, ms):
        return np.full(int(RATE * ms / 1000), level, dtype='<i2').tobytes()

    def test_holds_until_prebuffered_then_plays_in_order(self):
        b = self.buffer()
        b.feed(self.pcm(5000, 100))
        self.assertFalse(any(b.pull(960)))        # 100 ms: ainda guardando
        b.feed(self.pcm(5000, 100))
        self.assertTrue(all(b.pull(960)))

    def test_short_phrase_plays_without_reaching_prebuffer(self):
        b = self.buffer()
        b.feed(self.pcm(5000, 60))
        self.clock.now += 0.31
        self.assertTrue(any(b.pull(960)))

    def test_quiet_chunk_before_voice_is_not_lost(self):
        # Inicio de palavra e baixo: descartar esse trecho engolia a primeira silaba
        b = self.buffer()
        b.feed(self.pcm(100, 100))
        b.feed(self.pcm(5000, 200))
        first = np.frombuffer(b.pull(960), dtype='<i2')
        self.assertEqual(first[0], 100)

    def test_silence_outside_speech_does_not_build_up_delay(self):
        b = self.buffer()
        for _ in range(50):
            b.feed(self.pcm(0, 100))
        self.assertFalse(b.speaking)
        self.assertEqual(len(b._data), 0)

    def test_pause_between_words_is_kept(self):
        b = self.buffer()
        b.feed(self.pcm(5000, 200))
        self.clock.now += 0.1
        b.feed(self.pcm(0, 100))
        self.assertEqual(len(b._data), int(RATE * 0.3) * 2)

    def test_network_gap_counts_and_rebuffers_instead_of_stuttering(self):
        b = self.buffer()
        b.feed(self.pcm(5000, 200))
        for _ in range(10):
            b.pull(960)
        self.assertEqual(b.underruns, 0)
        self.clock.now += 0.1
        out = b.pull(960)
        self.assertEqual(b.underruns, 1)
        self.assertEqual(len(out), 960)
        b.feed(self.pcm(5000, 60))
        self.assertFalse(any(b.pull(960)))        # junta um pouco antes de voltar
        b.feed(self.pcm(5000, 80))
        self.assertTrue(any(b.pull(960)))

    def test_end_of_phrase_is_not_a_network_problem(self):
        b = self.buffer()
        b.feed(self.pcm(5000, 200))
        self.clock.now += 1.0
        for _ in range(12):
            b.pull(960)
        self.assertEqual(b.underruns, 0)

    def test_speaking_covers_the_tail_and_clear_stops_at_once(self):
        b = self.buffer()
        b.feed(self.pcm(5000, 200))
        self.assertTrue(b.speaking)
        for _ in range(6):
            b.pull(1920)
        self.clock.now += 0.3
        self.assertTrue(b.speaking)              # o som ainda esta saindo
        self.clock.now += 0.3
        self.assertFalse(b.speaking)
        b.feed(self.pcm(5000, 200))
        b.clear()
        self.assertFalse(b.speaking)
        self.assertFalse(any(b.pull(960)))

    def test_level_reports_what_was_just_played(self):
        b = self.buffer()
        b.feed(self.pcm(8000, 300))
        b.pull(960)
        self.assertGreater(b.level(), 0.2)
        self.clock.now += 1.0
        self.assertEqual(b.level(), 0.0)


class ControllerTests(unittest.TestCase):
    """Decisoes do app sobre cada fala, sem microfone nem rede."""

    def voice(self):
        v = VoiceController.__new__(VoiceController)
        v.conv = Mock(speaking=False)
        v.ctrl = Mock(session=Mock(empty=True), state={})
        v.live = True
        v._voice_epoch, v._pending_guess, v._recent = 0, '', []
        v._conv_turn_now, v._conv_delegation, v._reply_delegation = None, None, None
        v._conv_last_agent, v._conv_corrected_at = '', 0.0
        v._delegations, v._traces, v._reply_trace = {}, {}, None
        v._inflight = False
        v._cmd_q = []
        v._enqueue = Mock()
        return v

    @staticmethod
    def understood(kind, **fields):
        def understand_fn(heard, confidence, ctx, recent):
            base = {'kind': kind, 'command': '', 'reply': '', 'guess': '', 'target': '', 'via': 'llm'}
            return {**base, **fields}
        return understand_fn

    def test_command_runs_even_if_model_never_delegates(self):
        v = self.voice()
        v._conv_turn('abre a calculadora', self.understood('command', command='abrir calculadora'))
        v._enqueue.assert_called_once_with('abrir calculadora', 'abre a calculadora')

    def test_result_uses_the_delegation_of_that_command(self):
        v = self.voice()
        v._conv_delegated('item_9')
        v._conv_turn('abre a calculadora', self.understood('command', command='abrir calculadora'))
        self.assertEqual(v._delegations['abrir calculadora'], 'item_9')
        self.assertIsNone(v._conv_delegation)

    def test_chat_never_runs_anything_even_when_model_delegates(self):
        v = self.voice()
        v._conv_delegated('item_2')
        v._conv_turn('que dia bonito', self.understood('chat', reply='Verdade!'))
        v._enqueue.assert_not_called()
        v.conv.say.assert_not_called()
        v.conv.think.assert_called_once()
        self.assertIn('Nada foi executado', v.conv.think.call_args[0][0])
        self.assertEqual(v.conv.think.call_args[0][1], 'item_2')

    def test_plain_chat_sends_nothing_to_the_model(self):
        v = self.voice()
        v._conv_turn('obrigado', self.understood('chat', reply='De nada'))
        v.conv.say.assert_not_called()
        v.conv.think.assert_not_called()

    def test_unclear_asks_and_only_yes_runs_the_guess(self):
        v = self.voice()
        v._conv_turn('abre aquele', self.understood('unclear', guess='abrir o Excel'))
        v._enqueue.assert_not_called()
        self.assertEqual(v._pending_guess, 'abrir o Excel')
        v._conv_last_agent = 'Foi para abrir o Excel?'
        v._conv_turn('sim')
        v._enqueue.assert_called_once_with('abrir o Excel', 'sim')

    def test_yes_does_not_run_a_guess_the_person_never_heard(self):
        v = self.voice()
        v._pending_guess = 'abrir o Excel'
        v._conv_last_agent = 'Como posso ajudar?'
        v._conv_turn('sim', self.understood('chat'))
        v._enqueue.assert_not_called()

    def test_sentence_starting_with_yes_word_is_its_own_request_not_the_guess(self):
        # A cadeia real: o palpite "configuracoes de rede" nao pode rodar com "pode abrir a rede"
        v = self.voice()
        v._pending_guess = 'abrir configuracoes de rede'
        v._conv_last_agent = 'Foi para abrir configuracoes de rede?'
        v._conv_turn('pode abrir a rede aurora', self.understood('command', command='abrir o cofre Rede Aurora no Obsidian'))
        v._enqueue.assert_called_once_with('abrir o cofre Rede Aurora no Obsidian', 'pode abrir a rede aurora')

    def test_cut_request_runs_when_model_also_took_it_as_a_request(self):
        # Sessao real: "... Rede Aurora" -> o modelo disse "deixa comigo" e nada aconteceu
        v = self.voice()
        v._conv_delegated('item_5')
        v._conv_turn('Rede Aurora', self.understood('unclear', guess='abrir o cofre Rede Aurora no Obsidian'))
        v._enqueue.assert_called_once_with('abrir o cofre Rede Aurora no Obsidian', 'Rede Aurora')
        self.assertEqual(v._delegations['abrir o cofre Rede Aurora no Obsidian'], 'item_5')

    def test_delegation_arriving_after_the_doubt_runs_the_guess(self):
        v = self.voice()
        v._conv_turn('Rede Aurora', self.understood('unclear', guess='abrir o cofre Rede Aurora no Obsidian'))
        v._enqueue.assert_not_called()
        v._conv_delegated('item_6')
        v._enqueue.assert_called_once()
        self.assertEqual(v._pending_guess, '')

    def test_model_promising_action_on_a_guess_runs_it(self):
        v = self.voice()
        v._say = Mock()
        with patch('desktop.voice.bus'):
            v._conv_turn('Rede Aurora', self.understood('unclear', guess='abrir o cofre Rede Aurora no Obsidian'))
            v._conv_agent_turn('Deixa comigo.', False)
        v._enqueue.assert_called_once()
        v._say.assert_not_called()               # nao ha o que corrigir: a tarefa foi pedida

    def test_settings_guard_stays_closed_even_if_the_model_delegates(self):
        # A guarda nao deixa palpite: uma delegacao sozinha nao abre as Configuracoes
        v = self.voice()
        v._conv_delegated('item_7')
        v._conv_turn('pode ser', self.understood('unclear', guess='', reply='Não vou mexer nas Configurações.'))
        v._enqueue.assert_not_called()

    def test_listening_sound_from_the_model_is_not_a_message_or_an_answer(self):
        v = self.voice()
        with patch('desktop.voice.bus') as bus:
            turn = {'heard': 'eu queria', 'kind': None, 'reply': ''}
            v._conv_turn_now = turn
            for sound in ('Aham.', 'uhum', 'Certo!'):
                v._conv_agent_turn(sound, False)
        bus.emit.assert_not_called()
        self.assertEqual(turn['reply'], '')
        self.assertEqual(v._conv_last_agent, '')

    def test_app_never_speaks_over_a_cut_sentence(self):
        v = self.voice()
        turn = {'heard': 'eu queria abrir o', 'kind': 'chat', 'reply': ''}
        v._conv_turn_now = turn
        v._conv_ensure_reply(turn, v.conv, 'Oi?')
        v.conv.say.assert_not_called()

    def test_app_waits_long_enough_for_a_pause_to_think(self):
        import desktop.voice as module
        self.assertGreaterEqual(module.REPLY_WINDOW_S, 5.0)

    def test_promise_is_not_corrected_aloud_but_stays_out_of_the_context(self):
        v = self.voice()
        v._say = Mock()
        with patch('desktop.voice.bus'):
            v._conv_turn_now = {'heard': 'abre aquilo', 'kind': 'chat', 'reply': ''}
            v._conv_agent_turn('Deixa comigo.', False)
        v._say.assert_not_called()
        v.ctrl.session.set_last_reply.assert_not_called()

    def test_silent_model_gets_a_reply_from_the_app(self):
        v = self.voice()
        with patch('desktop.voice.bus') as bus:
            turn = {'heard': 'tudo bem?', 'kind': 'chat', 'reply': ''}
            v._conv_turn_now = turn
            v._conv_ensure_reply(turn, v.conv, 'Tudo sim!')
        v.conv.say.assert_called_once_with('Tudo sim!')
        bus.emit.assert_called_once()

    def test_model_that_answered_is_not_answered_twice(self):
        v = self.voice()
        for turn, speaking in (({'heard': 'x', 'kind': 'chat', 'reply': 'Oi'}, False),
                               ({'heard': 'x', 'kind': 'chat', 'reply': ''}, True)):
            v.conv.speaking = speaking
            v._conv_turn_now = turn
            v._conv_ensure_reply(turn, v.conv, 'Tudo sim!')
        v.conv.say.assert_not_called()

    def test_reply_from_an_old_conversation_is_dropped(self):
        v = self.voice()
        turn = {'heard': 'x', 'kind': 'chat', 'reply': ''}
        v._conv_turn_now = turn
        v._conv_ensure_reply(turn, Mock(), 'Tudo sim!')
        v.conv.say.assert_not_called()

    def test_noise_is_never_answered_by_the_app(self):
        v = self.voice()
        with patch.object(v, '_later') as later:
            v._conv_turn('conversa da tv', self.understood('noise'))
        later.assert_not_called()

    def test_latency_row_has_times_and_no_text(self):
        v = self.voice()
        import desktop.voice as module
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'latency.jsonl'
            with patch.object(module, 'VOICE_LATENCY_PATH', path):
                v._record_latency({'speech_end': 10.0, 'first_delta': 10.9, 'flush': 11.5, 'understood': 12.7,
                                   'delegated': True}, kind='command', via='llm')
                v._record_latency({'speech_end': float('-inf')}, kind='chat', via='llm')
            rows = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]['first_delta_s'], rows[0]['flush_s'], rows[0]['understood_s']), (0.9, 1.5, 2.7))
        self.assertNotIn('heard', rows[0])

    def test_shutdown_stops_everything_and_waits_for_the_session(self):
        v = self.voice()
        conv = v.conv
        v.tts, v.hotkey, v._live_stop, v._rec_stop = Mock(), Mock(), threading.Event(), threading.Event()
        v.shutdown()
        self.assertFalse(v.live)
        self.assertIsNone(v.conv)
        conv.stop.assert_called_once()
        conv.wait_closed.assert_called_once()
        self.assertTrue(v._live_stop.is_set() and v._rec_stop.is_set())
        v.hotkey.stop.assert_called_once()
        v.tts.stop.assert_called_once()

    def test_task_reply_is_shown_only_after_decision_and_stays_out_of_the_conversation(self):
        v = self.voice()
        with patch('desktop.voice.bus') as bus:
            v._conv_turn_now = {'heard': 'abre o cofre', 'kind': None, 'reply': ''}
            v._conv_agent_turn('Deixa comigo.', False)
            bus.emit.assert_not_called()
            v._conv_decided('command')
            bus.emit.assert_called_once_with('voice_reply', {'text': 'Deixa comigo.'})
        v.ctrl.session.add_turn.assert_not_called()

    def test_false_action_claim_is_corrected_and_not_kept_as_context(self):
        # "To clicando no que ta com o mouse em cima" sem nenhuma tarefa rodando
        v = self.voice()
        v._say = Mock()
        with patch('desktop.voice.bus'):
            v._conv_turn_now = {'heard': 'cima', 'kind': None, 'reply': ''}
            v._conv_decided('chat')
            v._conv_agent_turn('To clicando no que ta com o mouse em cima.', False)
        v.ctrl.session.set_last_reply.assert_not_called()
        v._say.assert_called_once()
        self.assertIn('ainda não fiz nada', v._say.call_args[0][0])

    def test_plain_chat_reply_is_kept_and_not_corrected(self):
        v = self.voice()
        v._say = Mock()
        with patch('desktop.voice.bus'):
            v._conv_turn_now = {'heard': 'tudo bem?', 'kind': 'chat', 'reply': ''}
            v._conv_agent_turn('Tudo sim!', False)
        v.ctrl.session.set_last_reply.assert_called_once_with('Tudo sim!')
        v._say.assert_not_called()

    def test_no_discards_the_guess(self):
        v = self.voice()
        v._pending_guess = 'abrir o Excel'
        self.assertEqual(v._conv_turn('nao')['kind'], 'chat')
        v._enqueue.assert_not_called()
        self.assertEqual(v._pending_guess, '')

    def test_stop_stops_the_running_task(self):
        v = self.voice()
        v.ctrl.state = {'running': True}
        v._conv_turn('para tudo', self.understood('stop'))
        v.ctrl.force_stop.assert_called_once()
        self.assertEqual(v._voice_epoch, 1)

    def test_stop_listening_closes_the_conversation(self):
        v = self.voice()
        v.set_live = Mock()
        self.assertEqual(v._conv_turn('para de ouvir')['kind'], 'stop_listening')
        v.set_live.assert_called_once_with(False)

    def test_say_routes_results_to_session_and_quiets_feedback(self):
        v = self.voice()
        v.tts = Mock()
        v._reply_delegation = 'item_3'
        v._say('Ainda trabalhando', show=False)
        v.conv.think.assert_called_once_with('Ainda trabalhando', 'item_3')
        v.conv.say.assert_not_called()
        v._say('A planilha esta pronta.', show=False, purpose='reply')
        v.conv.say.assert_called_once_with('A planilha esta pronta.', 'item_3')
        self.assertIsNone(v._reply_delegation)
        v.tts.speak.assert_not_called()

    def test_failure_returns_to_local_conversation(self):
        v = self.voice()
        v.stt, v._live_stop, v._live_loop = Mock(), threading.Event(), Mock()
        v._live_stop.set()
        v._conv_blocked_until = 0.0
        v._conv_failed('conexao')
        self.assertIsNone(v.conv)
        self.assertGreater(v._conv_blocked_until, 0)
        self.assertFalse(v._live_stop.is_set())
        self.assertTrue(wait_for(lambda: v._live_loop.called))

    def test_toggle_off_or_cool_off_keeps_microphone_local(self):
        v = self.voice()
        v.tts = Mock(metered=True)
        v.live_conversation, v._conv_blocked_until = False, 0.0
        self.assertFalse(v._conv_start())
        v.live_conversation, v._conv_blocked_until = True, time.monotonic() + 60
        self.assertFalse(v._conv_start())
        v.tts, v._conv_blocked_until = Mock(metered=False), 0.0
        self.assertFalse(v._conv_start())

    def test_spoken_task_reply_is_not_shown_again_but_conversation_is(self):
        v = self.voice()
        with patch('desktop.voice.bus') as bus:
            v._conv_agent_turn('A calculadora esta aberta.', True)
            bus.emit.assert_not_called()
            v._conv_turn_now = {'heard': 'tudo bem?', 'kind': 'chat', 'reply': ''}
            v._conv_agent_turn('Tudo sim!', False)
            bus.emit.assert_called_once_with('voice_chat', {'heard': 'tudo bem?', 'reply': 'Tudo sim!', 'kind': 'chat'})


if __name__ == '__main__':
    unittest.main()
