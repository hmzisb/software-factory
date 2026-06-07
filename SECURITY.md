# Security policy

## Reporting a vulnerability

Please **do not open a public issue** for a security problem. Email the
maintainer (see the repo owner's profile) with details and, if possible, a
reproduction. You'll get an acknowledgement within a few days.

## Threat model — what this tool is and isn't

`software-factory` generates a harness that lets Claude Code modify your code
autonomously. Treat it accordingly.

- **Guardrail hooks are best-effort, not a sandbox.** `block-dangerous-git.py`
  and `protect-secrets.py` catch common footguns (force-push, `rm -rf .`,
  secret-shaped writes). They can be evaded by obfuscated commands and miss novel
  secret formats. The real boundary is: run untrusted/autonomous work in a
  worktree, require human review, and use a dedicated secret scanner
  (`gitleaks`/`trufflehog`) in CI.
- **The Layer 1 builder runs an unsandboxed agent.** It is hardened for **local,
  single-user** use only: loopback-only port, a shared token on `/chat`, a Host
  check (anti-DNS-rebinding), and single-flight. It is **not** safe to expose on a
  network without adding real auth + isolation. See
  `templates/layer1/README.layer1.md`.
- **Human-gated by design.** Credentialed provisioning, production deploys, and
  auth/billing/secret changes are never performed autonomously — the factory
  prints the commands but a human runs them.
- **Starters are third-party code.** Cloning a starter is safe; `npm install` /
  `pip install` on it runs upstream code on your machine. Pin refs and review.

## Supported versions

Pre-1.0: only the latest tag is supported. Pin a tag (`v0.x.y`) for stability.
