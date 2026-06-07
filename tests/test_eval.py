"""Tests for the generated eval harness (templates/eval/run.py.tmpl).

The .tmpl has no {{ }} placeholders, so it is valid Python and runs directly.
A deterministic fake runner proves the N-times scoring, threshold gate, and
baseline regression logic without needing a real `claude` runner.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RUN = Path(__file__).resolve().parent.parent / "templates" / "eval" / "run.py.tmpl"


def write_cases(d, cases):
    p = d / "cases.json"
    p.write_text(json.dumps(cases))
    return p


def run_eval(args, cwd):
    return subprocess.run([sys.executable, str(RUN), *args],
                          cwd=cwd, capture_output=True, text=True)


class EvalTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.baseline = self.d / "baseline.json"

    def test_full_pass_and_baseline_write(self):
        cases = write_cases(self.d, [{"id": "c1", "prompt": "x",
                                      "expect": {"files": ["out.txt"]}}])
        r = run_eval(["--cases", str(cases), "--baseline", str(self.baseline),
                      "--runner", "touch out.txt", "--runs", "3",
                      "--update-baseline"], cwd=self.d)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        bl = json.loads(self.baseline.read_text())
        self.assertEqual(bl["cases"]["c1"], 1.0)

    def test_below_threshold_fails(self):
        cases = write_cases(self.d, [{"id": "c1", "prompt": "x",
                                      "expect": {"files": ["nope.txt"]}}])
        r = run_eval(["--cases", str(cases), "--baseline", str(self.baseline),
                      "--runner", "true", "--runs", "3"], cwd=self.d)
        self.assertEqual(r.returncode, 1)

    def test_must_invoke(self):
        cases = write_cases(self.d, [{"id": "c1", "prompt": "x",
                                      "expect": {"mustInvoke": ["developer"],
                                                 "mustNotInvoke": ["merger"]}}])
        r = run_eval(["--cases", str(cases), "--baseline", str(self.baseline),
                      "--runner", "echo developer", "--runs", "2"], cwd=self.d)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_regression_detected(self):
        self.baseline.write_text(json.dumps({"threshold": 0.8, "cases": {"c1": 1.0}}))
        cases = write_cases(self.d, [{"id": "c1", "prompt": "x",
                                      "expect": {"files": ["x"]}}])
        r = run_eval(["--cases", str(cases), "--baseline", str(self.baseline),
                      "--runner", "true", "--runs", "2"], cwd=self.d)
        self.assertEqual(r.returncode, 1)

    def test_no_runner_errors(self):
        cases = write_cases(self.d, [{"id": "c1", "prompt": "x", "expect": {}}])
        r = run_eval(["--cases", str(cases), "--baseline", str(self.baseline)],
                     cwd=self.d)
        self.assertEqual(r.returncode, 2)  # no runner configured

    def test_max_duration_hard_fail(self):
        cases = write_cases(self.d, [{"id": "c1", "prompt": "x",
                                      "expect": {"maxDurationMs": 50}}])
        r = run_eval(["--cases", str(cases), "--baseline", str(self.baseline),
                      "--runner", "sleep 0.3", "--runs", "1"], cwd=self.d)
        self.assertEqual(r.returncode, 1)

    def test_max_cost_hard_fail(self):
        cases = write_cases(self.d, [{"id": "c1", "prompt": "x",
                                      "expect": {"maxCostUsd": 1.0}}])
        # runner output (its stdout) carries the cost; no literal braces in the
        # runner *command* (that would break .format)
        r = run_eval(["--cases", str(cases), "--baseline", str(self.baseline),
                      "--runner", "echo total_cost_usd=9.99", "--runs", "1"], cwd=self.d)
        self.assertEqual(r.returncode, 1)

    def test_must_modify_is_warning_not_failure(self):
        cases = write_cases(self.d, [{"id": "c1", "prompt": "x",
                                      "expect": {"mustModify": ["other.txt"]}}])
        r = run_eval(["--cases", str(cases), "--baseline", str(self.baseline),
                      "--runner", "touch out.txt", "--runs", "1"], cwd=self.d)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)   # warn, not fail
        self.assertIn("expected to modify", r.stdout)

    def test_must_not_modify_warns(self):
        cases = write_cases(self.d, [{"id": "c1", "prompt": "x",
                                      "expect": {"mustNotModify": ["*.txt"]}}])
        r = run_eval(["--cases", str(cases), "--baseline", str(self.baseline),
                      "--runner", "touch secret.txt", "--runs", "1"], cwd=self.d)
        self.assertEqual(r.returncode, 0)                        # warn, not fail
        self.assertIn("protected path", r.stdout)

    def test_seed_copies_into_sandbox(self):
        seed = self.d / "seeddir"
        seed.mkdir()
        (seed / "seeded.txt").write_text("hi")
        cases = write_cases(self.d, [{"id": "c1", "prompt": "x", "seed": "seeddir",
                                      "expect": {"files": ["seeded.txt"]}}])
        r = run_eval(["--cases", str(cases), "--baseline", str(self.baseline),
                      "--runner", "true", "--runs", "1"], cwd=self.d)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)   # seed file present

    def test_cost_unenforced_warns(self):
        cases = write_cases(self.d, [{"id": "c1", "prompt": "x",
                                      "expect": {"maxCostUsd": 1.0}}])
        r = run_eval(["--cases", str(cases), "--baseline", str(self.baseline),
                      "--runner", "true", "--runs", "1"], cwd=self.d)
        self.assertEqual(r.returncode, 0)                        # warn, not fail
        self.assertIn("cost not enforced", r.stdout)


if __name__ == "__main__":
    unittest.main()
