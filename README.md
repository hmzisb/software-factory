# software-factory

**Turn any project into a disciplined software factory — so Claude Code can plan, build, review, test, and ship real software dependably.**

`software-factory` is a [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill. Install it once, run `/software-factory` in any project, and it scaffolds a complete **agentic harness** — an operating manual, an agent team, slash commands, rules, guardrails, CI, and a probabilistic eval — so Claude Code can then autonomously plan, build, review, test, and ship your software, gated by safety hooks and measurable validation.

The promise is simple: **AI coding shouldn't be a coin flip.** Whether you're a non-coder with an idea or a senior engineer who wants a reliable pipeline, this gives the model a factory floor with rails instead of a blank page.

> **Proof before promise.** This README leads with what's verifiable: **86 standard-library tests + a no-API-key end-to-end demo, both enforced in CI**; a deterministic scaffolder (same config → byte-identical tree); and a [`LIMITATIONS.md`](LIMITATIONS.md) that draws an explicit line between what's *guaranteed* and what's *model-dependent*.

---

## Why I built this

I read marmelab's article [**"Agentic Software Factories: The Future of Programming?"**](https://marmelab.com/blog/2026/05/22/software-factories-the-future-of-programming.html) and it reframed the whole problem for me.

Its thesis: a software factory is

> **harness** (skills + tools + domain knowledge) **+ template + orchestrator-led agent team + probabilistic validation**

and specializing that factory to one job and one domain drives the failure rate toward zero. marmelab proved it the hard way — they hand-built a bespoke factory for **one** application, a real reference CRM ([marmelab/crm-builder](https://github.com/marmelab/crm-builder)). It works. But it's *their* factory, for *their* app, built by experts.

That's the gap this skill closes. The article describes **one bespoke factory for one CRM**. **software-factory generalizes the idea into a generator** — point it at any project and, after a short interview, it builds that specialized harness for *you*: your stack, your domain, your definition of done. The goal is to let anyone — not just a team that can hand-roll their own factory — get a reliable agentic build pipeline and ship real software with AI, regardless of their coding skill.

---

## What it does

You run `/software-factory` and it walks a short, disciplined flow:

| Step | What happens |
|---|---|
| **1. Detect** | Greenfield (empty dir) vs. retrofit (existing repo); sniffs your stack and build / test / lint commands. |
| **2. Interview** | Asks you one domain at a time: product, domain, stack, quality, NFRs, delivery, factory shape, seed. |
| **3. Scaffold** | Deterministically generates the harness from your answers — *same config produces a byte-identical tree*. |
| **4. Seed** *(optional)* | Writes the first PRD, then breaks it into vertical-slice tickets so the factory has work the moment it exists. |

Then **you drive it** with the generated commands:

```text
/factory-build "<feature>"   →  plan, implement, review, test the slice
/factory-verify              →  run the definition-of-done gates
/factory-ship                →  gated, dry-by-default deploy
/factory-preview             →  live preview of the running app
```

It **never clobbers**: in retrofit mode it backs up existing files and appends managed blocks, so it's safe to point at a repo you care about.

---

## What it generates — the factory

A complete, self-contained harness — **no plugins required**:

- **`CLAUDE.md`** (operating manual), **`CONTEXT.md`** (your domain language), and a **definition-of-done**.
- A **7-agent team**: orchestrator, planner, developer, reviewer, test-validator, merger, documentator.
- **9 slash commands** — `factory-build` / `plan` / `verify` / `ship` / `preview` / `undo` / `screenshot` / `handoff` / `resume` — and **12 modular rules**.
- **8 vendored discipline skills** — `tdd`, `verification`, `writing-plans`, `brainstorming`, `worktrees`, `writing-migrations`, `visual-testing`, `handoff`. Self-contained; **zero plugins required**.
- **Guardrail hooks**: block dangerous git/`rm`, protect secrets, validate-on-stop, worktree setup/cleanup.
- A **probabilistic eval harness** — run each case *N* times, score against a baseline, detect regressions — plus **out-of-the-box CI** for your stack.
- **Gated, dry-by-default deploy** and **per-ORM migrations** (prisma / drizzle / alembic / supabase / django / typeorm).
- *Optional* **Layer 1 "product factory"**: a containerized builder **chat** so a non-coder can drive the whole factory in plain language.

### Modes

| Mode | Behavior |
|---|---|
| **Greenfield** | Empty directory → full factory + optional seeded backlog. |
| **Retrofit** | Existing repo → **never clobbers**: backs up first, then appends managed blocks. |

The layout is **layered**: Layer 0 (the dev harness above) is always installed; Layer 1 (the product-factory chat) only on request.

---

## Requirements

| | |
|---|---|
| **Runtime** | `python3` (3.8+), `git`, `bash` |
| **Platforms** | macOS, Linux, Windows via WSL |
| **Python deps** | **None** — standard library only |

---

## Install

```bash
git clone https://github.com/hamzaahmed/software-factory.git && bash software-factory/install.sh
```

Then, in any project:

```text
/software-factory
```

---

## See it work (no API key)

```bash
bash examples/demo/run_demo.sh
```

This scaffolds a real factory and exercises the whole pipeline end to end — detect → scaffold → the generated hooks, deploy, and migrations **actually run** (gated dry-runs, a guardrail hook blocking a force-push) → closes the loop with the eval harness. No model is called. It's the same script CI runs.

---

## Proof — what's actually guaranteed

This project tries hard not to be AI hype. It draws an honest line between *the pipeline* (deterministic, ours to guarantee) and *autonomous build quality* (model-dependent, measured by the eval you configure).

| Claim | Evidence |
|---|---|
| The pipeline works | **86 standard-library tests** |
| It works end-to-end | A **no-API-key demo** ([`examples/demo/run_demo.sh`](examples/demo/run_demo.sh)) |
| It stays working | **Both the tests and the demo are enforced in CI** |
| Output is reproducible | Scaffolding is **deterministic** — same config, byte-identical tree |
| We're honest about limits | [`LIMITATIONS.md`](LIMITATIONS.md) draws the guaranteed-vs-model-dependent line; [`SECURITY.md`](SECURITY.md) documents the threat model |

```bash
python3 -m unittest discover -s tests -v   # 86 tests, no third-party deps
bash examples/demo/run_demo.sh             # the pipeline, end to end
```

What's tested is the factory: scaffolding, hooks, migrations, deploy gating, and the eval runner. What's *not* promised is that the model will write perfect features unattended — that's exactly what the probabilistic eval is for: you measure it, score it against a baseline, and catch regressions.

**That's the bargain: the harness is engineering you can verify; the autonomy is a capability you measure.**

---

## Built on / credits

This skill stands on three pieces of excellent work. Go read all of them.

- **marmelab — "Agentic Software Factories" + [crm-builder](https://github.com/marmelab/crm-builder)** — the concept and a worked reference implementation that proved a specialized factory drives failure toward zero. This skill generalizes that idea. [Read the article.](https://marmelab.com/blog/2026/05/22/software-factories-the-future-of-programming.html)
- **[superpowers](https://github.com/obra/superpowers) by obra** — engineering discipline packaged as skills (TDD, verification, worktrees, brainstorming). This skill **vendors** that discipline so a generated factory needs no plugins; if `superpowers` is installed, it prefers it.
- **[mattpocock/skills](https://github.com/mattpocock/skills) by Matt Pocock** — context engineering done right: lean `CLAUDE.md` / `CONTEXT.md`, to-prd → to-issues, triage labels, handoff, and a sub-100k context budget.

---

## Author & license

Built by **Hamza Ahmed** — [github.com/hamzaahmed](https://github.com/hamzaahmed).

Released under the **MIT License**. Use it, fork it, ship with it. If it helps you ship something real, a star or a mention is the kind of recognition that keeps open source going — and I'd genuinely love to hear about it.
