# Backend provisioning + migrations

How a generated factory takes a non-coder from "demo" (no setup) to "full" (real,
persistent backend) — and keeps the schema in sync. See also `deploy-recipes.md`,
`.claude/rules/data-modes.md`, `.claude/skills/writing-migrations/`.

## The two scripts (generated)

- `db/provision.sh` — one-time, human-confirmed: create/link the managed backend
  (`delivery.backend`). Prints exact steps rather than running blind, because
  provisioning touches credentials + real infra.
- `db/migrate.sh` — generate + apply migrations, dispatching on
  `delivery.migration_tool`. `generate <name>` creates a migration from the schema
  diff; `apply [--yes]` applies (dry until `--yes`).

## Migration tools (`delivery.migration_tool`)

| Tool | generate | apply |
|---|---|---|
| prisma | `prisma migrate dev --name N` | `prisma migrate deploy` |
| drizzle | `drizzle-kit generate` | `drizzle-kit migrate` |
| alembic | `alembic revision --autogenerate -m N` | `alembic upgrade head` |
| supabase | `supabase db diff -f N` | `supabase db push` |
| django | `manage.py makemigrations` | `manage.py migrate` |
| typeorm | `typeorm migration:generate -n N` | `typeorm migration:run` |

## Backends (`delivery.backend`)

| Backend | Provision |
|---|---|
| supabase | `supabase init` → `supabase link --project-ref <ref>` |
| neon / postgres / rds | create DB → set `DATABASE_URL` |
| planetscale | `pscale database create <name>` → set `DATABASE_URL` |

## Flow (demo → full)

```
build in demo (no backend)  ->  user happy
  ->  db/provision.sh            (one-time, confirmed)
  ->  db/migrate.sh generate N   (from the schema diff)
  ->  review SQL                 (reviewer / human)
  ->  db/migrate.sh apply --yes  (confirmed)
  ->  deploy/deploy.sh --yes
```

## Why provisioning isn't fully automated

Creating accounts, projects, and credentials is interactive and security-
sensitive. The factory generates the *exact commands* and runs the *safe,
repeatable* parts (migrations, gated); a human confirms the credentialed parts.
That's the right safety boundary — never let an agent silently create billable
infra or hold long-lived secrets.
