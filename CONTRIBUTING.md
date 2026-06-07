# Contributing to software-factory

Thanks for helping. The project is small, stdlib-only, and test-first — keep it
that way.

## Ground rules

- **No third-party Python deps.** Everything (scaffolder, hooks, eval, tests)
  runs on the standard library. A PR that adds a dependency needs a very good
  reason.
- **Test-first.** Add or update a test before/with any behavior change. The whole
  suite must stay green:
  ```bash
  python3 -m unittest discover -s tests -v
  bash examples/demo/run_demo.sh
  ```
- **Determinism.** The scaffolder must produce a byte-identical tree for the same
  config. If you add a computed fragment, sort/normalize it and cover it with a
  test (`tests/test_scaffold.py`).

## Common changes

| You want to… | Do this |
|---|---|
| Add a file to every generated factory | Drop a `*.tmpl` (or static file) under `templates/`; the walker stamps it. Add a golden-file assertion in `tests/test_scaffold.py`. |
| Add a `{{ computed.X }}` fragment | Compute it in `build_computed()` (deterministic), document it in `references/scaffold-algorithm.md`, add a test. |
| Add a starter template | Add an entry to `scripts/starters.json` (pin `ref` to a tag/SHA). Note the supply-chain caveat in `references/starter-registry.md`. |
| Tighten a guardrail hook | Edit `templates/hooks/*`; add a positive **and** negative test in `tests/test_hooks.py`. Hooks are fail-open by design — keep them that way. |
| Add an interview question | Update `references/interview.md` + the schema `templates/factory.config.schema.json`; the validator enforces it. |

## PR checklist

- [ ] Tests added/updated; full suite + demo green.
- [ ] No third-party deps, no secrets, no machine-specific paths.
- [ ] If you touched templates, regenerated `examples/greenfield-saas`
      (`python3 scripts/scaffold.py examples/greenfield-saas/factory.config.json --target examples/greenfield-saas --no-git`).
- [ ] `CHANGELOG.md` updated under "Unreleased".

## Security

Found a vulnerability (especially in the Layer 1 builder)? See
[`SECURITY.md`](SECURITY.md) — don't open a public issue for it.
