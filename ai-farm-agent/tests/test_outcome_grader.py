import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.outcome_grader import grade


class GraderTests(unittest.TestCase):
    def test_correct_incorrect_and_valid_alternative(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = {'expected_agents': ['CODE'], 'artifacts': [{'path': 'index.html', 'contains': '<h1>Example</h1>'}]}
            trace = {'agents': ['CODE'], 'status': 'succeeded', 'reply': 'done'}
            self.assertFalse(grade(case, trace, tmp)['outcome'])
            Path(tmp, 'index.html').write_text('<h1>Wrong</h1>', encoding='utf-8')
            self.assertFalse(grade(case, trace, tmp)['outcome'])
            Path(tmp, 'index.html').write_text('<html><h1>Example</h1></html>', encoding='utf-8')
            self.assertTrue(grade(case, trace, tmp)['outcome'])
            refusal = {'accepted_statuses': ['rejected', 'blocked'], 'artifacts': [{'path': 'forbidden.txt', 'absent': True}]}
            self.assertTrue(grade(refusal, {'status': 'blocked'}, tmp)['process'])
            self.assertTrue(grade(refusal, {'status': 'rejected'}, tmp)['outcome'])

    def test_no_escape_or_fluent_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(grade({}, {'status': 'succeeded', 'reply': 'all done'}, tmp)['outcome'])
            self.assertFalse(grade({'artifacts': [{'path': '../escape', 'absent': True}]}, {}, tmp)['outcome'])


if __name__ == '__main__':
    unittest.main()
