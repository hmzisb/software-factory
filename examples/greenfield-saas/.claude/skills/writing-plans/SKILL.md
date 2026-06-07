---
name: writing-plans
description: Turn a spec or request into an ordered, reviewable implementation plan of vertical-slice tickets before touching code. Use when starting a multi-step feature.
---

# Writing plans

Vendored, self-contained. (If `superpowers` is installed, prefer its
`writing-plans` skill.)

## Output

A plan is a set of **vertical-slice tickets** in `plans/`, grouped into
dependency waves. Each slice is independently shippable and testable — a tracer
bullet through the stack, not a horizontal layer.

## Process

1. Read the spec and `CONTEXT.md`. Restate the goal in one sentence.
2. List the smallest tickets that each deliver one user-visible capability.
3. Order them by dependency into waves (wave 0 = no deps).
4. For each ticket write: goal, testable acceptance criteria, file hints, and the
   **test to write first**.
5. Note open questions and risks up front — resolve before building.

## Quality bar

- Every ticket has at least one acceptance criterion you can write a test for.
- No ticket needs "and" to describe its goal — if it does, split it.
- The plan is reviewable by a human in a couple of minutes.

Do not implement while planning. Plan, get agreement, then build.
