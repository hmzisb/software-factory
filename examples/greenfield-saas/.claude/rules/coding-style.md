# Coding style

Defaults; the project's linter/formatter is the source of truth for mechanics.

## Principles (KISS)

- Minimal version first. Three similar lines beat a premature abstraction.
- No speculative generality — no config-driven indirection, feature flags, or
  hooks for hypothetical futures.
- Don't add error handling/validation for cases that can't happen. Validate at
  boundaries only (user input, external APIs).
- Match the surrounding code's conventions. Don't reformat unrelated lines.

## Naming

- Use the exact domain terms from `CONTEXT.md`. No synonyms, no drift.
- Names say intent, not type. Functions are verbs; values are nouns.

## Functions

- One responsibility. If you need "and" to describe it, split it.
- Prefer pure functions; isolate side effects.

## Comments

- Explain *why*, not *what*. Delete commented-out code.

## Language

Code, comments, commits → English.
