# Starter registry — building on a working base

The fastest way to a *complete, running* app for a non-coder is to start from a
working template and specialize it — not to build from zero. This is marmelab's
core move (Atomic CRM as the base) and the single biggest lever for reliability:
the factory only has to *change* a working app, not invent one.

## How it works

1. The interview (D3) offers the starters in `scripts/starters.json` by app-type.
2. `scripts/fetch_starter.py --id <id> --target <dir>` clones the chosen starter
   into the target and strips its `.git` (so it becomes the user's own repo).
3. `scaffold.py` runs in **retrofit** mode on top of the starter — adding the
   harness (`.claude/`, CLAUDE.md managed block, eval, CI) without clobbering the
   app's files.
4. `scripts/preview.py` runs the starter's dev command so the user sees it live.
5. From there, `/factory-build "<request>"` specializes the app.

```
fetch_starter (clone base)  ->  scaffold.py --retrofit (add harness)
   ->  git init  ->  preview.py (live app)  ->  /factory-build (specialize)
```

## The registry (`scripts/starters.json`)

Each entry: `id`, `title`, `repo`, `ref`, `dev_cmd`, `stack`, `description`.
`repo: null` (id `blank`) means "no starter — build from scratch".

```bash
python3 scripts/fetch_starter.py --list
python3 scripts/fetch_starter.py --id crm --target ./my-app
```

> The shipped URLs are curated but upstreams move — **verify the repo/ref** before
> relying on one. `fetch_starter.py` fails loudly if a clone fails.

## Adding a starter

Append an entry to `scripts/starters.json`. Prefer templates that:
- run with one dev command,
- include auth + a data layer (so "complete app" is real),
- are MIT/permissively licensed,
- map cleanly to an app-type a non-coder would ask for (CRM, booking, inventory,
  marketplace, dashboard, blog, internal tool).

A good starter + a narrow domain = the article's "failure rate ≈ 0".
