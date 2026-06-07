# Worktree & promotion protocol

How parallel agent work stays isolated and integrates safely — the crm-builder
model, generalized. Two levels: per-ticket isolation (always) and the
session/promotion layer (for parallel/multi-session use, e.g. Layer 1).

## Per-ticket isolation (always — automated by the hook)

- Each ticket runs in its own worktree on its own branch.
- The `setup-worktree` hook creates it on developer start; `cleanup-worktree`
  prunes on merger stop. Branch/worktree names it produces:
  - **single session (default):** `factory/<task>` in `worktrees/<task>/`
  - **parallel sessions:** export `FACTORY_SESSION=<id>` and the hook produces
    `<id>/<task>` in `worktrees/<id>/<task>/`.
  - If a same-named branch from a dead run still holds unmerged commits, the hook
    does **not** delete it — it forks a `-2`/`-3` suffix so that work survives.
- A developer edits only inside its worktree; the base checkout is never touched
  while a worktree is open.

## Session + promotion layer (parallel / Layer 1 — orchestrator-driven)

The hook automates per-ticket isolation only. The session integration + promotion
 refs below are created and moved by the **orchestrator and merger** (the hook
can't know the session id at the moment a developer starts), following this
protocol so parallel requests never collide and migrations diff cleanly:

```
default branch (main)
  └─ session/<id>            integration branch for one request/session
       ├─ session-base/<id>  FIXED anchor ref (never moves) — the diff baseline
       └─ <id>/TASK-XXX       per-ticket branches (the hook makes these when
                              FACTORY_SESSION=<id>), merged into session/<id>
```

- **Session start** (orchestrator): create `session/<id>` off the default branch
  and a fixed `session-base/<id>` anchor at the same commit; export
  `FACTORY_SESSION=<id>` for the developers it dispatches.
- **Stage A** (merger): merge each `<id>/TASK-XXX` → `session/<id>` (in a dedicated
  `_session` worktree). Single shared merger per wave avoids `.git/index.lock`
  contention.
- **Stage B** (promotion): merge `session/<id>` → the default branch **under a
  lock** (`flock <repo>/.promote.lock`) so concurrent sessions serialize. Promote
  once per request.
- **`session-base/<id>`** never moves: migrations are generated from
  `git diff session-base/<id>..session/<id>` so a session's migration captures
  only that session's schema change, not other sessions' work.

## Rules

- Only the `merger` merges/promotes. Developers commit in worktrees.
- Never `reset --hard` / force-push / rewrite history (guardrail hook blocks it).
- On a crash/usage-limit mid-wave, recover from disk: re-check which task branches
  merged into `session/<id>`, which worktrees hold uncommitted work, and resume —
  never restart finished tickets (see `non-coder-ux.md` RECOVERY).
- Clean up worktrees after promotion (`git worktree prune`).
