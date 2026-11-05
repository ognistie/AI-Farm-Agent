"""Executor boundary regressions: mocks never operate the user's desktop."""
import sys
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class ExecutorTests(unittest.TestCase):
    def engine(self):
        from core.automation import AutomationEngine
        engine = AutomationEngine.__new__(AutomationEngine)
        engine.executed_steps, engine.workspace = [], {}
        engine.should_stop = None
        return engine

    def test_simulation_never_dispatches_handlers(self):
        engine = self.engine()
        methods = {name: Mock(side_effect=AssertionError("handler dispatched"))
                   for name in dir(engine) if name.startswith("_") and callable(getattr(engine, name))
                   and not name.startswith("__")}
        with patch.multiple(engine, **methods), patch('core.action_logger.log_action'):
            for action in ('delete_file', 'move_file', 'copy_file', 'create_folder', 'run_command',
                           'run_python', 'pip_install', 'type_text', 'click', 'hotkey', 'web_goto'):
                with self.subTest(action=action):
                    result = engine.execute(action, {}, dry_run=True)
                    self.assertTrue(result['success'])
                    self.assertEqual(result['status'], 'simulated')
                    self.assertFalse(result['verified'])
        for handler in methods.values():
            handler.assert_not_called()

    def test_nonzero_exit_is_failure(self):
        engine = self.engine()
        with patch('core.automation._fg_state', return_value=(0, '')), \
             patch('core.process_runner.run_command', return_value={'success': False, 'status': 'failed',
                   'result': 'synthetic failure', 'exit_code': 1, 'verified': False}), \
             patch('core.action_logger.log_action'):
            result = engine._run_command({'command': 'synthetic'})
        self.assertFalse(result['success'])
        self.assertEqual(result['exit_code'], 1)

    def test_arbitrary_execution_is_rejected_in_application(self):
        engine = self.engine()
        for action in ('run_python', 'run_command', 'pip_install'):
            with self.subTest(action=action):
                result = engine.execute(action, {'code': 'print(1)', 'command': 'synthetic'})
                self.assertFalse(result['success'])
                self.assertEqual(result['status'], 'rejected')

    def test_cancel_does_not_release_running_slot(self):
        from desktop.controller import Controller
        controller = Controller.__new__(Controller)
        controller.state = {'running': True}
        controller._lock = threading.Lock()
        controller._plan_gate = threading.Event()
        controller._cancel_event = threading.Event()
        controller._tls = threading.local()
        controller._run_id = 1
        with patch('desktop.controller.bus.emit'):
            controller.force_stop()
        self.assertTrue(controller.state['running'])
        self.assertTrue(controller._cancel_event.is_set())
        self.assertFalse(controller._alive())
        with patch('desktop.controller.threading.Thread') as thread, patch('desktop.controller.bus.emit'):
            controller.execute_task('next task')
            thread.assert_not_called()

    def test_approval_is_bound_to_current_plan(self):
        from desktop.controller import Controller
        controller = Controller.__new__(Controller)
        controller._lock = threading.Lock()
        controller._plan_gate = threading.Event()
        controller._cancel_event = threading.Event()
        controller._plan_token, controller._plan_ok = 'current-plan', False
        self.assertFalse(controller.approve_plan(True, 'old-plan'))
        self.assertFalse(controller._plan_gate.is_set())
        self.assertTrue(controller.approve_plan(True, 'current-plan'))
        controller._cancel_event.set()
        self.assertFalse(controller.approve_plan(True, 'current-plan'))


class VoiceFailureTests(unittest.TestCase):
    def test_provider_error_and_invalid_kind_are_not_commands(self):
        from core.voice.understand import understand
        for llm in (Mock(side_effect=RuntimeError('provider error')),
                    Mock(return_value='{"kind":"invalid","command":"delete something"}')):
            with patch('core.voice.persona.get_persona') as persona:
                persona.return_value.pick.return_value = 'Pode repetir?'
                persona.return_value.style.return_value = ''
                result = understand('talvez faca algo naquele aplicativo', 0.1, llm=llm)
                self.assertEqual(result['kind'], 'unclear')
                self.assertEqual(result['command'], '')
                self.assertEqual(result['guess'], '')

    def test_cancel_during_understanding_discards_result(self):
        from desktop.voice import VoiceController
        from types import SimpleNamespace
        voice = VoiceController.__new__(VoiceController)
        voice._voice_epoch = 0
        voice._pending_guess, voice._recent = '', []
        voice.ctrl = SimpleNamespace(session=SimpleNamespace(empty=True))
        voice._enqueue = Mock()
        def understand(*args):
            voice._voice_epoch += 1
            return {'kind': 'command', 'command': 'stale'}
        result = voice.handle_text('pedido sintetico', understand_fn=understand)
        self.assertEqual(result['kind'], 'noise')
        voice._enqueue.assert_not_called()

    def test_queues_are_bounded_and_stale_audio_rejected(self):
        import collections, queue
        from desktop.voice import VoiceController
        voice = VoiceController.__new__(VoiceController)
        voice._voice_epoch, voice._audio_q = 1, queue.Queue(maxsize=1)
        voice._say, voice._dispatch = Mock(), Mock()
        voice._queue_audio('old', 'record', None, 0)
        self.assertTrue(voice._audio_q.empty())
        voice._queue_audio('new', 'record', None, 1)
        voice._queue_audio('overflow', 'record', None, 1)
        self.assertEqual(voice._audio_q.qsize(), 1)
        voice._qlock, voice._cmd_q = threading.RLock(), collections.deque([('x','x',0)]*8)
        voice._enqueue('overflow','overflow')
        self.assertEqual(len(voice._cmd_q), 8)


if __name__ == '__main__':
    unittest.main()
