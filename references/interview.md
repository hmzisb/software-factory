# The interview

How the skill interviews the user to fill `factory.config.json`. Modeled on
crm-builder's `setup-interview`, generalized to any project.

## Protocol

- **One domain per turn.** Ask the domain's questions, wait for the answer,
  **summarize what you understood**, get confirmation, then advance. Never ask
  two domains at once.
- **Persist after every domain.** Read → update the domain section → set
  `interview_progress.dN = "done"` → keep `validated: false` → write
  `factory.config.json`.
- **Prefer multiple choice** where the answer space is small (use the harness's
  question UI when available); free text otherwise.
- In **retrofit** mode, pre-fill from `detect.py` output and ask only:
  *"Detected `<X>` — keep, or change?"* per field.
- Bounce side-requests: if the user asks for something unrelated mid-interview,
  relay the current question unchanged and don't advance.

## Startup detection

Run `detect.py`, then read `factory.config.json` if present:

| State | Action |
|---|---|
| no config, empty dir | FRESH interview, `mode: greenfield`, from D1. |
| no config, existing repo | FRESH interview, `mode: retrofit`, pre-filled from detection. |
| config, `validated: false` | RESUME from the first `pending` domain. |
| config, `validated: true` | Summarize it; ask: update specific domains, or restart. |

## Domains

### D1 — Product → `project`
- What is it, in one sentence? (`one_liner`)
- What problem does it solve? (`problem`)
- Who uses it? (`users`)
- How will you know it works? (`success_metric`)
- Project name? (`name`)

### D2 — Domain → `domain`
- Is this specialized to a **job** (e.g. recruitment) or a **domain/industry**
  (e.g. bike rental), or general? (`specialization.kind` + `.label`)
  > The narrower the scope, the lower the failure rate (the article's principle).
- What are the main things the system manages? (entities + relationships)
- Any domain terms that must be used precisely? (glossary)
- What are the 2–4 key workflows? (workflows)

### D3 — Stack + starter → `stack`, `starter`, `quality.dev_cmd`
- **Greenfield:** offer a starter template by app-type (`fetch_starter.py --list`,
  see `references/starter-registry.md`). Picking one clones a working base and
  pre-fills `stack` + `dev_cmd`; the build becomes a specialization, not a
  from-zero build (lower failure rate). `blank` = build from scratch.
- Language? Framework? Database? Package manager? Runtime?
  > Retrofit (or a chosen starter): all detected/known — confirm or correct.

### D4 — Quality → `quality`  **(critical — drives eval + the gate hook)**
- Test command? (`test_cmd`) — required.
- Build command? Lint command? Typecheck command?
- Test framework? Coverage target (or none)?
- **Validate the commands actually run** before writing the baseline (D4 is the
  one place a wrong answer silently breaks the eval).

### D5 — NFRs → `nfrs`
- Security boundaries (auth, scopes, secrets, input validation, RLS)?
- Performance budget? Accessibility needs? Internationalization?

### D6 — Delivery → `delivery`
- Git host (GitHub / GitLab / local / none)?
- Want CI generated?
- Deploy target? (vercel / netlify / fly.io / cloudflare / render — drives
  `deploy/deploy.sh`.) Environments (dev/staging/prod)?
- Data mode to start in? `demo` (mocked/in-memory, instant — recommended for
  building) vs `full` (real backend). Managed backend for full mode?
  (`backend`: supabase / neon / planetscale / …) Migration tool?
  (`migration_tool`: prisma / drizzle / alembic / supabase / django / typeorm —
  drives `db/migrate.sh`). See `data-modes.md` + `backend-provisioning.md`.

### D7 — Factory shape → `factory`
- **Layer 0 only**, or also **Layer 1** (a self-modifying product non-coders
  drive)? (`layers`)
- Max tickets per wave, 1–5? (`agent_team_size`, default 3)
- Autonomy: supervised / semi-autonomous / autonomous? (`autonomy`)
- Per-request cost cap in USD? (`budget_usd`, blank = none) — the factory pauses
  and asks before exceeding it. Recommended for non-coder / Layer 1 use.

### D8 — Seed → `seed`
- Generate the first PRD + vertical-slice tickets now? (`generate_prd`)
- If yes: one-line description of the first feature. (`first_feature`)

## Consistency checks (before final validation)

- `quality.test_cmd` is non-empty.
- Every entity name in `domain.workflows`/relationships exists in `entities`.
- No duplicate entity names.
- If `factory.layers` includes 1, a `stack.framework` and `delivery.deploy_target`
  are set (Layer 1 needs something to deploy).
- If `delivery.ci` is true, `git_host` is not `none`.
- No secret values captured in the config.

On a failed check: ask one targeted question to fix it, then re-check.

## Final validation

When all applicable domains are `done`:
1. Produce a compact plain-language summary of the whole config.
2. Ask: *"All good? I'll lock the spec and scaffold the factory. (yes / no)"*
3. On yes: set `validated: true`, write the file, then run `scaffold.py`.
4. On no: ask which domain to revisit; re-enter it.

D8 may be `skipped`. D5/D6 may be `skipped` for a throwaway/local project.
