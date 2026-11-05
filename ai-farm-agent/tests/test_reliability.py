"""Offline regression fixtures. No API calls, microphone or desktop actions."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.brain import Brain
from core import memory_gate as gate
from core import artifact_qa as qa


def note(agent="DESKTOP", verified="nao"):
    return (f"---\ntipo: tarefa-referencia\nagente: {agent}\nverificado: {verified}\n"
            "keywords: calculadora\n---\n## Caminho\napp_search → wait\n")


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.vault = self.root / "vault"
        self.refs = self.vault / gate.REFS
        self.refs.mkdir(parents=True)
        self.archive = self.root / "archive"
        self.history = self.root / "history.jsonl"
        self.source = self.refs / "Calculadora.md"
        self.source.write_text(note(), encoding="utf-8")

    def test_missing_history_preserves_verified_note(self):
        self.source.write_text(note(verified="sim"), encoding="utf-8")
        before = self.source.read_bytes()
        gate.verify_all(self.vault, self.history, True, self.archive)
        self.assertEqual(before, self.source.read_bytes())

    def test_unproven_reference_stays_versionable(self):
        self.history.write_text("", encoding="utf-8")
        gate.verify_all(self.vault, self.history, True, self.archive)
        self.assertTrue(self.source.exists())
        self.assertFalse(self.archive.exists())

    def test_apply_is_idempotent_and_keeps_unmatched_notes(self):
        self.history.write_text(json.dumps({"task": "calculadora", "success": False,
                                "subtasks": [{"agent": "DESKTOP"}]}) + "\n", encoding="utf-8")
        gate.verify_all(self.vault, self.history, True, self.archive)
        first = self.source.read_bytes()
        gate.verify_all(self.vault, self.history, True, self.archive)
        self.assertEqual(first, self.source.read_bytes())

    def test_retrieval_filters_agent_before_top_k(self):
        self.source.write_text(note("WEB", "sim"), encoding="utf-8")
        (self.refs / "Calculadora Desktop.md").write_text(note("DESKTOP", "sim"), encoding="utf-8")
        refs = Brain(str(self.vault)).find_references("calculadora", k=1, agent="DESKTOP")
        self.assertEqual([r["agent"] for r in refs], ["DESKTOP"])

    def test_empty_procedure_is_not_a_reference(self):
        self.source.write_text(note(verified="sim").split("## Caminho")[0], encoding="utf-8")
        self.assertEqual(Brain(str(self.vault)).find_references("calculadora"), [])

    def test_restore_is_idempotent_and_never_overwrites(self):
        self.archive.mkdir()
        (self.archive / self.source.name).write_text("old copy", encoding="utf-8")
        (self.archive / "Outra.md").write_text(note(), encoding="utf-8")
        before = self.source.read_bytes()
        self.assertEqual(gate.restore_references(self.vault, self.archive), ["Outra.md"])
        self.assertEqual(gate.restore_references(self.vault, self.archive), [])
        self.assertEqual(before, self.source.read_bytes())
        self.assertTrue((self.archive / "Outra.md").exists())

    def test_unverified_and_wrong_agent_are_excluded(self):
        self.assertEqual(Brain(str(self.vault)).find_references("calculadora"), [])
        self.source.write_text(note("WEB", "sim"), encoding="utf-8")
        self.assertEqual(Brain(str(self.vault)).find_references("calculadora", agent="DESKTOP"), [])
        self.assertEqual(len(Brain(str(self.vault)).find_references("calculadora", agent="MAESTRO")), 1)


class SpreadsheetTests(unittest.TestCase):
    def test_single_pass_numbers(self):
        rows = iter([("Produto", "Valor"), ("A", 10), ("B", 20), ("C", 30)])
        self.assertIn("soma 60,00", "\n".join(qa._sheet_numbers(rows)))

    def test_scan_budget_and_close_on_failure(self):
        from types import SimpleNamespace
        def rows(**kwargs):
            for _ in range(qa.MAX_SCAN_ROWS + 1):
                yield ("A", 1)
            raise AssertionError("reader consumed past the scan budget")
        wb = SimpleNamespace(worksheets=[SimpleNamespace(title="Dados", iter_rows=rows)], close=lambda: None)
        with patch("openpyxl.load_workbook", return_value=wb), patch.object(wb, "close") as close:
            result = qa.read_file("example.xlsx")
            self.assertIn("PARCIAL", result)
            self.assertLessEqual(len(result), qa.MAX_CHARS)
            close.assert_called_once()

    def test_real_workbook_totals_and_preview(self):
        from openpyxl import Workbook
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "book.xlsx"
            wb = Workbook()
            ws = wb.active
            ws.append(["Item", "Valor"])
            for i in range(100):
                ws.append([f"Item {i}", 2])
            wb.save(path)
            wb.close()
            result = qa.read_file(str(path))
            self.assertIn("soma 200,00", result)
            self.assertNotIn("Item 99\t", result)

    def test_workbook_closes_when_iteration_raises(self):
        from types import SimpleNamespace
        wb = SimpleNamespace(worksheets=[SimpleNamespace(title="Dados", iter_rows=Mock(side_effect=OSError("broken")))], close=Mock())
        with patch("openpyxl.load_workbook", return_value=wb):
            with self.assertRaises(OSError):
                qa.read_file("example.xlsx")
        wb.close.assert_called_once()


class VoiceTests(unittest.TestCase):
    def test_uncertain_action_waits_for_yes_and_no_cancels(self):
        from desktop.voice import VoiceController
        from types import SimpleNamespace
        for answer, expected in [("sim", 1), ("nao", 0)]:
            with self.subTest(answer=answer):
                voice = VoiceController.__new__(VoiceController)
                voice._pending_guess, voice._asked, voice._recent = "", False, []
                voice.ctrl = SimpleNamespace(session=SimpleNamespace(empty=True, targets=lambda: {"explorer": 1}))
                voice._enqueue, voice._say = Mock(), Mock()
                voice.line = lambda *a, **k: "ok"
                unclear = lambda *a: {"kind": "unclear", "guess": "clicar na pasta Relatorios", "reply": "Qual pasta?"}
                voice.handle_text("na pasta...", confidence=0.2, understand_fn=unclear)
                voice._enqueue.assert_not_called()
                self.assertEqual(voice._pending_guess, "clicar na pasta Relatorios")
                voice.handle_text(answer)
                self.assertEqual(voice._enqueue.call_count, expected)
                self.assertEqual(voice._pending_guess, "")


if __name__ == "__main__":
    unittest.main()
