# Factory anatomy

What a generated software factory contains, why each artifact exists, and how it
maps to the canonical real-world factory (`marmelab/crm-builder`).

A factory has two layers. **Layer 0** (dev harness) is always generated.
**Layer 1** (product factory) is optional.

---

## Layer 0 — the dev harness

The harness Claude Code reads to plan, build, review, test, and ship features in
*this* project. Everything here is stack-neutral and self-contained.

### `CLAUDE.md` — the operating manual

Auto-loaded by Claude Code on every turn. Keep it lean (it's always in context).
Contains: a one-paragraph product description, the runtime/architecture map, the
**agent table** (who does what, which model), the **hook table** (what's blocked
when), hard invariants, the validation commands, and the "keep primary context
< 100k tokens; push heavy reads into subagents" rule.

> crm-builder: `CLAUDE.md` (runtime diagram, agent table, hook list, gotchas).
> mattpocock: operational `CLAUDE.md`/`AGENTS.md` with a `## Agent skills` block.

### `CONTEXT.md` — domain shared language

The ubiquitous language of the domain: entities, a glossary, and the key
workflows. Prevents the agent from inventing inconsistent terms (mattpocock's
fix for "verbosity / drift"). The documentator keeps it current.

> mattpocock: `CONTEXT.md` (single-context) or `CONTEXT-MAP.md` (monorepo).

### `.claude/agents/*` — the specialized team

One file per role. The orchestrator leads; the rest are dispatched per ticket.

| Agent | Role |
|---|---|
| `orchestrator` | Classifies a request (simple/complex), plans waves, dispatches the team, reports. Never edits files itself. Runs a strict per-turn state machine. |
| `planner` | Decomposes a request into vertical-slice tickets with dependency waves + file hints. |
| `developer` | Implements one ticket in an isolated worktree, TDD-first, commits. Writes an ADR when a structural decision is made. |
| `reviewer` | Semantic code + security review. Does not re-run validation (hooks do). |
| `test-validator` | Confirms tests exist and wire up; checks coverage of the change. |
| `merger` | `git merge --no-ff` only. Never `git add`/`commit`. Single shared merger avoids index-lock contention. |
| `documentator` | Updates `CONTEXT.md`, `docs/adr/`, `docs/learnings/` from the merged diff. |

> crm-builder: chat-orchestrator, planner, developer, simple-developer,
> quality-reviewer, test-validator, merger, documentator. Wave = `3N+1` agents
> (N dev + 2N reviewers + 1 merger), N ≤ 5.

### `.claude/commands/*` — the factory's entry points

Slash commands a human (or CI) runs:
`/factory-build "<request>"` (full loop), `/factory-plan`, `/factory-verify`
(run the gates), `/factory-ship` (merge → PR/deploy).

### `.claude/skills/*` — vendored discipline

Minimal, self-contained rewrites of the disciplines the factory depends on, so
it works with no plugins:
- `tdd` — red → green → refactor.
- `verification` — evidence before "done"; run the command, show the output.
- `writing-plans` — turn a spec into an ordered, reviewable plan.
- `brainstorming` — explore intent before building.
- `worktrees` — isolate each ticket in its own git worktree.

If `superpowers`/`mattpocock` are installed, `CLAUDE.md` links to them instead.

> superpowers: brainstorming, writing-plans, test-driven-development,
> verification-before-completion, using-git-worktrees.

### `.claude/rules/*` — modular rules

Small, focused files the agents load as needed: `coding-style.md`,
`testing.md`, `security.md`, `validation-commands.md` (the exact build/test/lint
commands), `scope.md` (worktree scope, what's off-limits). A 5-state triage
vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`,
`wontfix`) lives here too.

> crm-builder: rules/coding-style, testing, typescript, security-triggers,
> validation-commands, web-security, worktree-scope. mattpocock: triage labels.

### `.claude/hooks/*` + `settings.json` — guardrails

Deterministic enforcement the model can't talk its way past:
- `block-bash-write` — no file writes via Bash (forces Write/Edit, which hooks see).
- `validate-before-review` — typecheck + lint + tests must pass before a dev can
  hand off to review/merge.
- `run-tests`, `typecheck-on-commit` — post-change validation.
- `setup-worktree` / `cleanup-worktree` — worktree lifecycle.

Each hook ships with a matching test in `hooks/test/`.

> crm-builder: ~25 hooks wired in `settings.json`, with `hooks/test/*`.

### `docs/adr/`, `docs/learnings/`

`adr/` = Architecture Decision Records (one per structural decision).
`learnings/patterns.md` = recurring frictions captured by the documentator.

### `specs/`, `plans/`

`specs/` = PRDs / feature specs (the "what"). `plans/` = ordered execution plans
/ vertical-slice tickets (the "how"). The `to-prd → to-issues` pipeline.

### `eval/` — probabilistic validation

The distinctive factory bit. From the article: *"a feature is only 'done' when
the factory produces the right result on a large number of tries."*

- `cases.json` — `[{id, prompt, expect:{files, mustInvoke, mustNotInvoke,
  checks, maxCostUsd}}]`.
- `run.py` — runs each case **N times** (default 5), records success rate, cost,
  duration, diff; compares to `baseline.json`; exits non-zero on regression.
- `baseline.json` — the known-good snapshot.

> crm-builder: `chat-service/tests/` — `cases.json` + `run.js` + `baseline.json`
> + Playwright `checks/` + diff-capture.

### `.github/workflows/factory-ci.yml`

Runs the validation gates on every PR; runs the eval on a schedule/label.

### `definition-of-done.md`

The explicit bar: tests pass, typecheck clean, reviewed, ADR written if
structural, CONTEXT.md updated, eval case green at target rate.

---

## Layer 1 — the product factory (optional)

Generated only on request. Turns the repo into a marmelab-style **self-modifying
product**: non-coders describe changes in plain language and the factory ships
them. Adds:

- A **builder UI** (chat) the end user talks to.
- A **user-facing orchestrator** that speaks plain language (never exposes file
  paths/agent names), classifies requests, and drives the Layer 0 team.
- **Container isolation** (Docker) so the factory can run with
  `--dangerously-skip-permissions` safely.
- A **deploy pipeline** (build → migrate → ship) gated behind a satisfaction
  check.
- A **template** the factory modifies (the marmelab "avoid reinventing the
  wheel" base).

> crm-builder: `chat-service/` (WS server spawning `claude -p` + builder UI),
> Docker + supervisord, `app-variants/` (Atomic CRM template), deploy-routes.

See `layer1-product-factory.md` for the detailed shape.

---

## The specialization principle

Per the article, a factory's failure rate drops toward zero as its scope
narrows. The interview captures the **job** (e.g. recruitment) or **domain**
(e.g. bike rental) so the generated `CONTEXT.md`, rules, and agent prompts encode
that specific knowledge — not a general-purpose harness that needs constant
supervision.
