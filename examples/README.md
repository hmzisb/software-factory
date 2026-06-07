# Examples

Committed, real output of the scaffolder — so you can see what a generated
factory looks like without running anything.

## `greenfield-saas/`

A Layer 0 factory generated for a fictional SaaS ("Tasker", a team task tracker:
TypeScript / Next / Postgres). Produced by:

```bash
python3 scripts/scaffold.py <config> --target examples/greenfield-saas --no-git
```

Browse it to see the rendered `CLAUDE.md`, `CONTEXT.md`, the agent team under
`.claude/agents/`, the guardrail hooks, the `eval/` harness, and CI. The
`factory.config.json` at its root is the exact spec it was generated from — edit
that and re-run the scaffolder to get a different factory.

> This is generated output, not hand-written. It is regenerated when the
> templates change. Don't edit it directly — change `templates/` instead.
