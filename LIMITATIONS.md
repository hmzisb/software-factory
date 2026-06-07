# Limitations & what's actually guaranteed

Honesty matters more than hype for a tool that writes your code. Here's the line
between what this skill **guarantees** and what it **enables but can't promise**.

## Guaranteed (deterministic, CI-tested every commit)

- **The scaffold pipeline.** `detect → interview → scaffold` produces the same
  factory tree for the same config (byte-identical), refuses an invalid or
  unvalidated config, and never clobbers your files in retrofit mode.
- **The generated artifacts run.** The guardrail hooks block force-push / secret
  writes / `rm -rf .`; deploy and migrations are dry-by-default and gated; the
  probabilistic eval harness scores cases and detects regressions. See
  `examples/demo/run_demo.sh` — one command, no API key, proves all of this
  end-to-end. It runs as a test (`tests/test_demo.py`) on every push.
- **The safety boundary holds.** Credentialed provisioning, production deploys,
  and anything touching auth/billing/secrets are human-gated by construction —
  the factory prints the exact commands but does not run them autonomously.

## Enabled, but not promised (model- and prompt-dependent)

- **Autonomous build quality.** Whether `/factory-build "<feature>"` produces a
  correct, complete feature depends on the model, the prompt, the codebase, and
  the task. This skill gives the agent team the *harness* to do it well (TDD,
  review, verify, worktrees, a domain `CONTEXT.md`); it does not make a weak model
  strong. **Measure it** with the eval harness — that's exactly what `eval/` is
  for. Set a `success_threshold` and let regressions fail CI.
- **Cost.** A from-scratch build can run tens of dollars. The cost-controls rule
  + `budget_usd` cap help, but spend is ultimately yours to watch.
- **Starter templates.** The registry points at third-party repos pinned to a
  branch; verify the ref and remember `npm install`/`pip install` runs upstream
  code on your machine.

## Not in scope

- A hosted, zero-setup SaaS for fully non-technical users. The Layer 1 builder is
  a *local, single-user, containerized* convenience, not a multi-tenant product.
  Putting it on the internet needs real auth + isolation you must add yourself
  (see `templates/layer1/README.layer1.md`).
- Windows without WSL. The hooks and scripts assume `python3` + `bash` + `git`
  (macOS / Linux / WSL).

## How to verify the claims yourself

```bash
python3 -m unittest discover -s tests   # the full unit + end-to-end suite
bash examples/demo/run_demo.sh          # the pipeline, end to end, no API key
```
