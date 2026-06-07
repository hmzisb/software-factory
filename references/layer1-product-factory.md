# Layer 1 — the product factory

Generated only when the interview's D7 sets `factory.layers` to `[0, 1]`. It
turns the project into a marmelab-style **self-modifying product**: a
non-technical user describes changes in plain language and the factory ships
them. Layer 1 sits on top of the Layer 0 dev harness — it does not replace it.

## Shape (what gets stamped)

```
Dockerfile              isolation: app + builder + claude CLI in one container
docker-compose.yml      `docker compose up --build` -> builder on :8080
builder/server.py       stdlib chat server; each message runs `claude -p` once
builder/index.html      the chat UI the builder uses
.claude/agents/builder-orchestrator.md   plain-language, user-facing orchestrator
deploy/deploy.sh        gated deploy to the configured target
README.layer1.md        how to run + harden
```

## Flow

```
user (browser chat :8080)
  -> builder/server.py        spawns: claude -p "<plain request>" --dangerously-skip-permissions
     -> builder-orchestrator  (plain language in/out; never leaks technical detail)
        -> Layer 0 factory    planner -> developer/reviewer/test-validator -> merger
           -> verify gate -> definition-of-done
  -> plain-language reply      "I added ... to your app"
```

## Why a container

The builder is non-technical, so the factory runs with
`--dangerously-skip-permissions` (no approval prompts). That is only safe inside
an isolated container with no access to anything outside the sandbox — which is
exactly what the Dockerfile provides. Never run the builder directly on a host
with real credentials or data.

## The orchestrator's contract (Layer 1 vs Layer 0)

The Layer 0 `orchestrator` talks like an engineer (tickets, agents, gates). The
Layer 1 `builder-orchestrator` wraps it and talks like a product person:
- replies only in plain language — no paths, code, git, or agent names;
- asks at most one clarifying question;
- confirms "done" only when the verify gate is green and the change meets the
  definition of done;
- routes auth/billing/secrets/irreversible work to a human (never autonomous);
- never deploys to real data without explicit confirmation.

## Hardening checklist (before real use)

- Put auth in front of the builder chat.
- Run each request on an isolated worktree/branch; review before promoting to the
  live branch (the crm-builder pattern: session branch -> promote under a lock).
- Secrets in env/secret store only; never baked into the image or committed.
- Expose only the ports you need; keep the app behind the same isolation.
- Add large-scale eval (`eval/`) gating: a feature is "done" only when it passes
  across many runs.

## Reference

`marmelab/crm-builder`'s `chat-service/` is the production-grade version of
`builder/` (WebSocket, multi-session, streaming, deploy modal, recovery). See
`crm-builder-walkthrough.md`.
