# Definition of done — Tasker

A change is **done** only when every box is checked. The orchestrator gates on
this; the verify command checks the mechanical parts.

## Every change

- [ ] The failing test was written first, and now passes (TDD).
- [ ] All tests pass: `pnpm test`
- [ ] Typecheck clean (if applicable): `pnpm run typecheck`
- [ ] Lint clean (if applicable): `pnpm run lint`
- [ ] Build succeeds (if applicable): `pnpm run build`
- [ ] Reviewed by the reviewer agent (semantic + security).
- [ ] No secrets, credentials, or tokens added to the repo.
- [ ] Scope respected — only the ticket's files changed.

## When the change is structural

- [ ] An ADR is written in `docs/adr/` explaining the decision and alternatives.

## When the change touches the domain

- [ ] `CONTEXT.md` updated (new/changed entities, glossary terms, workflows).

## When an eval case exists for the feature

- [ ] The case passes at the target success rate across N runs (`python3 eval/run.py`).

## Security pass (quick)

- [ ] Inputs validated at boundaries.
- [ ] Auth/scope enforced where relevant.
- [ ] No default-open flags, no unescaped interpolation, no orphan-row risk.
