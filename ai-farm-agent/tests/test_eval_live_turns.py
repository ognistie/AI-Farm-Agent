import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
spec = importlib.util.spec_from_file_location("eval_live_turns", APP / "scripts" / "eval_live_turns.py")
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)


def trace(voice, said=((1.0, 2.0),), pauses=(), **fields):
    return {"voice": list(voice), "said": list(said), "pauses": list(pauses), "expect_delegation": None,
            "delegated_at": None, "usage_s": 5.0, **fields}


class Grading(unittest.TestCase):
    def test_voice_chunks_with_short_gaps_are_one_speech(self):
        self.assertEqual(evaluation.merge_voice([(1.0, 1.1), (1.2, 1.3), (3.0, 3.1)]), [[1.0, 1.3], [3.0, 3.1]])

    def test_response_after_speech_is_measured(self):
        out = evaluation.grade(trace([(3.2, 5.0)]))
        self.assertTrue(out["responded"])
        self.assertEqual(out["first_voice_s"], 1.2)
        self.assertIsNone(out["interrupted_pause"])

    def test_short_answer_after_the_speech_is_a_response(self):
        out = evaluation.grade(trace([(3.0, 3.4)]))
        self.assertTrue(out["responded"])
        self.assertEqual(out["first_voice_s"], 1.0)
        self.assertEqual(out["backchannels"], 0)

    def test_silence_is_no_response(self):
        out = evaluation.grade(trace([]))
        self.assertFalse(out["responded"])
        self.assertIsNone(out["first_voice_s"])

    def test_talking_during_the_pause_is_an_interruption(self):
        out = evaluation.grade(trace([(3.0, 4.5)], said=[(1.0, 2.0), (5.0, 6.0)], pauses=[(2.0, 5.0)]))
        self.assertTrue(out["interrupted_pause"])

    def test_short_listening_sound_in_the_pause_is_not_an_interruption(self):
        out = evaluation.grade(trace([(3.0, 3.4), (7.0, 9.0)], said=[(1.0, 2.0), (5.0, 6.0)], pauses=[(2.0, 5.0)]))
        self.assertFalse(out["interrupted_pause"])
        self.assertEqual(out["backchannels"], 1)
        self.assertEqual(out["first_voice_s"], 1.0)

    def test_waiting_through_the_pause_passes(self):
        out = evaluation.grade(trace([(7.0, 9.0)], said=[(1.0, 2.0), (5.0, 6.0)], pauses=[(2.0, 5.0)]))
        self.assertFalse(out["interrupted_pause"])

    def test_delegation_is_compared_only_when_a_scenario_expects_it(self):
        self.assertNotIn("delegation_correct", evaluation.grade(trace([])))
        self.assertTrue(evaluation.grade(trace([], expect_delegation=True, delegated_at=2.5))["delegation_correct"])
        self.assertFalse(evaluation.grade(trace([], expect_delegation=True))["delegation_correct"])
        self.assertFalse(evaluation.grade(trace([], expect_delegation=False, delegated_at=2.5))["delegation_correct"])

    def test_time_to_stop_after_being_interrupted(self):
        out = evaluation.grade(trace([(3.0, 6.5), (9.0, 10.0)], said=[(1.0, 2.0), (5.0, 6.0)], interject_at=5.0))
        self.assertEqual(out["yield_s"], 1.5)

    def test_summary_counts_only_applicable_sessions(self):
        rows = [{"interrupted_pause": True, "responded": True, "first_voice_s": 1.0, "usage_s": 5.0},
                {"interrupted_pause": None, "responded": False, "first_voice_s": None, "usage_s": 7.0}]
        out = evaluation.summarize(rows)
        self.assertEqual(out["interrompeu_pausa"], (1, 1))
        self.assertEqual(out["respondeu"], (1, 2))
        self.assertEqual(out["segundos_cobrados"], 12.0)


class Spending(unittest.TestCase):
    def test_spend_adds_up_across_runs_and_counts_unconfirmed_sessions(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "spend.jsonl"
            self.assertEqual(evaluation.spent_usd(path), 0.0)
            evaluation.record_spend(path, "a", "x", 60.0, True)
            evaluation.record_spend(path, "b", "y", 30.0, False)
            self.assertAlmostEqual(evaluation.spent_usd(path), 0.075)
            self.assertFalse(json.loads(path.read_text().splitlines()[1])["confirmed"])

    def test_refuses_to_start_a_session_over_the_cap(self):
        args = type("Args", (), {"scenarios": ["pergunta"], "label": "t", "trials": 1, "spend_cap_usd": 0.0})
        calls = []
        real_session, real_out, real_synth = evaluation.run_session, evaluation.OUT, evaluation.synthesize
        with tempfile.TemporaryDirectory() as tmp:
            evaluation.OUT = Path(tmp)
            evaluation.run_session = lambda *a: calls.append(a)
            evaluation.synthesize = lambda texts: {}
            try:
                self.assertEqual(evaluation.run(args), 3)
            finally:
                evaluation.run_session, evaluation.OUT, evaluation.synthesize = real_session, real_out, real_synth
        self.assertEqual(calls, [])

    def test_live_run_needs_explicit_permission(self):
        sys.argv = ["eval_live_turns.py", "--label", "x"]
        with self.assertRaises(SystemExit):
            evaluation.main()


if __name__ == "__main__":
    unittest.main()
