import json
import os
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
from core.task_ledger import TaskLedger, replay

ENV = {**os.environ, "PYTHONPATH": str(APP), "PYTHONIOENCODING": "utf-8"}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ledger = TaskLedger(Path(self.tmp.name))


class Recording(Base):
    def test_full_task_produces_every_required_field(self):
        ledger = self.ledger
        ledger.begin("t1", "abrir o bloco de notas", source="voz")
        ledger.plan("t1", ["abrir", "digitar"])
        ledger.step_started("t1", 1, "DESKTOP", "app_search", {"name": "x"}, "Abrir")
        ledger.step_finished("t1", 1, "app_search", {"success": True, "status": "succeeded", "verified": True, "result": "ok"})
        ledger.finish("t1", "completed", verified=True)
        task = ledger.load("t1")
        self.assertEqual((task["id"], task["state"], task["goal"]), ("t1", "completed", "abrir o bloco de notas"))
        self.assertEqual(task["steps_done"][0]["action"], "app_search")
        self.assertEqual(task["evidence"][0]["result"], "ok")
        self.assertTrue(task["verified"])
        self.assertEqual(task["steps_uncertain"], [])

    def test_failed_step_is_kept_apart_from_done(self):
        self.ledger.begin("t", "x")
        self.ledger.step_started("t", 1, "WEB", "open_url", {})
        self.ledger.step_finished("t", 1, "open_url", {"success": False, "result": "erro"})
        self.ledger.finish("t", "failed", error="erro")
        task = self.ledger.load("t")
        self.assertEqual(task["steps_done"], [])
        self.assertEqual(task["steps_failed"][0]["action"], "open_url")

    def test_parameter_values_never_reach_the_disk(self):
        self.ledger.begin("t", "x")
        self.ledger.step_started("t", 1, "DESKTOP", "type_text", {"text": "senha-secreta-123"}, "Digitar")
        raw = (Path(self.tmp.name) / "t.jsonl").read_text(encoding="utf-8")
        self.assertNotIn("senha-secreta-123", raw)
        self.assertIn('"text"', raw)

    def test_step_is_on_disk_before_the_action_runs(self):
        self.ledger.begin("t", "x")
        self.ledger.step_started("t", 1, "DESKTOP", "hotkey", {})
        self.assertEqual(self.ledger.load("t")["steps_uncertain"][0]["action"], "hotkey")

    def test_results_are_bounded(self):
        self.ledger.begin("t", "x")
        self.ledger.step_started("t", 1, "WEB", "browser_read", {})
        self.ledger.step_finished("t", 1, "browser_read", {"success": True, "result": "y" * 5000})
        self.assertLessEqual(len(self.ledger.load("t")["evidence"][0]["result"]), 240)

    def test_interruptions_are_recorded_without_ending_the_task(self):
        self.ledger.begin("t", "x")
        self.ledger.note("t", "interruption", reason="pessoa falou por cima")
        task = self.ledger.load("t")
        self.assertEqual(task["state"], "running")
        self.assertEqual(task["interruptions"][0]["reason"], "pessoa falou por cima")

    def test_ledger_failure_never_breaks_the_task(self):
        blocker = Path(self.tmp.name) / "arquivo"
        blocker.write_text("x")
        broken = TaskLedger(blocker / "sub")
        broken.begin("t", "x")
        broken.step_started("t", 1, "WEB", "wait", {})
        broken.finish("t", "failed")
        self.assertEqual(broken.events("t"), [])

    def test_disabled_ledger_writes_nothing(self):
        off = TaskLedger(Path(self.tmp.name) / "off", enabled=False)
        off.begin("t", "x")
        self.assertFalse((Path(self.tmp.name) / "off").exists())
        self.assertEqual(off.recover(), [])

    def test_concurrent_writes_keep_every_event_whole(self):
        self.ledger.begin("t", "x")
        threads = [threading.Thread(target=lambda n=n: self.ledger.progress("t", 1, f"m{n}")) for n in range(30)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        events = self.ledger.events("t")
        self.assertEqual(len(events), 31)
        self.assertEqual(sorted(e["seq"] for e in events), list(range(1, 32)))


class Recovery(Base):
    def test_cut_last_line_does_not_lose_the_earlier_events(self):
        self.ledger.begin("t", "x")
        self.ledger.step_started("t", 1, "DESKTOP", "hotkey", {})
        with (Path(self.tmp.name) / "t.jsonl").open("a", encoding="utf-8") as stream:
            stream.write('{"seq": 3, "type": "step_fin')
        task = self.ledger.load("t")
        self.assertEqual(task["goal"], "x")
        self.assertEqual(task["steps_uncertain"][0]["action"], "hotkey")

    def test_dead_process_task_becomes_interrupted_with_uncertain_step(self):
        self.ledger.begin("t", "enviar relatorio")
        self.ledger.plan("t", ["abrir", "enviar", "fechar"])
        self.ledger.step_started("t", 1, "DESKTOP", "app_task", {"goal": "x"}, "Enviar")
        lines = (Path(self.tmp.name) / "t.jsonl").read_text(encoding="utf-8").splitlines()
        first = json.loads(lines[0])
        first["pid"] = 999999
        lines[0] = json.dumps(first)
        (Path(self.tmp.name) / "t.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
        with patch("core.task_ledger._pid_alive", return_value=False):
            found = TaskLedger(Path(self.tmp.name)).recover()
        self.assertEqual(len(found), 1)
        task = found[0]
        self.assertEqual(task["state"], "interrupted")
        self.assertEqual(task["steps_uncertain"][0]["action"], "app_task")
        self.assertEqual(task["steps_pending"], ["enviar", "fechar"])
        self.assertTrue(task["interruptions"])

    def test_recovery_marks_once(self):
        self.ledger.begin("t", "x")
        with patch("core.task_ledger.os.getpid", return_value=1), patch("core.task_ledger._pid_alive", return_value=False):
            self.assertEqual(len(self.ledger.recover()), 1)
            self.assertEqual(self.ledger.recover(), [])

    def test_task_of_a_living_process_is_left_alone(self):
        self.ledger.begin("t", "x")
        with patch("core.task_ledger.os.getpid", return_value=1), patch("core.task_ledger._pid_alive", return_value=True):
            self.assertEqual(self.ledger.recover(), [])
        self.assertEqual(self.ledger.load("t")["state"], "running")

    def test_finished_tasks_are_not_touched(self):
        self.ledger.begin("t", "x")
        self.ledger.finish("t", "completed")
        self.assertEqual(self.ledger.recover(), [])

    def test_old_tasks_are_pruned(self):
        for n in range(5):
            self.ledger.begin(f"t{n}", "x")
            self.ledger.finish(f"t{n}", "completed")
            os.utime(Path(self.tmp.name) / f"t{n}.jsonl", (n + 1, n + 1))
        self.assertEqual(self.ledger.prune(keep=2), 3)
        self.assertEqual(self.ledger.task_ids(), ["t3", "t4"])

    def test_real_process_killed_mid_action_leaves_a_recoverable_task(self):
        # O caso real: o processo morre com o passo em andamento, e nada e repetido
        script = textwrap.dedent("""
            import sys, time
            from pathlib import Path
            from core.task_ledger import TaskLedger
            ledger = TaskLedger(Path(sys.argv[1]))
            ledger.begin('real', 'enviar mensagem')
            ledger.plan('real', ['abrir', 'enviar'])
            ledger.step_started('real', 1, 'DESKTOP', 'app_search', {}, 'abrir')
            ledger.step_finished('real', 1, 'app_search', {'success': True, 'verified': True, 'result': 'ok'})
            ledger.step_started('real', 2, 'DESKTOP', 'app_task', {'goal': 'x'}, 'enviar')
            print('pronto', flush=True)
            time.sleep(60)
        """)
        process = subprocess.Popen([sys.executable, "-c", script, self.tmp.name], stdout=subprocess.PIPE, text=True, env=ENV, cwd=APP)
        self.assertEqual(process.stdout.readline().strip(), "pronto")
        process.kill()
        process.wait(5)
        process.stdout.close()
        # O python.exe do venv e um lancador: o processo que grava morre um instante depois dele
        found, end = [], time.monotonic() + 8
        while not found and time.monotonic() < end:
            found = TaskLedger(Path(self.tmp.name)).recover()
            time.sleep(0.05)
        self.assertEqual([t["id"] for t in found], ["real"])
        task = found[0]
        self.assertEqual([s["action"] for s in task["steps_done"]], ["app_search"])
        self.assertEqual([s["action"] for s in task["steps_uncertain"]], ["app_task"])


class ControllerIntegration(unittest.TestCase):
    """O _run de verdade com agentes falsos: os eventos saem nos pontos certos, sem mudar a execucao."""

    def run_task(self, results, ledger, cancel_at=None, retryable=False):
        from desktop.controller import Controller
        c = Controller.__new__(Controller)
        c.state = {"running": True}
        c._lock = threading.Lock()
        c._run_id = 1
        c._tls = threading.local()
        c._cancel_event = threading.Event()
        c._plan_gate = threading.Event()
        c._plan_ok, c._plan_token = False, ""
        c._voice_hints = {}
        c._ai_client = Mock(metrics={})
        c._config = Mock(get=lambda key, default=None: default)
        c._brain = Mock(last_skills={}, write_plan=Mock(return_value=None), context_for=Mock(return_value=""))
        c.capture = Mock()
        c.memory = Mock()
        c.narrator = Mock()
        from core.session import Session
        c.session = Session()
        c.session.save = lambda *a, **k: None
        c._ContextManager = lambda: Mock(prepare_subtask=lambda s, i: s, extract_from_results=Mock(return_value={}),
                                         after_subtask=Mock(), has_folder=False)
        action = "vision_click" if retryable else "wait"
        agent = Mock(spec=["plan"])
        agent.plan.return_value = {"steps": [{"action": action, "params": {"seconds": 0}, "description": f"passo {i}"}
                                             for i in range(len(results))]}
        c.agents = {"DESKTOP": agent}
        c.maestro = Mock(analyze=Mock(return_value={"analysis": "a", "skills": [], "subtasks": [
            {"agent": "DESKTOP", "task": "fazer", "params": {}, "original_task": "fazer"}]}))
        sequence = iter(results)

        def execute(a, p, dry_run=False):
            result = next(sequence)
            if cancel_at == "during":
                c._cancel_event.set()
            return {"action": a, "params": p, **result}
        c.engine = Mock(execute=Mock(side_effect=execute), workspace={}, last_say="")
        c.engine.vision = Mock()
        c._after_turn = Mock()
        c._metrics_delta = lambda before, after: {}
        c._emit_usage = lambda: None
        with patch("core.task_ledger.get_ledger", return_value=ledger), patch("desktop.controller.history_store.append"), \
                patch("core.plan_validator.validate_steps", return_value=Mock(approved=True)), \
                patch("core.followup.resolve", return_value={"task": "fazer", "kind": "new", "target": None}), \
                patch("core.followup.from_hint", return_value=None), \
                patch("agents.maestro.vault_plan", return_value=None), patch("agents.maestro.continue_plan", return_value=None), \
                patch("core.user_settings.load", return_value={"plan_review": False}), patch("time.sleep"),                 patch("core.action_logger.log_action"):
            c._run("fazer", False, False, 1)
        return c

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ledger = TaskLedger(Path(self.tmp.name))

    def only_task(self):
        ids = self.ledger.task_ids()
        self.assertEqual(len(ids), 1)
        return self.ledger.load(ids[0])

    def test_successful_task_is_recorded_from_start_to_end(self):
        self.run_task([{"success": True, "verified": True, "status": "succeeded", "result": "ok"}], self.ledger)
        task = self.only_task()
        self.assertEqual((task["state"], task["goal"]), ("completed", "fazer"))
        self.assertEqual(len(task["steps_done"]), 1)
        self.assertTrue(task["verified"])

    def test_unverified_success_stays_visible_as_unverified(self):
        self.run_task([{"success": True, "verified": False, "status": "succeeded", "result": "ok"}], self.ledger)
        task = self.only_task()
        self.assertEqual(task["state"], "completed")
        self.assertFalse(task["verified"])

    def test_failed_step_ends_as_failed_with_the_reason(self):
        self.run_task([{"success": False, "status": "failed", "result": "❌ sem janela"}], self.ledger)
        task = self.only_task()
        self.assertEqual(task["state"], "failed")
        self.assertEqual(len(task["steps_failed"]), 1)

    def test_cancelled_task_is_recorded_as_cancelled(self):
        self.run_task([{"success": True, "verified": True, "status": "succeeded", "result": "ok"},
                       {"success": True, "verified": True, "status": "succeeded", "result": "ok"}], self.ledger, cancel_at="during")
        self.assertEqual(self.only_task()["state"], "cancelled")

    def test_automatic_retry_is_visible(self):
        self.run_task([{"success": False, "status": "failed", "result": "❌ nao achei"},
                       {"success": True, "verified": False, "status": "succeeded", "result": "ok"}], self.ledger, retryable=True)
        kinds = [e["type"] for e in self.ledger.events(self.ledger.task_ids()[0])]
        self.assertIn("step_retry", kinds)

    def test_history_entry_points_to_the_same_task(self):
        with patch("desktop.controller.history_store.new_execution", wraps=__import__("desktop.history_store", fromlist=["x"]).new_execution) as new:
            self.run_task([{"success": True, "verified": True, "status": "succeeded", "result": "ok"}], self.ledger)
        self.assertTrue(new.called)
        self.assertEqual(self.ledger.load(self.ledger.task_ids()[0])["id"], self.ledger.task_ids()[0])

    def test_broken_ledger_does_not_change_the_result(self):
        class Broken(TaskLedger):
            def _write(self, task_id, event):
                raise RuntimeError("disco cheio")
        c = self.run_task([{"success": True, "verified": True, "status": "succeeded", "result": "ok"}], Broken(Path(self.tmp.name)))
        c.engine.execute.assert_called_once()
        c._after_turn.assert_called_once()


if __name__ == "__main__":
    unittest.main()
