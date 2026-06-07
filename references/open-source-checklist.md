# Open-source checklist

Steps to publish `software-factory` as a standalone GitHub repo and keep it
shareable.

## Repo layout (standalone)

The skill is already self-contained under `skills/software-factory/`. To ship it
as its own repo, that directory becomes the repo root:

```
software-factory/
  SKILL.md  README.md  LICENSE  PLAN.md
  references/  templates/  scripts/  tests/  examples/
```

## Before first release

- [x] `README.md` — what it is, requirements, install, a no-API-key demo, the
      anatomy table, links to `PLAN.md` / `CHANGELOG.md` / `LIMITATIONS.md`.
- [x] `LICENSE` — MIT (present).
- [x] `python3 -m unittest discover -s tests` — all green (no third-party deps).
- [x] `bash examples/demo/run_demo.sh` — end-to-end pipeline green (no API key),
      enforced by `tests/test_demo.py`.
- [x] `examples/greenfield-saas/` — a committed generated factory.
- [x] No secrets, no machine-specific paths in any committed file.
- [x] `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`,
      issue + PR templates, `LIMITATIONS.md`, `VERSION`.
- [ ] When carving into a standalone repo: move `skills/software-factory/.github/*`
      to the repo root `.github/` (GitHub only auto-discovers templates at the
      root), and adjust the CI workflow's `working-directory`/path filters.

## CI for the skill itself

Present at the monorepo root: `.github/workflows/software-factory-tests.yml`
(runs the unit + end-to-end suite and the demo on every push/PR that touches the
skill). When standalone, drop the `working-directory:` + path filters:

```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: python3 -m unittest discover -s tests -v
      - run: bash examples/demo/run_demo.sh
```

## Install instructions to document

```bash
git clone https://github.com/hamzaahmed/software-factory.git
ln -s "$PWD/software-factory" ~/.claude/skills/software-factory
# then, in any project:  /software-factory
```

## Versioning / sharing

- Tag releases (`v0.1.0`) so users can pin.
- Keep `PLAN.md`'s status section current (which phases are done).
- Credit the inspirations in the README (marmelab article + crm-builder,
  superpowers, mattpocock/skills) — all MIT/compatible.

## Maintenance hooks

- When you add a template file, add or update a golden-file test in
  `tests/test_scaffold.py`.
- When you add a `{{ computed.X }}` fragment, document it in
  `references/scaffold-algorithm.md` and cover it in a test.
