import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import app_pilot as pilot_module
from core.app_pilot import AppPilot, _window_gone


def snapshot():
    return SimpleNamespace(title='projeto - Visual Studio Code', elements=[], render=lambda: 'JANELA')


class ClosedWindow(unittest.TestCase):
    """A sequencia real: clica em Close, a janela some, e a volta seguinte nao acha a janela."""

    def run_pilot(self, goal, front, gone=True, snap=snapshot):
        llm = Mock(return_value=json.dumps({'action': 'click', 'id': 1, 'reason': 'x'}))
        pilot = AppPilot(llm=llm)
        with patch.object(pilot_module, 'window_from_handle', return_value=SimpleNamespace(handle=7)), \
                patch('core.automation._bring_to_front', side_effect=front), \
                patch('core.automation._is_front', return_value=True), \
                patch.object(pilot_module, '_window_gone', return_value=gone), \
                patch.object(pilot_module.B, 'snapshot', side_effect=lambda *a, **k: snap()), \
                patch.object(pilot_module, '_view', return_value=('v',)), \
                patch.object(AppPilot, '_act', return_value=('janela mudou', "click botao 'Close'")):
            return pilot.run(goal, 7, 'projeto'), llm

    def test_window_gone_after_click_counts_as_closed(self):
        result, llm = self.run_pilot('fechar o VS Code', [True, False])
        self.assertTrue(result['ok'])
        self.assertEqual(result['status'], 'done')
        self.assertEqual(result['trail'], ["click botao 'Close'"])
        self.assertIn('fechei', result['say'])
        llm.assert_called_once()                # nao gasta outra chamada com a janela ja fechada

    def test_accents_and_other_words_for_closing(self):
        for goal in ('encerrar o Word', 'sair do programa', 'Feche essa janela'):
            result, _ = self.run_pilot(goal, [True, False])
            self.assertTrue(result['ok'], goal)

    def test_window_gone_during_other_goal_is_a_failure(self):
        # O usuario fechou, ou o app caiu: o objetivo nao foi cumprido
        result, _ = self.run_pilot('escrever bom dia no documento', [True, False])
        self.assertFalse(result['ok'])
        self.assertEqual(result['result'], 'A janela foi fechada.')

    def test_window_alive_without_focus_is_still_a_failure(self):
        result, _ = self.run_pilot('fechar o VS Code', [True, False], gone=False)
        self.assertFalse(result['ok'])
        self.assertIn('primeiro plano', result['result'])

    def test_closing_goal_without_any_action_does_not_claim_success(self):
        result, llm = self.run_pilot('fechar o VS Code', [False])
        self.assertFalse(result['ok'])
        llm.assert_not_called()

    def test_snapshot_lost_after_click_counts_as_closed(self):
        snaps = iter([snapshot(), None])
        result, _ = self.run_pilot('fechar o VS Code', [True, True], snap=lambda: next(snaps))
        self.assertTrue(result['ok'])

    def test_save_dialog_keeps_going_instead_of_claiming_closed(self):
        # Janela segue na frente: o modelo le o dialogo, nada e dado como fechado
        llm = Mock(side_effect=[json.dumps({'action': 'click', 'id': 1}), json.dumps({'action': 'ask_user', 'reason': 'Salvar?'})])
        pilot = AppPilot(llm=llm)
        with patch.object(pilot_module, 'window_from_handle', return_value=SimpleNamespace(handle=7)), \
                patch('core.automation._bring_to_front', return_value=True), \
                patch('core.automation._is_front', return_value=True), \
                patch.object(pilot_module.B, 'snapshot', side_effect=lambda *a, **k: snapshot()), \
                patch.object(pilot_module, '_view', return_value=('v',)), \
                patch.object(AppPilot, '_act', return_value=('janela mudou', "click botao 'Close'")):
            result = pilot.run('fechar o VS Code', 7, 'projeto')
        self.assertEqual(result['status'], 'ask_user')


class WindowGone(unittest.TestCase):
    def user32(self, exists=True, visible=True):
        fake = SimpleNamespace(IsWindow=lambda h: exists, IsWindowVisible=lambda h: visible)
        return patch('ctypes.windll', SimpleNamespace(user32=fake), create=True)

    def test_destroyed_or_hidden_is_gone_and_visible_is_not(self):
        with self.user32(exists=False):
            self.assertTrue(_window_gone(7, wait=0))
        with self.user32(visible=False):
            self.assertTrue(_window_gone(7, wait=0))
        with self.user32():
            self.assertFalse(_window_gone(7, wait=0))


if __name__ == '__main__':
    unittest.main()
