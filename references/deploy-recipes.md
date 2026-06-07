# Deploy recipes

Concrete one-command deploys the factory can run (gated, verify-first). The
generated `deploy/deploy.sh` dispatches on `delivery.deploy_target`; this is the
reference for filling in / extending it. A non-coder never types these — the
factory runs them after explicit confirmation.

## Frontend / full-stack hosts

| Target | Command | Notes |
|---|---|---|
| Vercel | `npx vercel deploy --prod` | `vercel link` once; env vars in the dashboard or `vercel env`. |
| Netlify | `npx netlify deploy --prod` | `netlify link` once. |
| Cloudflare (Workers/Pages) | `npx wrangler deploy` | `wrangler.toml` defines the project; `wrangler secret put` for secrets. |
| Fly.io | `flyctl deploy` | `fly launch` once to create `fly.toml`. |
| Render | push to the connected branch | auto-deploys; create the service once in the dashboard. |

## Backend / database provisioning

A "complete app" needs persistence + auth + storage. Provision once, then
migrations flow (`.claude/skills/writing-migrations`, `.claude/rules/data-modes.md`).

| Backend | Provision | Migrate |
|---|---|---|
| Supabase | `supabase link --project-ref <ref>` | `supabase db push` (+ `functions deploy`, `secrets set`) |
| Neon / managed Postgres | create the DB, set `DATABASE_URL` | your ORM: `prisma migrate deploy` / `alembic upgrade head` / `drizzle-kit migrate` |
| PlanetScale | `pscale` connect | ORM migrate / `pscale deploy-request` |

## The crm-builder full sequence (reference)

`vite build` → `supabase link` → `db push` → `functions deploy` → `secrets set`
→ `wrangler deploy` (frontend). Built in an isolated worktree so the live dev
server is never touched; secrets redacted from logs; gated server-side on full
config. Copy this staging when hardening a real deploy.

## Rules

- **Verify before deploy** — build + tests green first; never ship red.
- **Confirm irreversible steps** — prod deploys, destructive migrations, secret
  changes: explicit human OK each time (`deploy.sh` is dry until `--yes`).
- **Secrets** live in the host's secret store, never in the repo or image.
