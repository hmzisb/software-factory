# Testing

Test framework: **vitest**. Run with `pnpm test`.

## Discipline

- **Test first.** Write the failing test from the spec before the code (TDD,
  `.claude/skills/tdd`). Confirm it fails for the right reason, then make it pass.
- Test **behavior**, not implementation. No assertions that can't fail.
- Cover: happy path, edge cases (empty/null/boundary), error paths, and the
  security boundaries relevant to the change (auth, scope, validation).

## Shape

- Arrange–act–assert. One logical assertion per test where practical.
- Deterministic: no real network/time/randomness — inject or stub them.
- A test name states the behavior: `does X when Y`.

## Coverage

Target: 80 (blank = no hard gate, but every change
adds tests for what it changes). New code without tests does not pass review.
