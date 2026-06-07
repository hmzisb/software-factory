---
name: tdd
description: Test-driven development — red/green/refactor. Use before writing any feature or bugfix code. Write the failing test first, make it pass minimally, then refactor with tests green.
---

# TDD — red / green / refactor

Vendored, self-contained. (If the `superpowers` plugin is installed, prefer its
`test-driven-development` skill.)

## The loop

1. **RED.** Write one small test that expresses the next behavior from the spec.
   Run it. Confirm it **fails for the right reason** (assertion, not import/typo).
2. **GREEN.** Write the **minimum** code to make it pass. No extra features. Run;
   confirm green.
3. **REFACTOR.** With tests green, clean up names/structure/duplication. Re-run;
   stay green.
4. Repeat for the next behavior.

## Rules

- Never write production code without a failing test that demands it.
- One behavior per cycle — small steps.
- Don't test implementation details; test observable behavior.
- A test you can't make fail is not a test — verify RED before GREEN.
- Cover edge cases and the security boundary of the change as their own cycles.

## Why

The failing test proves the test works and pins the spec. Minimal green prevents
gold-plating. Green-gated refactor keeps you safe. This is the feedback loop that
keeps the factory's output correct.
