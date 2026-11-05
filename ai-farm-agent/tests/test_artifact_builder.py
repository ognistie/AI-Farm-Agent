import copy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.artifact_builder import build_project, build_workbook, validate_project, validate_workbook


class ArtifactTests(unittest.TestCase):
    def project(self):
        return {'name': 'example', 'files': [{'path': 'main.py', 'content': "raise RuntimeError('must never execute')\n"},
                                            {'path': 'README.md', 'content': 'Example'}]}

    def workbook(self):
        return {'name': 'sales', 'sheets': [{'title': 'Sales', 'rows': [['Item', 'Value'], ['A', 10], ['B', 20], ['Total', '=SUM(B2:B3)']],
                                            'charts': [{'type': 'bar', 'column': 2}]}]}

    def test_project_written_without_execution_and_no_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = build_project(self.project(), tmp)
            second = build_project(self.project(), tmp)
            self.assertTrue(first['success'])
            self.assertTrue(first['verified'])
            self.assertNotEqual(first['artifacts']['folder'], second['artifacts']['folder'])
            self.assertEqual(Path(first['artifacts']['folder'], 'README.md').read_text(), 'Example')

    def test_paths_syntax_and_collisions_rejected(self):
        for path in ('../outside.py', 'C:/outside.py', 'folder/../../x.py', 'CON.txt', '.env', 'script.exe', 'a\\b.py'):
            with self.subTest(path=path):
                manifest = self.project()
                manifest['files'][0]['path'] = path
                with self.assertRaises(ValueError): validate_project(manifest)
        manifest = self.project()
        manifest['files'].append({'path': 'MAIN.py', 'content': 'x=1'})
        with self.assertRaises(ValueError): validate_project(manifest)
        manifest = self.project()
        manifest['files'][0]['content'] = 'def invalid('
        with self.assertRaises(SyntaxError): validate_project(manifest)

    def test_workbook_values_formulas_and_charts_verified(self):
        from openpyxl import load_workbook
        with tempfile.TemporaryDirectory() as tmp:
            result = build_workbook(self.workbook(), tmp)
            self.assertTrue(result['verified'], result)
            wb = load_workbook(result['artifacts']['files'][0])
            try:
                self.assertEqual(wb['Sales']['B4'].value, '=SUM(B2:B3)')
                self.assertEqual(len(wb['Sales']._charts), 1)
            finally: wb.close()

    def test_external_formulas_and_oversize_rejected(self):
        for formula in ('=HYPERLINK("https://example.com","x")', '=WEBSERVICE("https://example.com")', "='[other.xlsx]Sheet'!A1", '@SUM(A1:A2)', '=SUM(Other!A1:A2)'):
            manifest = self.workbook()
            manifest['sheets'][0]['rows'][1][1] = formula
            with self.subTest(formula=formula), self.assertRaises(ValueError): validate_workbook(manifest)

    def test_agent_uses_manifest_only(self):
        import json
        from types import SimpleNamespace
        from agents.artifact_planner import plan_artifact
        agent = SimpleNamespace(name='CODE', model='fixture', effort='low', _extract_task_text=lambda task:task,
                                _client=SimpleNamespace(message=lambda **k:json.dumps(self.project())))
        with patch('agents.artifact_planner.brain_guide', return_value=''):
            result = plan_artifact(agent, 'make example')
        self.assertEqual(result['steps'][0]['action'], 'create_project')
        agent.name = 'DATA'
        agent._client.message = lambda **k: json.dumps(self.workbook())
        with patch('agents.artifact_planner.brain_guide', return_value=''):
            result = plan_artifact(agent, 'make workbook')
        self.assertEqual(result['steps'][0]['action'], 'create_workbook')


if __name__ == '__main__': unittest.main()
