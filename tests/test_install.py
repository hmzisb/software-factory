"""Tests for install.sh — idempotent symlink, no clobber of real dirs."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
INSTALL = SKILL_DIR / "install.sh"


def run_install(skills_dir, home=None):
    env = {**os.environ, "CLAUDE_SKILLS_DIR": str(skills_dir)}
    if home:
        env["HOME"] = str(home)
    return subprocess.run(["bash", str(INSTALL)], capture_output=True, text=True, env=env)


class InstallTest(unittest.TestCase):
    def setUp(self):
        self.skills = Path(tempfile.mkdtemp())

    def test_creates_symlink(self):
        r = run_install(self.skills)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        link = self.skills / "software-factory"
        self.assertTrue(link.is_symlink())
        self.assertEqual(link.resolve(), SKILL_DIR.resolve())

    def test_idempotent(self):
        run_install(self.skills)
        r = run_install(self.skills)   # second run replaces its own symlink
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((self.skills / "software-factory").is_symlink())

    def test_refuses_to_clobber_real_dir(self):
        real = self.skills / "software-factory"
        real.mkdir()
        (real / "keep.txt").write_text("user data")
        r = run_install(self.skills)
        self.assertNotEqual(r.returncode, 0)
        self.assertTrue((real / "keep.txt").exists())   # not deleted


if __name__ == "__main__":
    unittest.main()
