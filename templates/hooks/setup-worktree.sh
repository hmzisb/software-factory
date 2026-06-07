#!/usr/bin/env bash
# SubagentStart hook: create an isolated git worktree for a developer agent.
# Portable + FAIL-OPEN: no-ops (exit 0) for non-developer agents, outside a git
# repo, or on any error — it must never block the agent. See
# rules/worktree-promotion.md for the full session/promotion model.
set -u

STDIN=$(cat 2>/dev/null || true)
AGENT=$(printf '%s' "$STDIN" | python3 -c '
import sys, json
try:
    print(json.load(sys.stdin).get("agent_type", ""))
except Exception:
    print("")
' 2>/dev/null || echo "")

case "$AGENT" in
  *developer*) : ;;          # developer or simple-developer → proceed
  *) exit 0 ;;               # any other agent → no-op
esac

git rev-parse --git-dir >/dev/null 2>&1 || exit 0   # not a git repo → no-op

TASK=$(printf '%s' "$AGENT" | grep -oE 'TASK-[0-9]+' || true)
SLUG="${TASK:-$AGENT}"

# Branch naming matches rules/worktree-promotion.md:
#  * single session (default): flat  factory/<task>
#  * parallel sessions: set FACTORY_SESSION=<id> → <id>/<task>, forked under the
#    session integration branch the orchestrator created (session/<id>).
if [ -n "${FACTORY_SESSION:-}" ]; then
  BRANCH="${FACTORY_SESSION}/${SLUG}"
  WT="worktrees/${FACTORY_SESSION}/${SLUG}"
else
  BRANCH="factory/${SLUG}"
  WT="worktrees/${SLUG}"
fi

# already set up for this run
[ -e "$WT/.git" ] && exit 0
git worktree list --porcelain 2>/dev/null | grep -qF "worktree $(pwd)/$WT" && exit 0

mkdir -p worktrees

# If a branch from a previous run exists, only remove it when git confirms it is
# fully merged (safe delete, -d). If it still holds unmerged commits, DO NOT
# discard them — fork a uniquely-suffixed branch/worktree so the prior work
# survives for recovery. Never lose work (see rules/worktree-promotion.md).
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  if ! git branch -d "$BRANCH" >/dev/null 2>&1; then
    i=2
    while git show-ref --verify --quiet "refs/heads/${BRANCH}-${i}"; do i=$((i+1)); done
    BRANCH="${BRANCH}-${i}"
    WT="${WT}-${i}"
  fi
fi

if git worktree add "$WT" -b "$BRANCH" >/dev/null 2>&1; then
  echo "[setup-worktree] $WT on $BRANCH" >&2
else
  echo "[setup-worktree] could not create $WT (continuing without isolation)" >&2
fi
exit 0
