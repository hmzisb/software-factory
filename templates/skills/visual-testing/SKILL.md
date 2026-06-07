---
name: visual-testing
description: Verify user-visible behavior with browser e2e + screenshots. Use when a change affects the UI, or when proving to a non-technical user that something works. For non-coders, the screenshot is the proof — not a green unit test.
---

# Visual testing

Vendored, self-contained. A non-coder can't read a passing unit test — they need
to *see* the app do the thing. This skill makes "it works" visual.

## When

- Any change to a screen, form, list, button, or flow.
- Before telling a non-technical user a feature is done.
- As an eval `check` (see `eval/visual_check.py`).

## Write the e2e first (with TDD)

1. From the acceptance criteria, write a browser test for the **user-visible**
   outcome: navigate, act (click/type), assert what the user should see.
2. Run it red, implement, run it green (same red→green→refactor loop as `tdd`).
3. Keep it deterministic: stub network/time; use stable selectors (roles/labels,
   not brittle CSS).

## Screenshot as proof

After a change, capture the relevant screen:

```bash
python3 eval/visual_check.py http://localhost:3000/path \
  --has-text "Priority" --screenshot proof.png
```

Show the screenshot (or describe what's visible) to the user in plain language:
"Here's the new priority badge on your tasks." Never say "tests pass" to a
non-coder — show them.

## In eval

Add a `checks` entry that runs `visual_check.py` against a known route with
`--has-text` / `--selector` assertions, so a feature counts as "done" only when
the UI actually renders the expected result across runs.

## Rules

- Test behavior the user cares about, not pixel-exact layout.
- If Playwright isn't installed, `visual_check.py` skips (exit 0 + a note) so it
  never blocks a non-visual environment — install it where you want the gate.
