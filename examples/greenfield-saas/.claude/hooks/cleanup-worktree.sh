#!/usr/bin/env bash
# SubagentStop hook (merger): prune merged/stale worktrees. FAIL-OPEN.
set -u
git rev-parse --git-dir >/dev/null 2>&1 || exit 0
git worktree prune >/dev/null 2>&1 || true
exit 0
