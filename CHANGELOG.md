# Changelog

All notable changes to `software-factory`. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); this project uses
[SemVer](https://semver.org/) (pre-1.0: minor = features, patch = fixes).

## [Unreleased]

## [0.1.0] — first community release

The skill: scaffold a complete agentic "software factory" for any project
(greenfield or retrofit), self-contained (zero plugins required).

### Added
- Deterministic scaffolder (`detect → interview → scaffold`) with a stdlib
  JSON-Schema validator that rejects malformed configs.
- Layer 0 dev harness: `CLAUDE.md`, `CONTEXT.md`, a 7-agent team, 9 slash
  commands, 12 modular rules, 8 vendored discipline skills, a definition-of-done.
- Guardrail hooks: block dangerous git/`rm`, protect secrets, validate-on-stop
  (tree-fingerprint gated, opt-out), worktree setup/cleanup.
- Probabilistic eval harness (run N×, baseline + regression, HARD/WARN checks,
  per-case sandbox **seeding**, visual checks) + generated CI that runs out of
  the box (real toolchain setup per stack).
- Optional Layer 1 product factory (containerized builder chat).
- Backend: per-ORM migrations + gated provisioning; gated, dry-by-default deploy.
- Multi-session memory (handoff/resume), starter-template registry + live
  preview, one-line installer, target `.gitignore`.
- One-command, no-API-key end-to-end demo (`examples/demo/run_demo.sh`) enforced
  as a test.

### Security
- Layer 1 builder hardened for local single-user use: loopback-only mapping,
  `X-Builder-Token` auth, Host check (anti-DNS-rebinding), single-flight lock.
- `setup-worktree` never force-deletes a branch with unmerged commits.
- `protect-secrets` no longer whole-tree-exempts `tests/`/`fixtures/`; added
  Stripe/Google/GCP patterns. Guardrails documented as best-effort heuristics.

[Unreleased]: https://github.com/hamzaahmed/software-factory/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/hamzaahmed/software-factory/releases/tag/v0.1.0
