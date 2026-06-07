---
description: Ship the integrated work — confirm the gate is green, then merge/PR/deploy per the project's delivery config.
---

Ship the current integrated work.

1. Run `/factory-verify` first. If anything fails, stop — never ship red.
2. Confirm the work meets `definition-of-done.md`.
3. Deliver per the project's delivery config (`CLAUDE.md` / `.claude/rules`):
   - git host **github**: open a PR (or merge to the default
     branch if that's the configured flow).
   - deploy target **vercel**: run `bash deploy/deploy.sh`
     (dry by default). After explicit user confirmation, run
     `bash deploy/deploy.sh --yes` to actually deploy, then smoke-check the live
     URL. See `.claude` / `references/deploy-recipes.md` for the per-target steps.
4. Report the PR/commit/deploy URLs and the smoke result.

Gate irreversible steps (force-push, prod deploy, deletes) on explicit human
confirmation — authorization once is not authorization always.
