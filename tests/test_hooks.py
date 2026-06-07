"""Tests for the generated guardrail hooks (templates/hooks/*.py)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parent.parent / "templates" / "hooks"


def run_hook(name, payload, env=None):
    full = {**os.environ, **(env or {})}
    return subprocess.run(
        [sys.executable, str(HOOKS / name)],
        input=json.dumps(payload), text=True, capture_output=True, env=full)


class BlockDangerousGitTest(unittest.TestCase):
    def _bash(self, command):
        return run_hook("block-dangerous-git.py",
                        {"tool_name": "Bash", "tool_input": {"command": command}})

    def test_blocks_force_push(self):
        self.assertEqual(self._bash("git push --force origin main").returncode, 2)

    def test_blocks_reset_hard(self):
        self.assertEqual(self._bash("git reset --hard HEAD~1").returncode, 2)

    def test_blocks_clean(self):
        self.assertEqual(self._bash("git clean -fd").returncode, 2)

    def test_blocks_branch_force_delete(self):
        self.assertEqual(self._bash("git branch -D feature").returncode, 2)

    def test_blocks_rm_rf_dangerous_paths(self):
        for cmd in ("rm -rf .", "rm -rf ..", "rm -rf ~", "rm -rf $HOME",
                    "rm -rf /", "rm -rf *", "rm -fr ."):
            self.assertEqual(self._bash(cmd).returncode, 2, cmd)

    def test_allows_rm_rf_real_subdir(self):
        for cmd in ("rm -rf ./build", "rm -rf node_modules", "rm -rf dist/",
                    "rm -rf /tmp/scratch-xyz"):
            self.assertEqual(self._bash(cmd).returncode, 0, cmd)

    def test_blocks_git_history_destruction(self):
        for cmd in ("git checkout -- .", "git restore .", "git stash clear",
                    "git reflog expire --expire=now --all", "git gc --prune=now",
                    "git update-ref -d refs/heads/x", "git push --mirror origin"):
            self.assertEqual(self._bash(cmd).returncode, 2, cmd)

    def test_allows_safe_git(self):
        self.assertEqual(self._bash("git status").returncode, 0)
        self.assertEqual(self._bash("git push origin main").returncode, 0)
        self.assertEqual(self._bash("git checkout -- src/app.ts").returncode, 0)

    def test_ignores_non_bash(self):
        r = run_hook("block-dangerous-git.py",
                     {"tool_name": "Read", "tool_input": {"file_path": "x"}})
        self.assertEqual(r.returncode, 0)


class ProtectSecretsTest(unittest.TestCase):
    def _write(self, path, content):
        return run_hook("protect-secrets.py",
                        {"tool_name": "Write",
                         "tool_input": {"file_path": path, "content": content}})

    def test_blocks_aws_key(self):
        self.assertEqual(self._write("config.ts", "const k='AKIA1234567890ABCDEF'").returncode, 2)

    def test_blocks_password_assignment(self):
        self.assertEqual(self._write("db.py", "password = 's3cretValue123456'").returncode, 2)

    def test_allows_placeholder(self):
        self.assertEqual(self._write("db.py", "api_key = 'your-api-key-here'").returncode, 0)

    def test_allows_example_file(self):
        self.assertEqual(self._write(".env.example", "API_KEY='AKIA1234567890ABCDEF'").returncode, 0)

    def test_blocks_real_secret_in_tests_dir(self):
        # a fixture/test path is NOT a blanket exemption — real keys still blocked
        self.assertEqual(
            self._write("tests/fixtures/seed.py", "key='AKIA1234567890ABCDEF'").returncode, 2)

    def test_ignores_read(self):
        r = run_hook("protect-secrets.py",
                     {"tool_name": "Read", "tool_input": {"file_path": "x"}})
        self.assertEqual(r.returncode, 0)


class ValidateOnStopTest(unittest.TestCase):
    def _project(self, test_cmd):
        d = Path(tempfile.mkdtemp())
        cfg = {"version": 1, "validated": True, "mode": "greenfield",
               "quality": {"test_cmd": test_cmd}}
        (d / "factory.config.json").write_text(json.dumps(cfg))
        return d

    def test_passes_when_tests_pass(self):
        d = self._project("true")
        r = run_hook("validate-on-stop.py", {"stop_hook_active": False},
                     env={"CLAUDE_PROJECT_DIR": str(d)})
        self.assertEqual(r.returncode, 0)

    def test_blocks_when_tests_fail(self):
        d = self._project("false")
        r = run_hook("validate-on-stop.py", {"stop_hook_active": False},
                     env={"CLAUDE_PROJECT_DIR": str(d)})
        self.assertEqual(r.returncode, 2)

    def test_no_loop_when_active(self):
        d = self._project("false")
        r = run_hook("validate-on-stop.py", {"stop_hook_active": True},
                     env={"CLAUDE_PROJECT_DIR": str(d)})
        self.assertEqual(r.returncode, 0)

    def test_noop_without_config(self):
        d = Path(tempfile.mkdtemp())
        r = run_hook("validate-on-stop.py", {"stop_hook_active": False},
                     env={"CLAUDE_PROJECT_DIR": str(d)})
        self.assertEqual(r.returncode, 0)

    def test_disabled_by_flag(self):
        d = Path(tempfile.mkdtemp())
        cfg = {"version": 1, "validated": True, "mode": "greenfield",
               "quality": {"test_cmd": "false", "validate_on_stop": False}}
        (d / "factory.config.json").write_text(json.dumps(cfg))
        r = run_hook("validate-on-stop.py", {"stop_hook_active": False},
                     env={"CLAUDE_PROJECT_DIR": str(d)})
        self.assertEqual(r.returncode, 0)  # would be 2 if it ran `false`

    def test_skips_when_tree_unchanged(self):
        d = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(d)], check=True)
        (d / "foo.txt").write_text("v1")
        subprocess.run(["git", "-C", str(d), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(d), "-c", "user.email=t@t", "-c",
                        "user.name=t", "commit", "-qm", "init"], check=True)
        (d / ".claude").mkdir()
        # test_cmd appends a byte each time it actually runs
        cfg = {"version": 1, "validated": True, "mode": "greenfield",
               "quality": {"test_cmd": "printf x >> ran.log"}}
        (d / "factory.config.json").write_text(json.dumps(cfg))
        env = {"CLAUDE_PROJECT_DIR": str(d)}

        run_hook("validate-on-stop.py", {"stop_hook_active": False}, env=env)
        self.assertEqual((d / "ran.log").read_text(), "x")        # ran once
        run_hook("validate-on-stop.py", {"stop_hook_active": False}, env=env)
        self.assertEqual((d / "ran.log").read_text(), "x")        # skipped (unchanged)

        (d / "foo.txt").write_text("v2")                          # tree changed
        run_hook("validate-on-stop.py", {"stop_hook_active": False}, env=env)
        self.assertEqual((d / "ran.log").read_text(), "xx")       # re-ran


def make_repo():
    import tempfile
    repo = Path(tempfile.mkdtemp())
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (repo / "f.txt").write_text("x")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c",
                    "user.name=t", "commit", "-qm", "init"], check=True)
    return repo


def run_hook_in(name, payload, cwd, env=None):
    full = {**os.environ, **(env or {})}
    return subprocess.run(["bash", str(HOOKS / name)], input=json.dumps(payload),
                          text=True, capture_output=True, cwd=cwd, env=full)


class WorktreeHookTest(unittest.TestCase):
    def test_setup_creates_worktree_for_developer(self):
        repo = make_repo()
        r = run_hook_in("setup-worktree.sh",
                        {"agent_type": "developer-TASK-001"}, repo)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((repo / "worktrees" / "TASK-001").exists())
        br = subprocess.run(["git", "-C", str(repo), "branch", "--list",
                             "factory/TASK-001"], capture_output=True, text=True)
        self.assertIn("factory/TASK-001", br.stdout)

    def test_setup_uses_session_branch_when_set(self):
        repo = make_repo()
        r = run_hook_in("setup-worktree.sh", {"agent_type": "developer-TASK-002"},
                        repo, env={"FACTORY_SESSION": "sess9"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((repo / "worktrees" / "sess9" / "TASK-002").exists())
        br = subprocess.run(["git", "-C", str(repo), "branch", "--list",
                             "sess9/TASK-002"], capture_output=True, text=True)
        self.assertIn("sess9/TASK-002", br.stdout)

    def test_setup_noop_for_non_developer(self):
        repo = make_repo()
        r = run_hook_in("setup-worktree.sh",
                        {"agent_type": "reviewer-TASK-001"}, repo)
        self.assertEqual(r.returncode, 0)
        self.assertFalse((repo / "worktrees").exists())

    def test_setup_noop_outside_git(self):
        import tempfile
        d = Path(tempfile.mkdtemp())
        r = run_hook_in("setup-worktree.sh", {"agent_type": "developer"}, d)
        self.assertEqual(r.returncode, 0)

    def test_setup_preserves_unmerged_branch(self):
        """A leftover branch with unmerged commits must NOT be force-deleted —
        the prior work is preserved and a uniquely-suffixed branch is forked."""
        repo = make_repo()
        # simulate a dead prior run: a branch with a commit not on main
        subprocess.run(["git", "-C", str(repo), "worktree", "add", "-b",
                        "factory/TASK-007", str(repo / "wt7")], check=True,
                       capture_output=True)
        (repo / "wt7" / "wip.txt").write_text("unmerged work")
        subprocess.run(["git", "-C", str(repo / "wt7"), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(repo / "wt7"), "-c", "user.email=t@t",
                        "-c", "user.name=t", "commit", "-qm", "wip"], check=True)
        subprocess.run(["git", "-C", str(repo), "worktree", "remove", "--force",
                        str(repo / "wt7")], check=True, capture_output=True)

        r = run_hook_in("setup-worktree.sh",
                        {"agent_type": "developer-TASK-007"}, repo)
        self.assertEqual(r.returncode, 0, r.stderr)

        branches = subprocess.run(["git", "-C", str(repo), "branch", "--list"],
                                  capture_output=True, text=True).stdout
        self.assertIn("factory/TASK-007", branches)    # original preserved
        self.assertIn("factory/TASK-007-2", branches)  # new run forked aside
        self.assertTrue((repo / "worktrees" / "TASK-007-2").exists())
        # the unmerged commit still reachable from the original branch
        log = subprocess.run(["git", "-C", str(repo), "log", "--oneline",
                              "factory/TASK-007"], capture_output=True, text=True).stdout
        self.assertIn("wip", log)

    def test_cleanup_exits_zero(self):
        repo = make_repo()
        r = run_hook_in("cleanup-worktree.sh", {"agent_type": "merger"}, repo)
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
