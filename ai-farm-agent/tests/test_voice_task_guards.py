import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agents.desktop_agent import DesktopAgent
from agents.maestro import vault_plan
from core.obsidian_vaults import known_vaults, mentioned_vault, parse_request, vault_uri
from core.voice.understand import confirms, understand

VAULTS = ['AI-Farm-agents', 'Cofre Pessoal x Amigos,Familia', 'Aurora-Financas', 'Rede Aurora', 'rede-aurora-vault']


def llm_says(**fields):
    base = {'kind': 'command', 'command': '', 'target': '', 'reply': 'Ok', 'guess': '', 'confidence': 0.95}
    return lambda system, user: json.dumps({**base, **fields})


class VaultParsing(unittest.TestCase):
    def test_misheard_name_from_real_use_opens_the_right_vault(self):
        for said in ('abre a rede Aurol dentro do Obsidian', 'abrir o cofre rede aurol', 'abre a rede aurora'):
            self.assertEqual(parse_request(said, VAULTS), {'open': 'Rede Aurora'}, said)

    def test_unnamed_or_ambiguous_vault_asks_instead_of_guessing(self):
        self.assertIn('Rede Aurora', parse_request('abrir o cofre no Obsidian', VAULTS)['ask'])
        self.assertIn('ask', parse_request('abrir um cofre (vault) chamado Aurol no Obsidian', VAULTS))

    def test_unknown_named_vault_says_so(self):
        self.assertIn('Não achei', parse_request('abre o cofre financeiro do joao silva', VAULTS)['ask'])

    def test_requests_about_other_things_are_not_taken(self):
        for said in ('abrir configurações de rede', 'abre o Obsidian', 'abre a rede', 'abre o excel',
                     'quanto custa uma rede de pesca'):
            self.assertIsNone(parse_request(said, VAULTS), said)

    def test_no_obsidian_installed_changes_nothing(self):
        self.assertIsNone(parse_request('abre o cofre rede aurora', []))

    def test_only_the_name_is_a_mention_not_a_sentence(self):
        self.assertEqual(mentioned_vault('E... na rede Aurol', VAULTS), 'Rede Aurora')
        self.assertEqual(mentioned_vault('a rede aurora tem muita coisa boa la dentro hoje', VAULTS), '')

    def test_uri_is_encoded_and_accepted_by_the_executor_pattern(self):
        import re
        from core.obsidian_vaults import URI_PATTERN
        for name in VAULTS:
            self.assertRegex(vault_uri(name), URI_PATTERN)
        self.assertIsNone(re.match(URI_PATTERN, 'obsidian://open?vault=x&file=../../segredo'))
        self.assertIsNone(re.match(URI_PATTERN, 'obsidian://new?vault=x&content=y'))

    def test_reads_only_vaults_that_exist_on_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            real = Path(tmp) / 'Cofre Real'
            real.mkdir()
            config = Path(tmp) / 'obsidian.json'
            config.write_text(json.dumps({'vaults': {'a': {'path': str(real)}, 'b': {'path': str(Path(tmp) / 'sumiu')}}}))
            self.assertEqual(known_vaults(config), ['Cofre Real'])
            config.write_text('{quebrado')
            self.assertEqual(known_vaults(config), [])
        self.assertEqual(known_vaults(Path('nao-existe.json')), [])


class VaultExecution(unittest.TestCase):
    def test_plan_goes_straight_to_the_link_even_with_another_window_in_focus(self):
        with patch('core.obsidian_vaults.known_vaults', return_value=VAULTS):
            plan = vault_plan('abrir o cofre rede aurol no Obsidian')
        self.assertEqual(plan['fast_path'], 'abrir')
        sub = plan['subtasks'][0]
        self.assertEqual(sub['agent'], 'DESKTOP')
        self.assertEqual(sub['params']['vault'], 'Rede Aurora')
        agent = DesktopAgent.__new__(DesktopAgent)
        sub['params']['continue'] = {'type': 'app', 'title': 'Configurações', 'hwnd': 1, 'key': 'configuracoes'}
        steps = agent.plan(sub)['steps']
        self.assertEqual([s['action'] for s in steps], ['open_path', 'focus_window'])
        self.assertEqual(steps[0]['params']['path'], 'obsidian://open?vault=Rede%20Aurora')
        self.assertEqual(steps[1]['params']['title'], 'Rede Aurora')
        self.assertNotIn('app_task', [s['action'] for s in steps])    # nenhum clique por visao

    def test_ambiguous_plan_returns_a_question(self):
        with patch('core.obsidian_vaults.known_vaults', return_value=VAULTS):
            plan = vault_plan('abrir o cofre no Obsidian')
        self.assertTrue(plan['needs_clarification'])

    def test_other_tasks_fall_through(self):
        with patch('core.obsidian_vaults.known_vaults', return_value=VAULTS):
            self.assertIsNone(vault_plan('abrir o Excel'))

    def test_executor_opens_only_the_fixed_pattern(self):
        from core.automation import AutomationEngine
        engine = AutomationEngine.__new__(AutomationEngine)
        engine.dry_run = False
        with patch('os.startfile') as start, patch('time.sleep'):
            engine._open_path({'path': 'obsidian://open?vault=Rede%20Aurora'})
            start.assert_called_once_with('obsidian://open?vault=Rede%20Aurora')
            start.reset_mock()
            result = engine._open_path({'path': 'obsidian://new?vault=x&content=y'})
            start.assert_not_called()
            self.assertTrue(result.startswith('❌'))


class VoiceGuards(unittest.TestCase):
    """As falas da sessao real que levaram o agente para as Configuracoes do Windows."""

    def setUp(self):
        patcher = patch('core.obsidian_vaults.known_vaults', return_value=VAULTS)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_spoken_vault_name_is_never_network_settings(self):
        u = understand('E... na rede Aurol', llm=self.fail)
        self.assertEqual(u['kind'], 'unclear')
        self.assertEqual(u['guess'], 'abrir o cofre Rede Aurora no Obsidian')
        u = understand('Abre a rede Aurol dentro do Obsidian', llm=self.fail)
        self.assertEqual((u['kind'], u['command']), ('command', 'abrir o cofre Rede Aurora no Obsidian'))

    def test_settings_not_named_by_the_person_never_run(self):
        u = understand('pode ser isso mesmo', llm=llm_says(command='abrir configurações de rede'))
        self.assertEqual(u['kind'], 'unclear')
        self.assertEqual(u['command'], '')
        self.assertEqual(u['guess'], '')       # sem palpite: um "sim" depois tambem nao roda

    def test_click_in_settings_from_vague_speech_never_runs(self):
        for said in ('esse aí mesmo que você tá com o mouse em cima', 'clica nesse aí'):
            u = understand(said, llm=llm_says(command='clicar no item em foco com o mouse, nas Configurações',
                                              target='app:configuracoes'))
            self.assertEqual(u['kind'], 'unclear', said)
            self.assertEqual(u['guess'], '', said)

    def test_pointing_at_the_screen_asks_for_the_name_in_any_app(self):
        u = understand('clica nesse aí', llm=llm_says(command='clicar no botão no Excel'))
        self.assertEqual(u['kind'], 'unclear')
        self.assertIn('nome do item', u['reply'])

    def test_settings_named_by_the_person_still_work(self):
        u = understand('abre as configurações de rede do Windows agora',
                       llm=llm_says(command='abrir configurações de rede'))
        self.assertEqual(u['kind'], 'command')

    def test_clear_named_click_still_works(self):
        u = understand('clica em salvar no Excel', llm=llm_says(command='clicar em salvar no Excel'))
        self.assertEqual(u['kind'], 'command')

    def test_low_confidence_in_live_mode_asks_before_acting(self):
        said = 'bota aquele negocio do relatorio ali'
        low = llm_says(command='abrir o relatório', confidence=0.5)
        u = understand(said, mode='live', llm=low)
        self.assertEqual((u['kind'], u['guess']), ('unclear', 'abrir o relatório'))
        self.assertEqual(understand(said, mode='record', llm=low)['kind'], 'command')

    def test_only_a_real_yes_confirms(self):
        for said in ('sim', 'pode', 'isso mesmo', 'pode sim'):
            self.assertTrue(confirms(said), said)
        for said in ('pode abrir a rede aurora', 'isso aí na rede aurora agora', 'não', ''):
            self.assertFalse(confirms(said), said)


if __name__ == '__main__':
    unittest.main()
