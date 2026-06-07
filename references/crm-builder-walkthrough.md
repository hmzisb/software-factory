# Worked example — `marmelab/crm-builder`

`crm-builder` is the canonical real-world software factory and the reference this
skill generalizes. This maps its parts onto what `software-factory` generates, so
you can see where a generated factory is the same idea and where crm-builder goes
further (production-grade).

## crm-builder at a glance

A Dockerised sandbox where non-technical users describe CRM changes in chat and
an agent team ships them in isolated git worktrees. Template: Atomic CRM
(React + shadcn/ui + Supabase). Harness: `claudeConfig/.claude/` + a Node
`chat-service` + a probabilistic eval rig.

## Mapping

| crm-builder | software-factory generates | Notes |
|---|---|---|
| `CLAUDE.md` (runtime, agent table, hooks, gotchas) | `CLAUDE.md` | Same role: the always-loaded operating manual. |
| `claudeConfig/.claude/agents/*` (chat-orchestrator, planner, developer, simple-developer, quality-reviewer, test-validator, merger, documentator) | `.claude/agents/*` (orchestrator, planner, developer, reviewer, test-validator, merger, documentator) | We fold simple-developer into the orchestrator's SIMPLE path. |
| `chat-orchestrator.md` strict per-turn state machine (SIMPLE/COMPLEX/SETUP/MEMORY/MODE-SWITCH; wave = 3N+1) | orchestrator's classify -> plan -> wave -> verify loop; `3N+1` wave math | Ours is slimmer; same backbone. |
| `skills/` (setup-interview, agent-team, adr-writing, writing-migrations, …) | the skill's own `references/interview.md` + vendored `.claude/skills/*` (tdd, verification, writing-plans, brainstorming, worktrees) | crm-builder's setup-interview is the model for our interview. |
| `rules/*` (coding-style, testing, typescript, security-triggers, validation-commands, worktree-scope, …) | `.claude/rules/*` (coding-style, testing, security, validation-commands, scope, triage-labels) | Same modular-rules idea, stack-neutral. |
| ~25 `hooks/*` + `settings.json`, with `hooks/test/*` | `.claude/hooks/*` (block-dangerous-git, protect-secrets, validate-on-stop) + `settings.json`, tested at skill level | crm-builder's hook set is larger and worktree-aware; ours is the portable core. |
| `app-variants/App.{fakerest,supabase}.tsx` (the template) | — (bring-your-own template / greenfield scaffold) | Layer 1 here is generic, not CRM-specific. |
| `chat-service/` (WS server spawning `claude -p`, builder UI, deploy modal, sessions, recovery) | Layer 1 `builder/server.py` + `builder/index.html` + `builder-orchestrator` | Ours is a minimal stdlib version of the same thing. |
| `chat-service/tests/` (cases.json + run.js + baseline.json + Playwright checks + diff-capture) | `eval/` (cases.json + run.py + baseline.json) | Same probabilistic bar; ours is stack-neutral Python. |
| `docs/learnings/patterns.md` + `MEMORY.md` (documentator) | `docs/learnings/patterns.md` + `CONTEXT.md` (documentator) | Same capture loop. |
| Docker + supervisord + worktree-per-ticket + session-branch promotion | Layer 1 Docker + vendored `worktrees` skill | crm-builder's branch/promotion machinery is the production version. |

## What crm-builder does that a generated factory doesn't (yet)

- Multi-session parallelism with per-session worktree namespaces and a single
  shared merger to avoid `.git/index.lock` contention.
- Streaming WS UI, cost/token stats, crash/usage-limit **recovery** replay.
- A deploy modal with staged build -> supabase link -> db push -> functions ->
  secrets -> wrangler, gated on full config.
- Demo (FakeRest) vs full (Supabase) **mode switch**.

These are the natural next steps when hardening a generated Layer 1 — crm-builder
is the blueprint to copy from.

## How to study it

```bash
git clone --depth 1 https://github.com/marmelab/crm-builder
# the harness:
ls crm-builder/claudeConfig/.claude/{agents,skills,rules,hooks}
# the eval rig:
ls crm-builder/chat-service/tests
```
