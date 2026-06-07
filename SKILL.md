---
name: software-factory
description: Scaffold a complete "software factory" (agentic harness) for any project so Claude Code can build and maintain the whole software autonomously. Use when the user wants to bootstrap a new project, set up a repo for AI-driven development, "build a factory", create CLAUDE.md + agents + guardrails + specs + eval harness, or retrofit an agentic harness onto an existing codebase. Interviews the user, then deterministically generates the harness.
---

# software-factory

Generate a **software factory** for any project: the full set of files Claude
Code needs to then build and maintain the software autonomously — `CLAUDE.md`,
a specialized agent team, slash commands, modular rules, guardrail hooks, a
domain `CONTEXT.md`, specs/plans, a probabilistic eval harness, CI, and a
definition-of-done.

Concept (from marmelab's "Agentic Software Factories"): a factory = **harness**
(skills + tools + domain knowledge) + **template** + **orchestrator-led agent
team** + **probabilistic validation**. This skill *builds that harness for you*,
then hands the wheel to the generated factory.

Self-contained: the generated factory works with **zero external plugins**. If
`superpowers` or `mattpocock` skills are installed, the factory prefers them; it
never requires them.

## When to use

- "Set up this project for Claude Code to build" / "bootstrap a new app"
- "Build a software factory / agentic harness for X"
- "Add CLAUDE.md + agents + guardrails + eval harness to this repo"
- "I want Claude to autonomously build and maintain this — scaffold it"
- Greenfield (empty dir) OR existing repo (retrofit).

## Runtime algorithm

Follow these steps in order. Load the referenced files **on demand** (keep
primary context lean).

### 1. Detect

```bash
python3 scripts/detect.py <target-dir>   # default: cwd
```

Prints JSON: `mode` (`greenfield` | `retrofit` | `resume`), detected `stack`,
`build/test/lint/typecheck` commands, whether CI exists, and whether a
`factory.config.json` already exists. Read it before interviewing.

### 2. Interview

Read `references/interview.md`. Conduct the interview **one domain per turn**:
ask, wait for the answer, summarize what you understood, confirm, then advance.
In `retrofit` mode, pre-fill answers from detection and ask only to confirm or
correct. Persist after every domain to `factory.config.json`
(`validated: false`). Run the consistency checks before final validation. On
final "yes", set `validated: true`.

Never scaffold before `validated: true`.

### 2.5 Starter template (greenfield only)

If greenfield, offer a working base to specialize instead of building from zero
(see `references/starter-registry.md`):

```bash
python3 scripts/fetch_starter.py --list
python3 scripts/fetch_starter.py --id <id> --target <target-dir>
```

It clones the starter and strips its `.git`. Record the choice in
`config.starter`, and pre-fill `stack` + `quality.dev_cmd` from the printed JSON.
A starter switches the scaffold to **retrofit** mode (harness added on top, app
files untouched). Choosing `blank` skips this and builds from scratch.

### 3. Scaffold

```bash
python3 scripts/scaffold.py factory.config.json --target <target-dir>
```

Deterministic: same config → same tree. It stamps `templates/` into the target.
- **Greenfield**: writes the full tree; `git init` if no repo.
- **Retrofit**: merges, **never clobbers** — backs up, appends managed blocks to
  an existing `CLAUDE.md`, adds `.claude/` files only where absent, and prints a
  diff summary of added vs skipped. See `references/scaffold-algorithm.md`.

### 4. Seed (optional)

If the user opted in (interview domain D8): produce the first PRD in
`specs/0001-*.md`, then break it into vertical-slice tickets in `plans/` (and
tracker issues if a git host was configured). This gives the factory immediate
work.

### 5. Next steps

Print, in plain language:
- how to see it live: `python3 scripts/preview.py` (or `/factory-preview`)
- how to drive the factory: `/factory-build "<feature request>"`
- how to run the eval: `python3 eval/run.py`
- which optional plugins it will use if installed (superpowers, mattpocock)

## What gets generated

See `references/factory-anatomy.md` for the full map and the rationale for each
artifact. Summary: `CLAUDE.md`, `CONTEXT.md`, `definition-of-done.md`,
`.claude/agents/*`, `.claude/commands/*`, `.claude/skills/*` (vendored
discipline), `.claude/rules/*`, `.claude/hooks/*` + `settings.json`, `docs/adr/`,
`docs/learnings/`, `specs/`, `plans/`, `eval/`, `.github/workflows/`.

Layer 0 (dev harness) is always generated. Layer 1 (marmelab-style self-modifying
product factory: Docker + builder UI + deploy) is generated only on request —
see `references/layer1-product-factory.md`.

## Reference: the worked example

`marmelab/crm-builder` is the canonical real-world factory. See
`references/crm-builder-walkthrough.md` for how its harness maps onto a
generated factory.
