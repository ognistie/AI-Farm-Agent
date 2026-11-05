import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.project_versions import apply_edit, read_project, revert_last, validate_edit


class TransactionTests(unittest.TestCase):
    def test_stale_snapshot_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp, 'a.txt'); file.write_text('old')
            snapshot = read_project(tmp)
            file.write_text('user edited')
            result = apply_edit(tmp, [{'path':'a.txt','content':'new'}], snapshot['hashes'])
            self.assertFalse(result['ok'])
            self.assertEqual(file.read_text(), 'user edited')

    def test_failure_rolls_back_first_file(self):
        import os
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, 'a.txt').write_text('old a')
            Path(tmp, 'b.txt').write_text('old b')
            replace = os.replace
            calls = []
            def fail_second(source, target):
                calls.append(target)
                if len(calls) == 2: raise OSError('synthetic write failure')
                return replace(source, target)
            with patch('core.project_versions.os.replace', side_effect=fail_second):
                result = apply_edit(tmp, [{'path':'a.txt','content':'new a'}, {'path':'b.txt','content':'new b'}])
            self.assertFalse(result['ok'])
            self.assertEqual(Path(tmp, 'a.txt').read_text(), 'old a')
            self.assertEqual(Path(tmp, 'b.txt').read_text(), 'old b')

    def test_two_fast_edits_undo_in_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp, 'a.txt');file.write_text('one')
            first=apply_edit(tmp,[{'path':'a.txt','content':'two'}])
            second=apply_edit(tmp,[{'path':'a.txt','content':'three'}])
            self.assertNotEqual(first['version'], second['version'])
            self.assertTrue(revert_last(tmp)['ok'])
            self.assertEqual(file.read_text(), 'two')
            self.assertTrue(revert_last(tmp)['ok'])
            self.assertEqual(file.read_text(), 'one')

    def test_secrets_invalid_syntax_and_duplicates_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            for files in ([{'path':'.env','content':'secret'}], [{'path':'x.py','content':'def x('}],
                          [{'path':'a.txt','content':'1'}, {'path':'a.txt','content':'2'}]):
                self.assertTrue(validate_edit(tmp,files))

    def test_undo_preserves_user_changes_to_existing_and_created_files(self):
        for existing in (True, False):
            with self.subTest(existing=existing), tempfile.TemporaryDirectory() as tmp:
                file = Path(tmp, 'a.txt')
                if existing: file.write_text('before')
                self.assertTrue(apply_edit(tmp, [{'path': 'a.txt', 'content': 'agent'}])['ok'])
                file.write_text('later user work')
                self.assertFalse(revert_last(tmp)['ok'])
                self.assertEqual(file.read_text(), 'later user work')

    def test_undo_rejects_corrupt_backup_before_any_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp, 'a.txt'); file.write_text('before')
            version = apply_edit(tmp, [{'path': 'a.txt', 'content': 'agent'}, {'path': 'b.txt', 'content': 'new'}])['version']
            Path(tmp, '.ai_versions', version, 'a.txt').write_text('corrupt')
            self.assertFalse(revert_last(tmp)['ok'])
            self.assertEqual(file.read_text(), 'agent')
            self.assertEqual(Path(tmp, 'b.txt').read_text(), 'new')

    def test_undo_failure_restores_current_files(self):
        import os
        with tempfile.TemporaryDirectory() as tmp:
            for name in ('a.txt', 'b.txt'): Path(tmp, name).write_text('before')
            apply_edit(tmp, [{'path': name, 'content': 'agent'} for name in ('a.txt', 'b.txt')])
            replace = os.replace
            calls = []
            def fail_second(source, target):
                calls.append(target)
                if len(calls) == 2: raise OSError('synthetic undo failure')
                return replace(source, target)
            with patch('core.project_versions.os.replace', side_effect=fail_second):
                self.assertFalse(revert_last(tmp)['ok'])
            for name in ('a.txt', 'b.txt'): self.assertEqual(Path(tmp, name).read_text(), 'agent')


if __name__ == '__main__': unittest.main()
