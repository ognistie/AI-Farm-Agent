"""Ciclo de vida do app com processos de verdade, sem janela visivel (Qt offscreen)."""
import os
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path
from unittest.mock import Mock

import psutil

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))

ENV = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "PYTHONIOENCODING": "utf-8", "PYTHONPATH": str(APP)}


def gone(pid, seconds):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if not psutil.pid_exists(pid):
            return True
        time.sleep(0.05)
    return not psutil.pid_exists(pid)


class Launcher(unittest.TestCase):
    def test_killing_the_launcher_kills_the_real_app(self):
        # O caso do VS Code: encerrar quem abriu nao pode deixar o agente vivo
        launcher = textwrap.dedent("""
            import subprocess, sys, importlib.util
            spec = importlib.util.spec_from_file_location('app_main', r'%s')
            module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
            child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
            job = module.tie_to_this_process(child)
            print(child.pid, flush=True)
            child.wait()
        """ % (APP / 'main.py'))
        parent = subprocess.Popen([sys.executable, '-c', launcher], stdout=subprocess.PIPE, text=True, env=ENV)
        child_pid = int(parent.stdout.readline())
        self.assertTrue(psutil.pid_exists(child_pid))
        parent.kill()
        parent.wait(5)
        self.assertTrue(gone(child_pid, 5), 'o processo filho sobreviveu ao lancador')

    def test_console_and_no_console_launchers_use_the_project_environment(self):
        source = (APP / 'main.py').read_text(encoding='utf-8')
        self.assertNotIn('os.execv(', source)
        self.assertIn('pythonw.exe', source)


class Instance(unittest.TestCase):
    SCRIPT = textwrap.dedent("""
        import sys
        from PySide6.QtCore import QCoreApplication, QTimer
        from desktop.instance import InstanceServer, notify_running
        name = sys.argv[1]
        app = QCoreApplication(sys.argv[:1])
        calls = []
        print('before', notify_running(name), flush=True)
        server = InstanceServer(lambda: calls.append(1), name=name, parent=app)
        print('listening', server.listening, flush=True)
        import subprocess
        second = subprocess.Popen([sys.executable, '-c', 'import sys; from PySide6.QtCore import QCoreApplication; '
                                   'from desktop.instance import notify_running; a = QCoreApplication(sys.argv[:1]); '
                                   'print(notify_running(sys.argv[1]))', name], stdout=subprocess.PIPE, text=True)
        def finish():
            if calls or second.poll() is not None and timer_ticks[0] > 20:
                print('second', second.communicate()[0].strip(), 'shown', len(calls), flush=True)
                app.quit()
            timer_ticks[0] += 1
        timer_ticks = [0]
        timer = QTimer(); timer.timeout.connect(finish); timer.start(100)
        QTimer.singleShot(15000, app.quit)
        app.exec()
    """)

    def test_second_launch_shows_the_first_and_does_not_start(self):
        name = f"aifarm-test-{os.getpid()}"
        out = subprocess.run([sys.executable, '-c', self.SCRIPT, name], capture_output=True, text=True, env=ENV,
                             cwd=APP, timeout=40).stdout
        self.assertIn('before False', out)
        self.assertIn('listening True', out)
        self.assertIn('second True shown 1', out)


class Closing(unittest.TestCase):
    """O app inteiro: fechar a janela encerra, mesmo com algo preso segurando o processo."""

    DRIVER = textwrap.dedent("""
        import os, sys, threading, time
        from pathlib import Path
        sys.argv = ['main.py']
        import importlib.util
        spec = importlib.util.spec_from_file_location('app_main', r'%(main)s')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        os.environ.setdefault('ANTHROPIC_API_KEY', 'sk-ant-api-test')
        from core.voice import hotkey
        hotkey.GlobalHotkey.start_and_wait = lambda self, timeout=2.0: False    # nao registra atalho de verdade
        from desktop import instance
        instance.SERVER_NAME = %(name)r
        instance.notify_running.__defaults__ = (%(name)r,)
        instance.InstanceServer.__init__.__kwdefaults__ = None
        import desktop.main as desktop_main
        original = desktop_main.InstanceServer
        desktop_main.InstanceServer = lambda on_show, parent=None: original(on_show, name=%(name)r, parent=parent)
        desktop_main.Bridge.splash_enabled = lambda self: False
        from desktop.controller import Controller
        Controller.execute_task = lambda *a, **k: None
        # Simula o que travava: uma thread que nao e daemon e nao termina nunca
        threading.Thread(target=lambda: time.sleep(600), daemon=False).start()
        from PySide6.QtCore import QTimer
        from PySide6.QtGui import QGuiApplication
        real_exec = QGuiApplication.exec
        def run_then_close(*args):
            def close():
                for window in QGuiApplication.topLevelWindows():
                    if window.title() == 'AI Farm Agent' and window.objectName() not in ('splashWindow', 'miniChat'):
                        print('closing', flush=True)
                        window.close()
                        return
            QTimer.singleShot(800, close)
            return real_exec()
        QGuiApplication.exec = run_then_close
        code = module.main()
        print('exec returned', code, flush=True)
        module._finish(code)
    """)

    def run_driver(self, timeout=40):
        name = f"aifarm-close-{os.getpid()}-{time.monotonic_ns()}"
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / 'driver.py'
            script.write_text(self.DRIVER % {'main': APP / 'main.py', 'name': name}, encoding='utf-8')
            started = time.monotonic()
            process = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, env=ENV,
                                     cwd=APP, timeout=timeout, encoding='utf-8', errors='replace')
        return process, time.monotonic() - started

    def test_closing_the_window_ends_the_process_even_with_a_stuck_thread(self):
        process, _ = self.run_driver()
        self.assertIn('closing', process.stdout, process.stderr[-800:])
        self.assertIn('exec returned 0', process.stdout, process.stderr[-800:])
        self.assertEqual(process.returncode, 0)


class BridgeShutdown(unittest.TestCase):
    def bridge(self, running=True, voice=True):
        from desktop.bridge import Bridge
        bridge = Bridge.__new__(Bridge)
        bridge._stop_hotkey, bridge._quick_hotkey = Mock(), Mock()
        bridge._controller = Mock(state={'running': running})
        bridge._voice = Mock() if voice else None
        return bridge

    def test_stops_hotkeys_task_and_voice(self):
        bridge = self.bridge()
        bridge.shutdown()
        bridge._stop_hotkey.stop.assert_called_once()
        bridge._quick_hotkey.stop.assert_called_once()
        bridge._controller.force_stop.assert_called_once()
        bridge._voice.shutdown.assert_called_once()

    def test_idle_app_without_voice_closes_cleanly(self):
        bridge = self.bridge(running=False, voice=False)
        bridge.shutdown()
        bridge._controller.force_stop.assert_not_called()


class Shortcut(unittest.TestCase):
    def test_icon_file_is_valid_and_has_taskbar_sizes(self):
        script = textwrap.dedent("""
            import struct, sys
            from pathlib import Path
            sys.path.insert(0, r'%s')
            from install_shortcuts import write_icon
            path = write_icon(Path(sys.argv[1]))
            data = path.read_bytes()
            reserved, kind, count = struct.unpack('<HHH', data[:6])
            sizes = [data[6 + 16 * i] or 256 for i in range(count)]
            print(reserved, kind, sizes)
        """ % (APP / 'scripts'))
        with tempfile.TemporaryDirectory() as tmp:
            out = subprocess.run([sys.executable, '-c', script, str(Path(tmp) / 'a.ico')], capture_output=True,
                                 text=True, env=ENV, cwd=APP, timeout=40)
        self.assertIn('0 1 [16, 24, 32, 48, 64, 256]', out.stdout, out.stderr[-600:])

    def test_shortcut_carries_the_same_identity_as_the_window(self):
        sys.path.insert(0, str(APP / 'scripts'))
        import install_shortcuts as shortcuts
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from desktop.main import APP_ID
        with tempfile.TemporaryDirectory() as tmp:
            link = Path(tmp) / 'teste.lnk'
            shortcuts.write_shortcut(link, APP_ID)
            saved = shortcuts.read_shortcut(link)
        self.assertEqual(saved['app_id'], APP_ID)
        self.assertEqual(Path(saved['target']).name.lower(), 'pythonw.exe')
        self.assertIn('main.py', saved['arguments'])
        self.assertTrue(saved['icon'].endswith('.ico'))


if __name__ == '__main__':
    unittest.main()
