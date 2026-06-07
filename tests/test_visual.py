"""Tests for the generated visual_check.py (templates/eval/visual_check.py.tmpl).

No {{ }} placeholders, so it runs directly. Playwright is not installed in the
test env, so the skip-path (exit 0) is what we assert — the gate is opt-in.
"""
import subprocess
import sys
import unittest
from pathlib import Path

VC = Path(__file__).resolve().parent.parent / "templates" / "eval" / "visual_check.py.tmpl"


def run(args):
    return subprocess.run([sys.executable, str(VC), *args],
                          capture_output=True, text=True)


class VisualCheckTest(unittest.TestCase):
    def test_skips_without_playwright(self):
        r = run(["http://localhost:3000", "--has-text", "Hello"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("skipped", (r.stdout + r.stderr).lower())

    def test_requires_url(self):
        r = run([])
        self.assertNotEqual(r.returncode, 0)  # argparse error (exit 2)


if __name__ == "__main__":
    unittest.main()
