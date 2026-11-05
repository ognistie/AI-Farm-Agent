import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class ReleaseSafetyTests(unittest.TestCase):
    def test_empty_close_never_enumerates_or_terminates_processes(self):
        from core.automation import AutomationEngine
        engine = AutomationEngine.__new__(AutomationEngine)
        with patch('core.automation.psutil.process_iter') as processes:
            self.assertTrue(engine._close_app({}).startswith('⛔'))
            processes.assert_not_called()

    def test_missing_target_never_types(self):
        from core.automation import AutomationEngine
        engine = AutomationEngine.__new__(AutomationEngine)
        with patch('core.automation.pyautogui.write') as write:
            self.assertTrue(engine._type_text({'text':'fixture'}).startswith('⛔'))
            write.assert_not_called()

    def test_native_web_uses_no_python_and_rejects_protocol_execution(self):
        from core.automation import AutomationEngine
        from agents.web_agent import _native_fallback
        steps = _native_fallback([{'action':'web_goto','params':{'url':'https://example.com'}}])
        self.assertEqual(steps[0]['action'], 'open_url')
        engine = AutomationEngine.__new__(AutomationEngine)
        with patch('webbrowser.open_new_tab') as browser:
            for url in ('file:///C:/Windows/system32/cmd.exe','javascript:alert(1)','ms-settings:','https://user:secret@example.com','https://['):
                self.assertTrue(engine._open_url({'url':url}).startswith('⛔'))
            browser.assert_not_called()

    def test_schema_is_preserved_alongside_effort(self):
        from core.ai_client import AIClient
        client = AIClient.__new__(AIClient)
        stream = Mock()
        stream.get_final_message.return_value = SimpleNamespace(stop_reason='end_turn')
        manager = Mock()
        manager.__enter__ = Mock(return_value=stream)
        manager.__exit__ = Mock(return_value=False)
        client._client = SimpleNamespace(messages=SimpleNamespace(stream=Mock(return_value=manager)))
        client.on_progress = None
        client._record_success = Mock(return_value={'text':'{}'})
        schema = {'type':'object','properties':{},'additionalProperties':False}
        client.message('claude-sonnet-5','fixture','fixture',effort='medium',json_schema=schema)
        args = client._client.messages.stream.call_args.kwargs
        self.assertEqual(args['output_config']['effort'],'medium')
        self.assertEqual(args['output_config']['format']['schema'],schema)


if __name__ == '__main__': unittest.main()
