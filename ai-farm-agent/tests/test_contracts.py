import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.file_contracts import validate
from core.plan_validator import validate_plan, validate_steps
from core import memory_gate


class ContractsTests(unittest.TestCase):
    def test_file_rejects_code_aliases_and_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(validate([{'action': 'run_python', 'params': {'code': "from os import remove as erase; erase('x')"}}], [tmp]))
            self.assertTrue(validate([{'action': 'delete_file', 'params': {'path': str(Path(tmp) / 'x')}}], [tmp]))
            self.assertFalse(validate([{'action': 'delete_file', 'params': {'path': str(Path(tmp) / 'x')}}], [tmp], True))
            self.assertTrue(validate([{'action': 'read_file', 'params': {'path': str(Path(tmp).parent / 'outside')}}], [tmp]))
            self.assertTrue(validate([{'action': 'move_file', 'params': {'source': tmp, 'destination': str(Path(tmp)/'x')}}], [tmp]))

    def test_negative_confirmation(self):
        from agents.file_agent import _has_explicit_confirmation
        self.assertFalse(_has_explicit_confirmation('nao confirmo a exclusao'))
        self.assertTrue(_has_explicit_confirmation('confirmo a exclusao'))

    def test_bad_dependencies_and_params(self):
        for dependency in (True, 0, 2, '1'):
            self.assertFalse(validate_plan('task', {'subtasks': [{'agent': 'CODE', 'depends_on': dependency}]}).approved)
        self.assertFalse(validate_plan('task', {'subtasks': [{'agent': 'CODE', 'params': []}]}).approved)
        self.assertFalse(validate_steps('WEB', {}, [{'action': 'run_python', 'params': {}}], 'task').approved)

    def test_success_without_procedure_evidence_does_not_promote(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            refs = root / memory_gate.REFS
            refs.mkdir()
            note = refs / 'Calculadora.md'
            note.write_text('---\ntipo: tarefa-referencia\nagente: DESKTOP\nkeywords: calculadora\nverificado: nao\n---\n## Caminho\nopen\n', encoding='utf-8')
            before = note.read_bytes()
            entry = {'task': 'calculadora', 'success': True, 'subtasks': [{'agent': 'DESKTOP'}]}
            self.assertIsNone(memory_gate.record_outcome(root, entry, root/'archive'))
            self.assertEqual(note.read_bytes(), before)
            entry['reference_evidence'] = [{'note': 'Calculadora.md', 'verified': True, 'verifier': 'uia'}]
            self.assertIsNotNone(memory_gate.record_outcome(root, entry, root/'archive'))
            self.assertIn('verificado: sim', note.read_text(encoding='utf-8'))

    def test_file_agent_produces_tools_without_python(self):
        import logging
        from types import SimpleNamespace
        from agents.file_agent import FileAgent, BASE_PROMPT
        with tempfile.TemporaryDirectory() as tmp:
            agent = FileAgent.__new__(FileAgent)
            agent._allowed_roots, agent._allow_delete = [tmp], False
            agent.system_prompt, agent.model, agent.effort, agent.name = BASE_PROMPT, 'fixture', 'low', 'FILE'
            agent._client = SimpleNamespace(message=lambda **k: __import__('json').dumps(
                {'steps': [{'action': 'list_files', 'params': {'path': tmp}}]}))
            result = agent._call_and_validate('listar', None)
            self.assertTrue(result['ok'], result)
            self.assertEqual(result['steps'][0]['action'], 'list_files')
            agent._client = SimpleNamespace(message=lambda **k: '{"steps":[{"code":"print(1)"}]}')
            self.assertFalse(agent._call_and_validate('listar', None)['ok'])


if __name__ == '__main__':
    unittest.main()
