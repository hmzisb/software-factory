"""Tests for scaffold.py — greenfield, determinism, retrofit no-clobber, validation."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import scaffold  # noqa: E402


def sample_config(mode="greenfield"):
    return {
        "version": 1,
        "validated": True,
        "mode": mode,
        "project": {
            "name": "Acme Rentals",
            "one_liner": "Bike rental management for city shops.",
            "problem": "Shops track rentals on paper.",
            "users": "Shop staff and managers.",
            "success_metric": "Rentals logged digitally in week 1.",
        },
        "domain": {
            "specialization": {"kind": "domain", "label": "bike rental"},
            "entities": [
                {"name": "bike", "description": "A rentable bike",
                 "relationships": ["rental"]},
                {"name": "rental", "description": "A booking",
                 "relationships": ["bike", "customer"]},
            ],
            "glossary": {"overdue": "past the return time", "fleet": "all bikes"},
            "workflows": ["Rent a bike", "Return a bike"],
        },
        "stack": {"language": "python", "framework": "fastapi",
                  "database": "postgres", "package_manager": "uv", "runtime": "python"},
        "quality": {"test_cmd": "pytest", "build_cmd": "", "lint_cmd": "ruff check .",
                    "typecheck_cmd": "mypy .", "test_framework": "pytest",
                    "coverage_target": 80},
        "nfrs": {"security": ["auth required on all writes"], "performance": "",
                 "accessibility": "", "i18n": False},
        "delivery": {"git_host": "github", "ci": True, "deploy_target": "fly.io",
                     "environments": ["dev", "prod"], "backend": "supabase",
                     "migration_tool": "prisma", "data_mode": "demo"},
        "factory": {"layers": [0], "agent_team_size": 3, "autonomy": "semi-autonomous",
                    "budget_usd": 5},
        "seed": {"generate_prd": False, "first_feature": ""},
        "uses_external_skills": {"superpowers": False, "mattpocock": False},
        "interview_progress": {f"d{i}_{n}": "done" for i, n in enumerate(
            ["product", "domain", "stack", "quality", "nfrs", "delivery", "factory", "seed"], 1)},
    }


def all_files(root):
    return {p.relative_to(root).as_posix(): p.read_text()
            for p in sorted(root.rglob("*")) if p.is_file()}


class GreenfieldTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_core_files_written(self):
        scaffold.scaffold(sample_config(), self.tmp, no_git=True)
        for rel in [
            "CLAUDE.md", "CONTEXT.md", "definition-of-done.md", "factory.config.json",
            ".claude/agents/orchestrator.md", ".claude/agents/developer.md",
            ".claude/agents/merger.md", ".claude/commands/factory-build.md",
            ".claude/rules/validation-commands.md", ".claude/rules/security.md",
            ".claude/skills/tdd/SKILL.md", ".claude/skills/verification/SKILL.md",
            "docs/adr/0000-record-architecture-decisions.md",
            "docs/learnings/patterns.md", "specs/spec.template.md",
            ".claude/rules/data-modes.md", ".claude/skills/writing-migrations/SKILL.md",
            "db/migrations/.gitkeep", "db/README.md", "deploy/deploy.sh",
            "db/migrate.sh", "db/provision.sh",
            ".claude/skills/visual-testing/SKILL.md", "eval/visual_check.py",
            "MEMORY.md", "docs/sessions/.gitkeep", ".claude/skills/handoff/SKILL.md",
            ".claude/commands/factory-handoff.md", ".claude/commands/factory-resume.md",
        ]:
            self.assertTrue((self.tmp / rel).exists(), f"missing: {rel}")

    def test_gitignore_written(self):
        scaffold.scaffold(sample_config(), self.tmp, no_git=True)
        gi = (self.tmp / ".gitignore")
        self.assertTrue(gi.exists())
        text = gi.read_text()
        self.assertIn("worktrees/", text)
        self.assertIn(".env", text)
        self.assertIn("__pycache__/", text)

    def test_ci_emits_toolchain_setup(self):
        scaffold.scaffold(sample_config(), self.tmp, no_git=True)  # python/uv
        ci = (self.tmp / ".github" / "workflows" / "factory-ci.yml").read_text()
        self.assertIn("actions/setup-python", ci)
        self.assertIn("astral-sh/setup-uv", ci)
        self.assertNotIn("TODO", ci)

    def test_deploy_script_executable(self):
        scaffold.scaffold(sample_config(), self.tmp, no_git=True)
        self.assertTrue((self.tmp / "deploy" / "deploy.sh").stat().st_mode & 0o100)

    def test_migrate_script_dry_runs(self):
        import subprocess
        scaffold.scaffold(sample_config(), self.tmp, no_git=True)
        self.assertTrue((self.tmp / "db" / "migrate.sh").stat().st_mode & 0o100)
        r = subprocess.run(["bash", str(self.tmp / "db" / "migrate.sh"), "apply"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Dry run", r.stdout)

    def test_placeholders_substituted(self):
        scaffold.scaffold(sample_config(), self.tmp, no_git=True)
        claude = (self.tmp / "CLAUDE.md").read_text()
        self.assertIn("Acme Rentals", claude)
        self.assertIn("bike rental", claude)
        context = (self.tmp / "CONTEXT.md").read_text()
        self.assertIn("**bike**", context)
        self.assertIn("**fleet**", context)  # glossary
        # no unrendered placeholders anywhere
        for rel, text in all_files(self.tmp).items():
            if rel == "factory.config.json":
                continue
            self.assertNotIn("{{", text, f"unrendered placeholder in {rel}")

    def test_schema_not_stamped(self):
        scaffold.scaffold(sample_config(), self.tmp, no_git=True)
        self.assertFalse((self.tmp / "factory.config.schema.json").exists())

    def test_layer1_excluded_when_layer0_only(self):
        scaffold.scaffold(sample_config(), self.tmp, no_git=True)
        self.assertFalse((self.tmp / "layer1").exists())

    def test_determinism(self):
        a = Path(tempfile.mkdtemp())
        b = Path(tempfile.mkdtemp())
        scaffold.scaffold(sample_config(), a, no_git=True)
        scaffold.scaffold(sample_config(), b, no_git=True)
        self.assertEqual(all_files(a), all_files(b))


class Layer1Test(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        cfg = sample_config()
        cfg["factory"]["layers"] = [0, 1]
        scaffold.scaffold(cfg, self.tmp, no_git=True)

    def test_layer1_files_present(self):
        for rel in [
            "Dockerfile", "docker-compose.yml", "README.layer1.md",
            "builder/server.py", "builder/index.html", "deploy/deploy.sh",
            ".claude/agents/builder-orchestrator.md",
        ]:
            self.assertTrue((self.tmp / rel).exists(), f"missing layer1: {rel}")

    def test_layer0_still_present(self):
        self.assertTrue((self.tmp / ".claude" / "agents" / "orchestrator.md").exists())

    def test_deploy_script_executable(self):
        self.assertTrue((self.tmp / "deploy" / "deploy.sh").stat().st_mode & 0o100)

    def test_no_placeholders(self):
        for p in self.tmp.rglob("*"):
            if p.is_file() and p.name != "factory.config.json":
                self.assertNotIn("{{", p.read_text(), f"unrendered: {p}")


class RetrofitTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_no_clobber(self):
        # pre-existing user files
        (self.tmp / "CLAUDE.md").write_text("# USER DOC\nkeep me\n")
        (self.tmp / ".claude" / "rules").mkdir(parents=True)
        (self.tmp / ".claude" / "rules" / "coding-style.md").write_text("USER RULES")

        report = scaffold.scaffold(sample_config("retrofit"), self.tmp, no_git=True)

        claude = (self.tmp / "CLAUDE.md").read_text()
        self.assertIn("# USER DOC", claude)            # user content preserved
        self.assertIn("keep me", claude)
        self.assertIn(scaffold.BEGIN, claude)          # managed block appended
        self.assertTrue((self.tmp / "CLAUDE.md.bak").exists())

        # existing rule left untouched + reported skipped
        self.assertEqual((self.tmp / ".claude" / "rules" / "coding-style.md").read_text(),
                         "USER RULES")
        self.assertIn(".claude/rules/coding-style.md", report["SKIPPED"])

        # new files still added
        self.assertTrue((self.tmp / ".claude" / "agents" / "orchestrator.md").exists())

    def test_managed_block_replaced_not_duplicated(self):
        (self.tmp / "CLAUDE.md").write_text("# USER\n")
        scaffold.scaffold(sample_config("retrofit"), self.tmp, no_git=True)
        scaffold.scaffold(sample_config("retrofit"), self.tmp, no_git=True)
        claude = (self.tmp / "CLAUDE.md").read_text()
        self.assertEqual(claude.count(scaffold.BEGIN), 1)

    def test_backup_preserves_original_across_reruns(self):
        (self.tmp / "CLAUDE.md").write_text("ORIGINAL USER DOC\n")
        scaffold.scaffold(sample_config("retrofit"), self.tmp, no_git=True)
        scaffold.scaffold(sample_config("retrofit"), self.tmp, no_git=True)
        # the .bak must still be the pristine original, not the merged file
        self.assertEqual((self.tmp / "CLAUDE.md.bak").read_text(),
                         "ORIGINAL USER DOC\n")


class ValidationTest(unittest.TestCase):
    def test_refuses_unvalidated(self):
        cfg = sample_config()
        cfg["validated"] = False
        with self.assertRaises(SystemExit):
            scaffold.validate_config(cfg)

    def test_refuses_missing_required(self):
        cfg = sample_config()
        cfg["quality"]["test_cmd"] = ""
        with self.assertRaises(SystemExit):
            scaffold.validate_config(cfg)

    def test_accepts_valid_config(self):
        # the validator must not false-positive on a good config
        self.assertEqual(scaffold.validate_against_schema(sample_config()), [])
        scaffold.validate_config(sample_config())  # no raise

    def test_refuses_wrong_type(self):
        cfg = sample_config()
        cfg["factory"]["agent_team_size"] = "three"  # should be integer
        with self.assertRaises(SystemExit):
            scaffold.validate_config(cfg)

    def test_refuses_unknown_key(self):
        cfg = sample_config()
        cfg["totally_bogus_key"] = 1  # additionalProperties: false
        with self.assertRaises(SystemExit):
            scaffold.validate_config(cfg)

    def test_refuses_bad_enum(self):
        cfg = sample_config()
        cfg["mode"] = "sideways"  # enum greenfield|retrofit
        with self.assertRaises(SystemExit):
            scaffold.validate_config(cfg)


if __name__ == "__main__":
    unittest.main()
