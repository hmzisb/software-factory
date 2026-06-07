# Validation commands

The exact commands that gate every change. The verify command, the developer's
validate step, and CI all use these. If a command is empty, that gate doesn't
apply to this project.

| Gate | Command |
|---|---|
| Tests | `pnpm test` |
| Typecheck | `pnpm run typecheck` |
| Lint | `pnpm run lint` |
| Build | `pnpm run build` |

- Run all applicable gates before handing a change to review/merge.
- Show the real output — evidence before "done".
- A failing gate blocks the merge. Fix, re-run, prove green.
