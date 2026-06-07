# Demo — the pipeline end to end (no API key)

```bash
bash run_demo.sh
```

This scaffolds a real factory into a temp dir and proves, deterministically, that
the generated machinery works:

| Step | What it shows |
|---|---|
| `detect` | sniffs mode + stack |
| `scaffold` | writes a complete factory from a validated config (refuses invalid) |
| core artifacts | CLAUDE.md, settings, agents, eval, deploy, migrate, `.gitignore` present |
| guardrail hook | a `git push --force` is blocked |
| deploy | dry-by-default, verify-first (never ships red) |
| migration | dry-by-default |
| eval | the probabilistic harness runs a case 5× and reports 100% |

It deliberately uses a **model-free runner** (`touch hello.txt`) so it's fast,
free, and reproducible. The thing it can't show here — how well a real model
builds a real feature — is what the `eval/` harness measures on your project.
See [`../../LIMITATIONS.md`](../../LIMITATIONS.md).

For a look at the *output* of scaffolding (not run here), see
[`../greenfield-saas/`](../greenfield-saas/) — a committed factory for a sample
"Tasker" app.
