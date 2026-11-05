import sys
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import automation as a


class DiscoveryTests(unittest.TestCase):
    def test_background_notepad_identified_by_process_not_document_title(self):
        window = SimpleNamespace(visible=True, title='Anotacao', _hWnd=42)
        with patch.object(a.gw, 'getAllWindows', return_value=[window]), patch.object(a, '_fg_state', return_value=(99,'AI Farm Agent')), patch.object(a, '_process_matches', return_value=True):
            self.assertEqual(a._resolve_app_window('Bloco de Notas'),42)

    def test_ambiguous_documents_are_not_selected(self):
        windows=[SimpleNamespace(visible=True,title='Documento',_hWnd=h) for h in (41,42)]
        with patch.object(a.gw,'getAllWindows',return_value=windows), patch.object(a,'_fg_state',return_value=(99,'AI Farm Agent')), patch.object(a,'_process_matches',return_value=True):
            self.assertIsNone(a._resolve_app_window('Bloco de Notas'))

    def test_new_window_is_found_even_with_another_of_the_same_app(self):
        windows=[SimpleNamespace(visible=True,title='Documento',_hWnd=h) for h in (41,42)]
        with patch.object(a.gw,'getAllWindows',return_value=windows), patch.object(a,'_fg_state',return_value=(99,'AI Farm Agent')), patch.object(a,'_process_matches',return_value=True):
            self.assertEqual(a._resolve_app_window('Bloco de Notas',known=[41]),42)
            self.assertIsNone(a._resolve_app_window('Bloco de Notas',known=[]))

    def test_spoofed_title_does_not_override_process_identity(self):
        window=SimpleNamespace(visible=True,title='Bloco de Notas',_hWnd=42)
        with patch.object(a.gw,'getAllWindows',return_value=[window]), patch.object(a,'_process_matches',return_value=False):
            self.assertIsNone(a._resolve_app_window('Bloco de Notas'))


class OpenTests(unittest.TestCase):
    """Abrir app sem janela de verdade: o Windows pode negar o primeiro plano."""

    def engine(self):
        engine = a.AutomationEngine.__new__(a.AutomationEngine)
        engine.dry_run, engine._expect, engine._target_hwnd = False, None, None
        return engine

    def opening(self, windows, front=(99, 'AI Farm Agent')):
        started = time.time()
        with patch.object(a.subprocess, 'Popen'), patch.object(a.gw, 'getAllWindows', side_effect=windows), \
                patch.object(a, '_fg_state', return_value=front), patch.object(a, '_process_matches', return_value=True), \
                patch.object(a, '_activate_hwnd', return_value='janela') as activate:
            engine = self.engine()
            result = engine._app_search({'name': 'Bloco de Notas'})
        return result, engine, activate, time.time() - started

    @staticmethod
    def window(hwnd):
        return SimpleNamespace(visible=True, title='Anotacao', _hWnd=hwnd)

    def test_opened_behind_does_not_wait_the_full_timeout(self):
        calls = iter([[]])                     # antes de abrir: nenhuma janela
        seen = lambda: next(calls, [self.window(42)])
        result, engine, activate, took = self.opening(lambda: seen())
        self.assertEqual(result, '✅ Bloco de Notas')
        self.assertEqual(engine._target_hwnd, 42)
        activate.assert_called_once_with(42)
        self.assertLess(took, 3)

    def test_second_window_opened_behind_is_not_ambiguous(self):
        calls = iter([[self.window(41)]])
        seen = lambda: next(calls, [self.window(41), self.window(42)])
        result, engine, _, took = self.opening(lambda: seen())
        self.assertEqual(result, '✅ Bloco de Notas')
        self.assertEqual(engine._target_hwnd, 42)
        self.assertLess(took, 3)

    def test_app_reusing_its_window_is_accepted_quickly(self):
        result, engine, _, took = self.opening(lambda: [self.window(41)])
        self.assertEqual(result, '✅ Bloco de Notas')
        self.assertEqual(engine._target_hwnd, 41)
        self.assertLess(took, 5)

    def test_no_window_at_all_still_fails_honestly(self):
        with patch.object(a.subprocess, 'Popen'), patch.object(a.gw, 'getAllWindows', return_value=[]), \
                patch.object(a, '_fg_state', return_value=(99, 'AI Farm Agent')), \
                patch.object(a.AutomationEngine, '_await_ready', return_value=(12.0, False)):
            result = self.engine()._app_search({'name': 'Bloco de Notas'})
        self.assertTrue(result.startswith('❌'), result)
