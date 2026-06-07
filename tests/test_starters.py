"""Tests for fetch_starter.py + preview.py."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import fetch_starter  # noqa: E402
import preview  # noqa: E402


def make_local_repo():
    repo = Path(tempfile.mkdtemp())
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (repo / "app.txt").write_text("hello starter")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c",
                    "user.name=t", "commit", "-qm", "init"], check=True)
    return repo


class RegistryTest(unittest.TestCase):
    def test_has_known_starters(self):
        ids = {s["id"] for s in fetch_starter.load_registry()}
        self.assertIn("crm", ids)
        self.assertIn("blank", ids)

    def test_blank_has_no_repo(self):
        self.assertIsNone(fetch_starter.find("blank")["repo"])

    def test_unknown_id(self):
        self.assertIsNone(fetch_starter.find("does-not-exist"))


class CloneTest(unittest.TestCase):
    def test_clone_strips_git(self):
        repo = make_local_repo()
        dest = Path(tempfile.mkdtemp()) / "app"
        fetch_starter.clone(str(repo), None, dest)
        self.assertTrue((dest / "app.txt").exists())
        self.assertFalse((dest / ".git").exists())

    def test_refuses_nonempty_target(self):
        repo = make_local_repo()
        dest = Path(tempfile.mkdtemp())
        (dest / "x").write_text("existing")
        with self.assertRaises(SystemExit):
            fetch_starter.clone(str(repo), None, dest)


class PreviewTest(unittest.TestCase):
    def test_dev_cmd_resolution(self):
        self.assertEqual(preview.get_dev_cmd({"quality": {"dev_cmd": "npm run dev"}}),
                         "npm run dev")
        self.assertEqual(preview.get_dev_cmd(
            {"quality": {}, "starter": {"dev_cmd": "pnpm dev"}}), "pnpm dev")
        self.assertEqual(preview.get_dev_cmd({}), "")

    def test_dry_run(self):
        d = Path(tempfile.mkdtemp())
        (d / "factory.config.json").write_text(json.dumps({"quality": {"dev_cmd": "echo up"}}))
        r = subprocess.run([sys.executable, str(SCRIPTS / "preview.py"),
                            "--target", str(d), "--dry"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_no_dev_cmd_errors(self):
        d = Path(tempfile.mkdtemp())
        (d / "factory.config.json").write_text(json.dumps({"quality": {}}))
        r = subprocess.run([sys.executable, str(SCRIPTS / "preview.py"),
                            "--target", str(d), "--dry"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
