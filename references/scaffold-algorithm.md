# Scaffold algorithm

The contract `scripts/scaffold.py` implements. Goal: **determinism** (same
config → byte-identical tree) and **safety** (retrofit never clobbers).

## Inputs

- `factory.config.json` (must have `validated: true`).
- `--target <dir>` (default: cwd).
- `--dry-run` (print the plan, write nothing).

Refuse to run if `validated` is false.

## Template tree walker

Templates live under `skills/software-factory/templates/`. The walker:

1. Recursively lists every file under `templates/`.
2. **Skips** `factory.config.schema.json` (that's the skill's own schema, never
   stamped) and any path under `templates/layer1/` **unless** `1 ∈
   factory.layers`.
3. For each remaining file:
   - Compute the destination: relative path with a trailing `.tmpl` stripped.
     `CLAUDE.md.tmpl` → `<target>/CLAUDE.md`;
     `agents/developer.md.tmpl` → `<target>/.claude/agents/developer.md`
     (note: `agents/`, `commands/`, `skills/`, `rules/`, `hooks/`, `settings.json`
     map under `<target>/.claude/`; `docs/`, `specs/`, `plans/`, `eval/`,
     `.github/` map to `<target>/` directly; root files like `CLAUDE.md`,
     `CONTEXT.md`, `definition-of-done.md` map to `<target>/`). The mapping table
     lives in `scaffold.py` (`DEST_MAP`).
   - **Render** the file (see below).
   - **Write** per the mode rules (see below).

This means adding a new template file in a later phase (a hook, an eval file)
requires no scaffolder change — drop it under `templates/` and it's stamped.

## Rendering

Deterministic, dependency-free. Two constructs only:

- `{{ dotted.key }}` — substituted with the string value at that path in the
  config. Whitespace inside the braces is tolerated. A missing **optional** key →
  empty string. A missing **required** key (listed in `REQUIRED_KEYS`) → hard
  error (should never happen post-validation).
- `{{ computed.NAME }}` — substituted with a markdown fragment computed by
  `scaffold.py` from the config. Computed fragments:

  | NAME | Content |
  |---|---|
  | `entities_md` | A markdown list/table of `domain.entities` (name, description, relationships). |
  | `glossary_md` | A definition list from `domain.glossary`. |
  | `workflows_md` | A numbered list of `domain.workflows`. |
  | `agent_table_md` | The agent table sized to `factory.agent_team_size`. |
  | `validation_block` | A fenced block with the project's `quality.*` commands. |
  | `discipline_note` | "Vendored skills are in `.claude/skills/`" OR, when `uses_external_skills.*`, "Prefer the installed `superpowers`/`mattpocock` skills." |
  | `layers_note` | Whether Layer 1 is present. |
  | `wave_math` | `N=<agent_team_size>`, dispatch `3N+1` agents. |

No in-file conditionals, no loops in templates — all variability is either
whole-file (gated by `layer1/` + config) or a computed fragment. This keeps the
renderer ~30 lines and fully deterministic.

## Greenfield mode

- If `<target>` has no `.git`, run `git init` (unless `--no-git`).
- Write every rendered file. Create parent dirs as needed.
- Write `factory.config.json` into `<target>` (the factory keeps its own spec).
- Print a tree of what was written.

## Retrofit mode — never clobber

For each destination that **already exists**:

| File | Rule |
|---|---|
| `CLAUDE.md` | Append a **managed block** delimited by `<!-- BEGIN software-factory -->` / `<!-- END software-factory -->`. If the block already exists, replace only its contents. Never touch text outside the markers. Back up to `CLAUDE.md.bak` first. |
| `CONTEXT.md` | Same managed-block approach. |
| `.claude/settings.json` | Deep-merge: add the factory's `hooks`/keys; never remove the user's existing keys. Back up first. |
| `.github/workflows/factory-ci.yml` | Write only if absent (the name is factory-specific; collisions are unlikely). |
| any other existing file | **Skip** (do not overwrite). Record it in the "skipped" report. |

Files that **don't** exist are written normally. After the run, print a report:

```
ADDED   (n):  <paths>
MERGED  (n):  <paths>   (managed-block / deep-merge)
SKIPPED (n):  <paths>   (already existed, left untouched)
BACKED-UP (n): <paths>.bak
```

## Determinism guarantees

- Files are processed in **sorted path order**.
- No timestamps, no random ids, no machine paths written into output (the config
  path is recorded relative).
- Computed fragments iterate config arrays/objects in **declared order** (and
  sort object keys where order is otherwise undefined, e.g. glossary).
- `--dry-run` produces the same report the real run would, minus the writes.

Golden-file tests (`tests/test_scaffold.py`) lock a sample config → expected tree.
