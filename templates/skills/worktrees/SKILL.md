---
name: worktrees
description: Isolate each ticket in its own git worktree so parallel work never collides. Use when starting implementation of a ticket or running multiple agents at once.
---

# Git worktrees

Vendored, self-contained. (If `superpowers` is installed, prefer its
`using-git-worktrees` skill.)

## Why

Each ticket gets an isolated checkout, so parallel developers never fight over
the working tree or the index, and an abandoned attempt is trivial to discard.

## Create

```bash
git worktree add worktrees/<branch> -b <branch>    # new branch off HEAD
```

Work happens entirely inside `worktrees/<branch>/`. Bash is stateless between
calls — every command starts with `cd worktrees/<branch> && ...`.

## Rules

- Never edit the base checkout while a worktree is open for the same area.
- Commit inside the worktree. The `merger` agent merges the branch back with
  `--no-ff`; developers do not merge.
- One ticket → one worktree → one branch.

## Clean up

```bash
git worktree remove worktrees/<branch>     # after the branch is merged
git worktree prune
```

If `remove` complains about changes, the branch wasn't merged — resolve before
discarding.

## Automation + the promotion model

The `setup-worktree` / `cleanup-worktree` hooks (wired in `settings.json`) create
a worktree on developer start and prune on merger stop, so isolation is automatic.
For parallel / multi-session work (Layer 1), use the full session-branch +
`session-base` anchor + promote-under-`flock` model in
`.claude/rules/worktree-promotion.md`.

