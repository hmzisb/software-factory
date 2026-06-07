#!/usr/bin/env python3
"""PreToolUse/Bash guardrail: block irreversible git/file commands.

Reads the Claude Code hook JSON on stdin. Exit 2 + stderr blocks the call and
shows the reason to the model. Fail-open on malformed input (never brick the
agent over a parse error).

This is a BEST-EFFORT heuristic, not a security boundary: it pattern-matches
common footguns, but a determined or obfuscated command can evade it. Treat it
as a seatbelt (catches the obvious mistakes), not a sandbox. The real isolation
is the worktree + human review + (for Layer 1) the container.
"""
import json
import re
import sys

DANGEROUS = [
    # --- git history / data destruction ---
    (r"\bgit\s+push\b[^\n|&;]*--force(?!-with-lease)", "git push --force (use --force-with-lease, or don't)"),
    (r"\bgit\s+push\b[^\n|&;]*\s-f\b", "git push -f"),
    (r"\bgit\s+push\b[^\n|&;]*\s(?:main|master)\b[^\n|&;]*--force", "force push to a protected branch"),
    (r"\bgit\s+push\b[^\n|&;]*--mirror", "git push --mirror (can delete remote refs)"),
    (r"\bgit\s+push\b[^\n|&;]*--delete", "git push --delete (deletes a remote ref)"),
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard (discards work irreversibly)"),
    (r"\bgit\s+clean\s+-[a-z]*f", "git clean -f (deletes untracked files)"),
    (r"\bgit\s+branch\s+-D\b", "git branch -D (force-deletes a branch)"),
    (r"\bgit\s+checkout\s+(?:--\s+)?\.\s*(?:$|[|&;])", "git checkout . (mass-discards changes)"),
    (r"\bgit\s+restore\s+(?:--\s+)?\.\s*(?:$|[|&;])", "git restore . (mass-discards changes)"),
    (r"\bgit\s+stash\s+clear\b", "git stash clear (drops all stashes)"),
    (r"\bgit\s+reflog\s+expire\b", "git reflog expire (destroys recovery refs)"),
    (r"\bgit\s+gc\b[^\n]*--prune\s*=\s*(?:now|all)", "git gc --prune=now (drops unreachable objects)"),
    (r"\bgit\s+update-ref\s+-d\b", "git update-ref -d (deletes a ref)"),
    # --- filesystem destruction ---
    (r"\brm\s+-[a-zA-Z]*[rf][a-zA-Z]*(?:\s+-[a-zA-Z]+)*\s+(?:/|~|\$HOME|\*|\.\.?)(?:\s|;|&|\||$)",
     "rm -rf of a dangerous path (/, ~, $HOME, *, ., ..)"),
]


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("tool_name") != "Bash":
        return 0
    cmd = (data.get("tool_input") or {}).get("command", "") or ""
    for pattern, reason in DANGEROUS:
        if re.search(pattern, cmd):
            sys.stderr.write(
                f"BLOCKED by block-dangerous-git: {reason}.\n"
                f"Command: {cmd}\n"
                "If this is truly intended, ask the human to run it manually.\n")
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
