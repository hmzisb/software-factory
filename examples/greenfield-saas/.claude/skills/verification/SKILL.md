---
name: verification
description: Evidence before completion. Use before claiming any work is done, fixed, or passing, and before committing or shipping. Run the verification command and confirm the output before making any success claim.
---

# Verification before completion

Vendored, self-contained. (If `superpowers` is installed, prefer its
`verification-before-completion` skill.)

## The rule

**Never claim "done / fixed / passing" without showing the command output that
proves it.** Evidence before assertion, always.

## Before saying it works

1. Run the actual verification — the tests, the typecheck, the build, the real
   feature path (`.claude/rules/validation-commands.md`).
2. Read the output. Did it actually pass, or did it error/skip/time out?
3. Only then state the result — and include the proof.

## Red flags (stop and verify)

| Thought | Reality |
|---|---|
| "This should work now." | "Should" isn't "does." Run it. |
| "It's a trivial change." | Trivial changes break builds. Run it. |
| "Tests probably pass." | Probably isn't proof. Run them. |
| "I'll just say it's fixed." | Not without the output. |

## On failure

Report the failure first, with the output. Don't bury it, don't round up a
partial pass to "done".
