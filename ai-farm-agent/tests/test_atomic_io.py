import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.atomic_io import replace_file


class AtomicTests(unittest.TestCase):
    def test_transient_lock_recovers_with_bound(self):
        error = PermissionError('synthetic lock'); error.winerror = 32
        with patch('core.atomic_io.os.replace', side_effect=[error, error, None]) as replace, patch('core.atomic_io.time.sleep'):
            replace_file('source', 'destination')
            self.assertEqual(replace.call_count, 3)

    def test_persistent_error_is_not_hidden(self):
        error = PermissionError('synthetic lock'); error.winerror = 5
        with patch('core.atomic_io.os.replace', side_effect=error) as replace, patch('core.atomic_io.time.sleep'):
            with self.assertRaises(PermissionError): replace_file('source', 'destination', attempts=3)
            self.assertEqual(replace.call_count, 3)


if __name__ == '__main__': unittest.main()
