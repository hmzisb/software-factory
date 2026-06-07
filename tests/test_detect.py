"""Tests for detect.py — mode + stack detection."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import detect  # noqa: E402


class DetectTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_empty_is_greenfield(self):
        d = detect.detect(self.tmp)
        self.assertEqual(d["mode"], "greenfield")
        self.assertFalse(d["config_exists"])

    def test_config_only_still_greenfield(self):
        (self.tmp / "factory.config.json").write_text("{}")
        d = detect.detect(self.tmp)
        self.assertEqual(d["mode"], "greenfield")
        self.assertTrue(d["config_exists"])

    def test_validated_config_is_resume(self):
        (self.tmp / "factory.config.json").write_text(json.dumps({"validated": True}))
        d = detect.detect(self.tmp)
        self.assertEqual(d["mode"], "resume")
        self.assertTrue(d["config_exists"])

    def test_node_project(self):
        (self.tmp / "package.json").write_text(json.dumps({
            "scripts": {"test": "vitest", "build": "vite build", "lint": "eslint ."},
            "dependencies": {"react": "^18"},
        }))
        (self.tmp / "tsconfig.json").write_text("{}")
        (self.tmp / "package-lock.json").write_text("{}")
        d = detect.detect(self.tmp)
        self.assertEqual(d["mode"], "retrofit")
        self.assertEqual(d["stack"]["language"], "typescript")
        self.assertEqual(d["stack"]["package_manager"], "npm")
        self.assertEqual(d["stack"]["framework"], "react")
        self.assertTrue(d["commands"]["test_cmd"])
        self.assertEqual(d["commands"]["build_cmd"], "npm run build")

    def test_python_project(self):
        (self.tmp / "pyproject.toml").write_text(
            "[project]\nname='x'\ndependencies=['pytest','ruff','mypy','fastapi']\n")
        (self.tmp / "tests").mkdir()
        d = detect.detect(self.tmp)
        self.assertEqual(d["mode"], "retrofit")
        self.assertEqual(d["stack"]["language"], "python")
        self.assertEqual(d["commands"]["test_cmd"], "pytest")
        self.assertEqual(d["commands"]["lint_cmd"], "ruff check .")
        self.assertEqual(d["commands"]["typecheck_cmd"], "mypy .")

    def test_go_project(self):
        (self.tmp / "go.mod").write_text("module x\n")
        d = detect.detect(self.tmp)
        self.assertEqual(d["stack"]["language"], "go")
        self.assertEqual(d["commands"]["test_cmd"], "go test ./...")

    def test_ci_detected(self):
        (self.tmp / ".github" / "workflows").mkdir(parents=True)
        (self.tmp / ".github" / "workflows" / "ci.yml").write_text("on: push")
        d = detect.detect(self.tmp)
        self.assertTrue(d["ci_exists"])


if __name__ == "__main__":
    unittest.main()
