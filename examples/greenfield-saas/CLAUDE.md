# Tasker

A minimal team task tracker.

> This file is the operating manual for the **software factory** that builds and
> maintains this project. It is auto-loaded every turn — keep it lean. Details
> live in `.claude/rules/*`, `CONTEXT.md`, and `docs/`, loaded on demand.

## What this is

- **Problem:** Small teams lose tasks in chat.
- **Users:** 5-person product teams.
- **Success:** Every task has an owner and a state.
- **Specialization:** domain — team productivity

Domain language lives in `CONTEXT.md`. Read it before touching domain code.

## Stack

- Language: typescript
- Framework: next
- Database: postgres
- Package manager: pnpm

## How the factory works

A request flows through the agent team, led by the orchestrator:

```
/factory-build "<request>"
  orchestrator: classify (simple | complex)
    simple  -> one developer, in a worktree -> verify -> merge
    complex -> planner: vertical-slice tickets, dependency waves
            -> per ticket (isolated worktree): developer (TDD)
                 -> reviewer + test-validator -> merger
            -> verify gate -> documentator updates CONTEXT/ADR/learnings
  -> definition-of-done gate
```

Wave size **N = 3**. A wave dispatches **10** agents (3 developers + 6 reviewers + 1 merger).

### Agents

| Agent | Model | Role |
|---|---|---|
| orchestrator | sonnet | Classifies, plans, dispatches, gates, reports. Never edits. |
| planner | sonnet | Decomposes a request into vertical-slice tickets in waves. |
| developer | opus | Implements one ticket in a worktree, TDD-first, commits. |
| reviewer | sonnet | Semantic + security review of the diff. |
| test-validator | sonnet | Confirms the change is adequately tested. |
| merger | haiku | The only agent that merges (`--no-ff`). |
| documentator | sonnet | Updates CONTEXT.md / ADRs / learnings after merge. |

Autonomy level: **semi-autonomous**.

## Validation (the gate)

Every change must pass, before review/merge:

```
pnpm test
pnpm run typecheck
pnpm run lint
pnpm run build
```

A change is "done" only when it meets `definition-of-done.md`.

## Hard rules

- **Worktree isolation.** Each ticket works in its own git worktree under
  `worktrees/`. Never edit the base checkout while a worktree is open.
- **The orchestrator never edits files or runs git writes** — it dispatches.
- **The merger is the only agent that merges.** Developers commit in worktrees.
- **TDD.** Write the failing test first (`.claude/skills/tdd`).
- **Evidence before "done".** Run the command, show the output
  (`.claude/skills/verification`). Never claim passing without proof.
- **Context budget.** Keep primary context under ~100k tokens. Push heavy reads
  (large files, broad greps) into subagents that return only the relevant slice.
- **Security boundaries** (`.claude/rules/security.md`): validate at boundaries,
  never commit secrets, respect auth/scope.
- **Cost** (`.claude/rules/cost-controls.md`): model-tier per role; per-request
  budget $10 (pause and ask before exceeding); prefer the
  SIMPLE path.
- **Non-coder UX** (`.claude/rules/non-coder-ux.md`): when a non-technical user
  drives, reply only in plain language; support undo / cleanup / recovery.

## Discipline

Discipline is vendored in `.claude/skills/` (tdd, verification, writing-plans, brainstorming, worktrees) — no external plugins required.

## Map

- `CONTEXT.md` — domain entities, glossary, workflows.
- `.claude/agents/` — the team. `.claude/commands/` — entry points.
- `.claude/rules/` — coding-style, testing, security, validation-commands, scope, triage-labels, cost-controls, non-coder-ux, data-modes, worktree-promotion.
- `.claude/skills/` — vendored discipline (tdd, verification, writing-plans, brainstorming, worktrees, writing-migrations, visual-testing, handoff).
- `specs/` — PRDs. `plans/` — execution plans / tickets.
- `docs/adr/` — architecture decisions. `docs/learnings/` — captured patterns.
- `MEMORY.md` — cross-session project memory + session index. `docs/sessions/` — per-session handoffs (`/factory-handoff`, `/factory-resume`).
- `db/migrations/` — ordered migrations (full mode). `db/migrate.sh` (generate/apply) + `db/provision.sh` (one-time backend setup). `deploy/deploy.sh` — gated deploy to vercel.

Layer 0 (dev harness) only. Layer 1 (product factory) not generated.
