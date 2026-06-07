---
name: handoff
description: Compact a working session into a handoff document so the next session (or agent) continues cleanly. Use when ending a session, hitting a usage limit, or switching context.
---

# Handoff

Vendored, self-contained. (If `mattpocock`/`superpowers` skills are installed,
prefer theirs.) The filesystem is the memory — not the chat history.

## When

End of a session, before a usage limit cuts you off, or when handing work to
another agent/person.

## Produce `docs/sessions/<YYYY-MM-DD-slug>.md`

```markdown
# Session <date> — <one-line topic>

## Done
- <what landed, with the user-visible outcome>

## Current state
- branch / what's merged / what's running
- tests: <pass/fail + command>

## Next action (single, concrete)
- <the very next step someone should take>

## Open questions / risks
- <decisions not yet made, things to watch>

## Key files
- <path> — <why it matters>
```

## Then

- Append a one-line entry to `MEMORY.md`'s session index (date + topic + link).
- Keep it short and factual — a handoff is a pointer, not a transcript.

## Resume (next session)

Read the latest `docs/sessions/*.md` + `MEMORY.md` + `CONTEXT.md` first, then do
the "Next action". Trust disk state over any assumption about what's "in
progress".
