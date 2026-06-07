#!/usr/bin/env python3
"""Stop guardrail: enforce 'evidence before done'.

On Stop, run the project's test (and typecheck) commands from
factory.config.json. If any fails, exit 2 + stderr so the model must fix before
finishing. Respects stop_hook_active to avoid loops.

Ergonomics: re-running the full suite on *every* turn-yield is painful on a real
codebase, so this only runs when the working tree changed since the last green
validation (tracked via .claude/.validate-marker). Set
`quality.validate_on_stop: false` in factory.config.json to disable entirely.

Fail-open on errors that aren't a real test failure — but say so on stderr, so a
silently-misconfigured command can't masquerade as "all green".
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def find_config():
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    p = Path(root) / "factory.config.json"
    if p.exists():
        return p
    for parent in [Path.cwd(), *Path.cwd().parents]:
        cand = parent / "factory.config.json"
        if cand.exists():
            return cand
    return None


def git_dir(project_dir):
    """Absolute path to the repo's git dir, or None if not a git repo."""
    try:
        r = subprocess.run(["git", "-C", str(project_dir), "rev-parse", "--git-dir"],
                           capture_output=True, text=True, timeout=15)
        if r.returncode != 0 or not r.stdout.strip():
            return None
        gd = Path(r.stdout.strip())
        return gd if gd.is_absolute() else (Path(project_dir) / gd).resolve()
    except Exception:
        return None


def tree_fingerprint(project_dir):
    """Cheap signal of working-tree state. '' if not a git repo (→ always run).
    The marker lives inside .git (see marker_path), so it never perturbs this."""
    try:
        def g(args):
            return subprocess.run(["git", "-C", str(project_dir), *args],
                                  capture_output=True, text=True, timeout=15).stdout
        if git_dir(project_dir) is None:
            return ""
        blob = g(["rev-parse", "HEAD"]) + g(["status", "--porcelain"]) + g(["diff"])
        return hashlib.sha256(blob.encode("utf-8", "replace")).hexdigest()
    except Exception:
        return ""


def marker_path(project_dir):
    gd = git_dir(project_dir)
    return (gd / "factory-validate-marker") if gd else None


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("stop_hook_active"):
        return 0  # already inside a stop-hook continuation — don't loop

    cfg_path = find_config()
    if not cfg_path:
        return 0
    try:
        cfg = json.loads(cfg_path.read_text())
    except Exception:
        return 0
    quality = cfg.get("quality") or {}
    if quality.get("validate_on_stop") is False:
        return 0  # explicitly disabled
    project_dir = cfg_path.parent

    # Skip if nothing changed since the last green validation.
    marker = marker_path(project_dir)
    fp = tree_fingerprint(project_dir)
    if fp and marker and marker.exists():
        try:
            if marker.read_text().strip() == fp:
                return 0
        except Exception:
            pass

    for label, key in (("tests", "test_cmd"), ("typecheck", "typecheck_cmd")):
        cmd = quality.get(key)
        if not cmd:
            continue
        try:
            res = subprocess.run(cmd, shell=True, cwd=project_dir,
                                 capture_output=True, text=True, timeout=270)
        except Exception as e:
            sys.stderr.write(
                f"[validate-on-stop] could not run {label} (`{cmd}`): {e}. "
                "Not enforcing this turn — fix the command so the gate works.\n")
            return 0  # fail open, but visibly
        if res.returncode != 0:
            tail = (res.stdout + res.stderr).strip().splitlines()[-25:]
            sys.stderr.write(
                f"BLOCKED by validate-on-stop: {label} failed (`{cmd}`).\n"
                "Fix it before finishing — evidence before done.\n\n"
                + "\n".join(tail) + "\n")
            return 2

    # All gates green — record the post-validation tree state so identical
    # follow-up turns skip re-running.
    if fp and marker:
        try:
            marker.write_text(tree_fingerprint(project_dir))
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
