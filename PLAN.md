# `software-factory` — a Claude skill that scaffolds a software factory for any project

> **What it is.** A single Claude Code skill. You invoke it in any directory
> (empty or an existing repo), it **interviews you**, then **deterministically
> scaffolds a complete "software factory"**: every file Claude Code needs to
> then build and maintain the whole software autonomously — CLAUDE.md, agents,
> commands, rules, guardrail hooks, specs, plans, a definition-of-done, a
> probabilistic eval harness, CI, and docs.
>
> Open-source-first: MIT, self-contained (zero plugin dependencies), shareable
> on GitHub and reusable across all your own projects.

---

## 0. Source of the idea

Distilled from three things, then made self-contained:

1. **marmelab — "Agentic Software Factories: The Future of Programming?"**
   (blog, May 2026) + its reference implementation **`marmelab/crm-builder`**
   (cloned + read in full at `/tmp/factory-research/crm-builder`). This is the
   concrete blueprint for *what a factory contains*.
2. **`superpowers`** (obra/Jesse Vincent) — the engineering *discipline*:
   brainstorm → writing-plans → TDD → verification-before-completion,
   subagent-driven development, git-worktree isolation.
3. **`mattpocock/skills`** (Matt Pocock, "Skills for Real Engineers") — the
   *context engineering*: operational `CLAUDE.md`, domain `CONTEXT.md`,
   `docs/adr/`, `to-prd → to-issues` vertical slices, 5-state triage, `handoff`,
   sub-100k-token context budgets via subagents.

### What the article actually says a factory is

> "software that builds software" — a **harness** (skills + tools + domain
> knowledge given to an AI) + a **template** + a **team of specialized agents
> led by an orchestrator** + **probabilistic validation** ("a feature is only
> 'done' when the factory produces the right result on a large number of
> tries"). Specialize by **job** or **domain** to drive the failure rate toward
> zero. The human stays essential: identify problems, rank solutions, criticize
> results.

### Factory anatomy, reverse-engineered from `crm-builder`

The whole harness lives in `claudeConfig/.claude/` + a runtime + an eval rig:

| Part | In crm-builder | Generalized for the skill |
|---|---|---|
| **Master context** | `CLAUDE.md` (runtime, invariants, agent table, hooks, gotchas) | `CLAUDE.md` (operating manual for the factory) |
| **Agent team** | `agents/`: chat-orchestrator, planner, developer, simple-developer, quality-reviewer, test-validator, merger, documentator | orchestrator + planner + developer + reviewer + test-validator + merger + documentator (stack-neutral) |
| **Skills** | `skills/`: setup-interview, agent-team, adr-writing, writing-migrations, e2e-conventions, playwright-testing, worktree-detection, shadcn-customization | vendored discipline skills (tdd, verification, writing-plans, brainstorming, worktree) + project-specific stubs |
| **Rules** | `rules/`: coding-style, testing, typescript, security-triggers, validation-commands, web-security, worktree-scope, english-only, agent-output-format | modular `rules/*.md` (coding-style, testing, security, validation-commands, scope) |
| **Guardrail hooks** | ~25 hooks in `hooks/` wired in `settings.json` (block-bash-write, block-migration-writes, circuit-breaker, validate-before-review, setup/cleanup-worktree, run-tests, typecheck-on-commit) + they **test their hooks** | a small, portable hook set + `settings.json`, each with a matching test |
| **Template** | `app-variants/App.{fakerest,supabase}.tsx` (Atomic CRM base) | optional: a starter template per stack, or "bring your own" |
| **Probabilistic eval** | `chat-service/tests/`: `cases.json` + `run.js` + `baseline.json` + Playwright `checks/` + diff-capture | stack-agnostic `eval/`: `cases.json` + a thin runner that re-runs N times and diffs against `baseline.json` |
| **Memory / learnings** | `docs/learnings/patterns.md` + `MEMORY.md` (documentator-maintained) | `docs/learnings/` + `CONTEXT.md` + `docs/adr/` |
| **Runtime / isolation** | Docker + supervisord + `chat-service` WS UI; git worktrees per ticket | git worktrees (always); Docker + builder UI only in the optional product-factory layer |
| **Orchestration** | `chat-orchestrator.md` strict per-turn **state machine** (SIMPLE / COMPLEX / SETUP / MEMORY / MODE-SWITCH; wave = `3N+1` agents) | a slimmer orchestrator state machine: classify → plan → wave (dev+review+test+merge) → verify → done |

---

## 1. Design decisions (locked with the user)

| # | Decision | Choice |
|---|---|---|
| 1 | Factory type | **Both, layered.** Layer 0 (dev harness) always generated. Layer 1 (marmelab-style product factory: deployable self-modifying app + builder UI + orchestrator the *end user* talks to) is optional, generated on request. |
| 2 | Target projects | **Both, auto-detect.** Empty dir → greenfield scaffold. Existing repo → retrofit (analyze stack, graft the harness onto what's there, never clobber). |
| 3 | Dependency posture | **Vendor discipline inline.** Generated factory is self-contained; works with zero plugins installed. If `superpowers` / `mattpocock` skills are detected, prefer/reference them — but never require them. |

### Defaults chosen by the skill (overridable in the interview)

- **Determinism:** scaffolding is a **deterministic Python script** (`scaffold.py`)
  driven by a validated `factory.config.json`, not free-form LLM file-writing.
  Same answers → byte-identical tree. (The article's reproducibility principle.)
- **Eval harness is stack-agnostic:** the generated runner shells out to the
  *project's own* build/test/lint commands (captured in the interview), repeats
  a case N times, and scores success rate vs a baseline.
- **Worktree isolation always on** (vendored), Docker only for Layer 1.

---

## 2. The skill's own structure (what we build, here in this repo)

```
skills/software-factory/
  SKILL.md                       # entrypoint: when-to-use + the runtime algorithm
  PLAN.md                        # this file
  README.md                      # open-source front door + install
  LICENSE                        # MIT
  references/
    factory-anatomy.md           # the table above, expanded — what/why each artifact
    interview.md                 # full domain-by-domain question bank + auto-detect rules
    scaffold-algorithm.md        # greenfield vs retrofit logic, merge/no-clobber rules
    layer1-product-factory.md    # optional self-modifying-app layer (orchestrator+UI+deploy+eval)
    crm-builder-walkthrough.md   # the worked demo: how crm-builder maps onto a generated factory
    open-source-checklist.md     # packaging, naming, GitHub release steps
  templates/                     # the harness files stamped into the TARGET project
    CLAUDE.md.tmpl
    CONTEXT.md.tmpl
    definition-of-done.md.tmpl
    factory.config.schema.json
    agents/{orchestrator,planner,developer,reviewer,test-validator,merger,documentator}.md.tmpl
    commands/{factory-build,factory-plan,factory-verify,factory-ship}.md.tmpl
    skills/{tdd,verification,writing-plans,brainstorming,worktrees}/SKILL.md   # vendored, minimal, self-contained
    rules/{coding-style,testing,security,validation-commands,scope}.md.tmpl
    hooks/{block-bash-write,validate-before-review,run-tests,setup-worktree,cleanup-worktree,typecheck-on-commit}.sh.tmpl
    hooks/test/*.test.sh.tmpl
    settings.json.tmpl
    docs/adr/0000-record-architecture-decisions.md.tmpl
    docs/learnings/patterns.md.tmpl
    specs/.gitkeep + spec.template.md
    plans/.gitkeep
    eval/{cases.json.tmpl, run.py.tmpl, baseline.json.tmpl, README.md.tmpl}
    .github/workflows/factory-ci.yml.tmpl
    layer1/                       # only stamped when product-factory layer is requested
      Dockerfile.tmpl, docker-compose.yml.tmpl, builder-ui/..., deploy/...
  scripts/
    scaffold.py                  # deterministic file-stamper (config -> tree)
    detect.py                    # empty-vs-existing + stack detection
  tests/
    test_scaffold.py             # greenfield + retrofit golden-file tests
    test_detect.py
  examples/
    greenfield-saas/             # a committed sample of a generated factory
```

**Repo conventions followed** (from existing skills here): `SKILL.md` with YAML
frontmatter (`name`, `description`); install via symlink
`ln -s "$PWD/skills/software-factory" ~/.claude/skills/software-factory`;
each skill self-contained; tests under `tests/`; documented in the root README.

---

## 3. Runtime behaviour (what the skill does when invoked)

```
/software-factory
  │
  ├─ 1. DETECT      scripts/detect.py
  │     empty dir            -> GREENFIELD
  │     existing repo        -> RETROFIT (read package.json/pyproject/go.mod/...,
  │                             test+build+lint commands, languages, CI present?)
  │     factory.config.json exists -> RESUME / UPDATE
  │
  ├─ 2. INTERVIEW   references/interview.md  (one domain per turn, summarize+confirm)
  │     D1 Product   : one-liner, problem, users, success metric
  │     D2 Domain    : entities, glossary (-> CONTEXT.md), key workflows
  │     D3 Stack     : language/framework/db (detected default in RETROFIT), package mgr
  │     D4 Quality   : test framework, build cmd, lint cmd, typecheck cmd  (-> validation-commands.md, DoD, eval runner)
  │     D5 NFRs      : security boundaries, perf budget, accessibility, i18n
  │     D6 Delivery  : git host, CI, deploy target, environments
  │     D7 Factory   : Layer 0 only, or + Layer 1 product-factory? agent-team size? autonomy level?
  │     D8 Seed      : generate the first PRD + vertical-slice issues now? (to-prd -> to-issues)
  │     -> writes/validates factory.config.json (validated:true, consistency checks)
  │
  ├─ 3. SCAFFOLD    scripts/scaffold.py factory.config.json
  │     stamps templates/ -> target tree.
  │     GREENFIELD : write everything (git init if needed).
  │     RETROFIT   : merge, NEVER clobber. Append a managed block to an existing
  │                  CLAUDE.md; add .claude/ only where absent; back up before edit;
  │                  print a diff summary of what was added vs skipped.
  │
  ├─ 4. (optional) SEED   to-prd -> specs/0001-*.md -> plans/ + tracker issues
  │
  └─ 5. NEXT STEPS  print: how to run the factory (/factory-build), how to run the
                    eval (eval/run.py), how to install the optional plugins it can use.
```

### The generated factory's own loop (Layer 0)

```
/factory-build "<feature request>"
   classify (simple vs complex)
   -> plan (planner agent -> tickets/vertical slices, waves by dependency)
   -> per ticket, in an isolated worktree: developer (TDD) -> reviewer + test-validator -> merger
   -> verify (run validation-commands; block merge on failure via hook)
   -> documentator updates CONTEXT.md / docs/adr / learnings
   -> definition-of-done gate
```

### Probabilistic validation (the distinctive factory bit)

`eval/cases.json` = list of `{id, prompt, expect:{files, mustInvoke, mustNotInvoke,
checks, maxCostUsd}}`. `eval/run.py` runs each case **N times** (default 5),
records success rate + cost + duration, compares to `eval/baseline.json`, and
exits non-zero on regression. A feature is "done" only when its case passes at
the target rate across N tries — exactly the article's bar. Wired into CI.

---

## 4. How the three sources are vendored (decision 3)

- **superpowers discipline** → `templates/skills/{tdd,verification,writing-plans,
  brainstorming,worktrees}/SKILL.md`: minimal, self-contained rewrites (not
  copies) so the generated project has the red-green-refactor + evidence-before-
  assertion + worktree discipline with no plugin install. If superpowers is
  detected, the generated CLAUDE.md links to it instead.
- **mattpocock context engineering** → the `CLAUDE.md`/`CONTEXT.md`/`docs/adr/`
  layout, the `to-prd → to-issues` seed step, the 5-state triage vocabulary in
  `rules/`, the `handoff` command, and the explicit "keep primary context
  <100k; push heavy reads into subagents" instruction in the orchestrator.
- **marmelab factory** → the agent team + orchestrator state machine + guardrail
  hooks + worktree-per-ticket + eval harness + (Layer 1) the Docker builder UI.

---

## 5. Build plan (phases — commit after each)

| Phase | Deliverable | Verify |
|---|---|---|
| **P0** | Skill skeleton: `SKILL.md`, `README.md`, `LICENSE`, `references/factory-anatomy.md`, `factory.config.schema.json` | SKILL.md frontmatter valid; loads as a skill |
| **P1** | `references/interview.md` (full question bank) + `references/scaffold-algorithm.md` + config schema finalized | self-review against crm-builder's setup-interview |
| **P2** | Layer 0 `templates/` — CLAUDE.md, CONTEXT.md, agents, commands, rules, vendored discipline skills, DoD | render templates with a sample config by hand |
| **P3** | `scripts/detect.py` + `scripts/scaffold.py` + `tests/` (golden-file greenfield & retrofit) | `pytest` green; no-clobber proven |
| **P4** | Guardrail hooks + `settings.json.tmpl` + hook tests | hook tests pass; settings.json validates |
| **P5** | `eval/` harness templates + `.github/workflows/factory-ci.yml` | run a 2-case eval against a toy generated project |
| **P6** | Layer 1 `templates/layer1/` (Docker, builder UI, deploy, eval) — optional layer | generate a Layer-1 factory, smoke it |
| **P7** | Self-test end-to-end: run `/software-factory` on a throwaway greenfield dir AND on a copy of an existing repo; confirm the generated factory builds one real feature with passing eval | screenshots/logs of a green build |
| **P8** | Open-source polish: `examples/`, `crm-builder-walkthrough.md`, root README entry, `open-source-checklist.md`, GitHub repo + release | external clone → install → run works |

KISS: P0–P3 + P7 is the **minimum viable factory generator** (Layer 0,
greenfield+retrofit, deterministic, tested, self-tested). P4–P6, P8 are
incremental. Ship P0–P3+P7 first, then layer on.

---

## 6. Decisions (resolved with the user)

1. **Skill name → `software-factory`.** Command `/software-factory`; GitHub repo
   `software-factory`.
2. **Generated-factory branding → neutral** (`.claude/…`, "the factory"). No
   named identity stamped in.
3. **Eval runner language → Python.** Stack-neutral; shells out to the project's
   own build/test/lint commands. One toolchain across the whole skill.
4. **Ship order → MVP first.** First release = **P0–P3 + P7** (Layer 0 dev
   harness, greenfield + retrofit, deterministic scaffolder, tested,
   self-tested end-to-end). P4 (hooks), P5 (eval), P6 (Layer 1), P8 (OSS polish)
   follow incrementally.

**Status: P0–P17 built, then hardened to v0.1.0 (review phases A–E).** **86 unit
tests + a no-API-key end-to-end demo, all green and CI-enforced**; generated
Python byte-compiles, generated shell parses, generated `settings.json` valid.

Post-build senior-review remediation (A–E):
- **A — Security (P0):** Layer 1 builder token-auth + Host check + single-flight +
  loopback-only mapping; `setup-worktree` never force-deletes unmerged work;
  `protect-secrets` stops whole-tree-exempting `tests/`/`fixtures/`.
- **B — Guardrail correctness:** `block-dangerous-git` covers `rm -rf .`, history
  destruction, etc. (labeled best-effort); validate-on-stop tree-gated + opt-out;
  worktree hook reconciled with the promotion doc (`FACTORY_SESSION`).
- **C — Scaffolder robustness:** stdlib schema validation, real per-stack CI
  toolchain emission, target `.gitignore`, eval sandbox seeding + cost warn,
  detect cleanup + `resume` mode.
- **D — Proof:** `examples/demo/run_demo.sh` (whole pipeline, no API key) +
  `tests/test_demo.py` + `LIMITATIONS.md`.
- **E — OSS release:** CONTRIBUTING/SECURITY/CODE_OF_CONDUCT/CHANGELOG, issue+PR
  templates, skill self-CI, `VERSION`, supply-chain notes; backups preserve the
  original across re-runs.

Remaining for a public release: push the branch + open the PR (or carve into a
standalone repo) + tag `v0.1.0` — see `references/open-source-checklist.md`.

Base (P0–P8): Layer 0 dev harness (greenfield + retrofit, deterministic
scaffolder), guardrail hooks, probabilistic eval + CI, optional Layer 1 product
factory, references + committed example.

Extension phases — closing the "non-coder builds a complete app by chatting" gap:
- **P9 — Starter registry + run/preview.** `scripts/starters.json` +
  `fetch_starter.py` (specialize a working base instead of building from zero) +
  `preview.py` (live app). The biggest lever: a running app from a chat.
- **P10 — Non-coder UX + cost.** `rules/non-coder-ux.md` (plain-language,
  satisfaction loop, cleanup, undo, recovery, human-gates) + `rules/cost-controls.md`
  (model tiering, per-request `budget_usd`) + `/factory-undo` + builder-orchestrator
  state machine.
- **P11 — Backend + deploy.** `data-modes.md` (demo/full) + `writing-migrations`
  skill + `db/` + `deploy/deploy.sh` (gated, verify-first dispatcher for
  vercel/netlify/fly/cloudflare/render) + `deploy-recipes.md`.
- **P12 — Richer eval.** diff capture; `mustModify`/`mustNotModify`/
  `expectedDiffStats` (warn) + `maxDurationMs`/`maxCostUsd` (hard) — crm-builder's
  warn-vs-fail split.
- **P13 — Visual verification.** `skills/visual-testing` + `eval/visual_check.py`
  (load URL, assert text/selectors, screenshot; skips cleanly without Playwright)
  + `/factory-screenshot`; test-validator requires it for UI changes.
- **P14 — Backend + per-ORM migrations.** `db/migrate.sh` (prisma/drizzle/alembic/
  supabase/django/typeorm) + `db/provision.sh` + `references/backend-provisioning.md`
  + `delivery.migration_tool`.
- **P15 — Multi-session memory.** `skills/handoff` + `/factory-handoff` +
  `/factory-resume` + `MEMORY.md` + `docs/sessions/`; documentator maintains them.
- **P16 — Distribution.** `install.sh` one-line installer (idempotent, no-clobber).
- **P17 — Worktree/promotion machinery.** portable `setup-worktree.sh` /
  `cleanup-worktree.sh` hooks (wired in settings) + `rules/worktree-promotion.md`
  (session-branch + `session-base` anchor + promote-under-`flock`).

Intentionally NOT automated (correct safety boundary): credentialed backend
*provisioning* and prod deploys run as human-confirmed steps (the factory prints/
runs the exact commands, a human approves) — never silent infra creation or
long-lived secret handling. A hosted SaaS front-end for fully non-technical users
is out of scope for a Claude Code skill.

### Self-test evidence (P7)

- `scaffold.py` greenfield → 31 files, **no leftover `{{ }}` placeholders**;
  computed sections (wave math 3N+1, agent table, validation block, sorted
  glossary, entities) render correctly.
- `detect.py` → correct `mode`/`stack`/`commands` on a real node repo
  (`crm-builder/chat-service`) and a TS/React fixture.
- `scaffold.py` retrofit → user `CLAUDE.md` preserved + managed block appended
  + `.bak` created; pre-existing `.claude/rules/coding-style.md` **skipped**;
  `src/` untouched.
- `python3 -m unittest discover -s tests` → **15 passed**.

---

## 7. Risks / notes

- **Retrofit must never clobber.** Back up, append managed blocks, diff-report.
  This is the highest-risk path; golden-file tests gate it.
- **Stack-agnostic eval** depends on the user giving correct build/test commands
  in D4 — validate they actually run before writing the baseline.
- **Token budget.** The skill itself must stay lean: SKILL.md points to
  `references/*` loaded on demand; scaffolding is a script (cheap), not LLM
  file-by-file writing.
- **Self-test is mandatory** (P7) — a factory generator that has never generated
  a working factory is vapor. Evidence before "done".
