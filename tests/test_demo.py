"""End-to-end pipeline proof: run examples/demo/run_demo.sh and require it green.

This is the credibility test — it exercises the whole deterministic pipeline
(detect -> scaffold -> generated artifacts run -> probabilistic eval) on every
CI run, with no API key. What it does NOT cover (model-dependent autonomous
build quality) is documented in LIMITATIONS.md.
"""
import subprocess
import unittest
from pathlib import Path

DEMO = Path(__file__).resolve().parent.parent / "examples" / "demo" / "run_demo.sh"


class DemoTest(unittest.TestCase):
    def test_demo_runs_end_to_end(self):
        r = subprocess.run(["bash", str(DEMO)], capture_output=True, text=True,
                           timeout=180)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("DEMO OK", r.stdout)


if __name__ == "__main__":
    unittest.main()
