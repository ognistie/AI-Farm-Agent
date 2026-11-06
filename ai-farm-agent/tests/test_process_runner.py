import json
import os
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import process_runner
from core.process_runner import run_python, run_command


class ProcessTests(unittest.TestCase):
    def test_python_workspace_cwd_and_failure(self):
        before = os.getcwd()
        result = run_python("workspace['answer']=42\nprint('hello')")
        self.assertTrue(result['success'], result)
        self.assertEqual(result['workspace']['answer'], 42)
        self.assertIn('hello', result['result'])
        self.assertEqual(before, os.getcwd())
        self.assertFalse(result['verified'])
        self.assertFalse(run_python("raise ValueError('fixture')")['success'])

    def test_command_exit_status(self):
        result = run_command(f'"{sys.executable}" -c "import sys; sys.exit(7)"')
        self.assertFalse(result['success'], result)
        self.assertEqual(result['exit_code'], 7)

    def test_timeout_and_cancel(self):
        self.assertEqual(run_python('import time; time.sleep(60)', timeout=0.25)['status'], 'timeout')
        stop = threading.Event()
        timer = threading.Timer(0.3, stop.set)
        timer.start()
        try:
            result = run_python('import time; time.sleep(60)', should_stop=stop.is_set)
            self.assertEqual(result['status'], 'cancelled')
        finally:
            timer.cancel()

    def _assert_cancel_kills_descendant(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / 'descendant.txt'
            gate = Path(tmp) / 'after_cleanup'
            ready = Path(tmp) / 'child_ready'
            # Must outlive the runner's 10 s pipe wait: a survivor that left by itself first would pass unnoticed.
            child = (f"import time; from pathlib import Path; Path({str(ready)!r}).write_text('ready')\n"
                     f"deadline=time.monotonic()+40\nwhile not Path({str(gate)!r}).exists() and time.monotonic()<deadline: time.sleep(.02)\n"
                     f"if Path({str(gate)!r}).exists(): Path({str(marker)!r}).write_text('escaped')")
            code = f"import subprocess, sys, time\nsubprocess.Popen([sys.executable,'-c',{child!r}])\nprint('started',flush=True)\ntime.sleep(60)"
            try:
                result = run_python(code, timeout=30, should_stop=ready.exists)
            finally:
                gate.touch()  # any write from now on proves a survivor, independent of scheduler speed
                time.sleep(0.5)
            self.assertTrue(ready.exists(), 'fixture child did not start')
            self.assertEqual(result['status'], 'cancelled', result)
            self.assertFalse(marker.exists(), 'descendant survived process cleanup')

    def test_cancel_kills_descendant(self):
        self._assert_cancel_kills_descendant()

    @unittest.skipUnless(os.name == 'nt', 'Windows Job Objects')
    def test_slow_job_setup_does_not_leak_descendant(self):
        # Under load the venv launcher used to start the interpreter before the job was assigned.
        attach = process_runner._attach_job

        def slow_attach(process):
            time.sleep(0.5)
            return attach(process)

        with patch.object(process_runner, '_attach_job', slow_attach):
            self._assert_cancel_kills_descendant()

    @unittest.skipUnless(os.name == 'nt', 'Windows Job Objects')
    def test_job_setup_failure_stops_suspended_process(self):
        with patch.object(process_runner, '_attach_job', side_effect=OSError('fixture')):
            result = run_python("print('never')", timeout=5)
        self.assertEqual(result['status'], 'failed', result)
        self.assertIn('fixture', result['result'])

    def test_output_limit(self):
        result = run_python("while True: print('x'*4096)", timeout=5)
        self.assertEqual(result['status'], 'output_limit', result)
        self.assertLessEqual(len(result['result']), 8000)

    def test_worker_does_not_inherit_provider_secret(self):
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'synthetic-secret'}):
            result = run_python("import os; workspace['key']=os.getenv('ANTHROPIC_API_KEY')")
        self.assertTrue(result['success'], result)
        self.assertIsNone(result['workspace']['key'])


if __name__ == '__main__':
    unittest.main()
