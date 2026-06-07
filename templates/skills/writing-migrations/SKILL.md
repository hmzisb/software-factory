---
name: writing-migrations
description: Generate and apply database migrations safely from a schema change. Use when a change alters the data shape (new field/table/relation). Demo mode stays in-memory; full mode generates and applies a real migration.
---

# Writing migrations

Vendored, self-contained. A data-shape change is the riskiest kind — this keeps
it safe and reversible.

## Demo vs full (see rules/data-modes.md)

- **Demo mode** — data is mocked/in-memory. Schema changes are reflected in the
  app's types/models only; no SQL runs. Fast iteration, no persistence.
- **Full mode** — a real backend. A schema change needs a migration, generated
  and applied deliberately.

## The rule (full mode)

Developers do **not** hand-write migrations mid-feature. Instead:

1. Build the feature against the app's models/types (works in demo immediately).
2. When promoting to full, generate the migration from the **diff** between the
   last known-good schema and the new one — run `bash db/migrate.sh generate
   "<name>"` (it dispatches to your ORM: prisma / drizzle / alembic / supabase /
   django / typeorm). Diff against the stable baseline, not an arbitrary point,
   so you don't pick up unrelated work.
3. Review the generated SQL (a reviewer pass): destructive ops (drop column/
   table), non-nullable columns without a default on a populated table,
   missing indexes on new FKs, data-loss risk.
4. Apply it (`migrate deploy` / `db push` / `alembic upgrade head`), then verify.

## Safety

- Every migration must be **reversible** (a down migration or a documented
  rollback). Never run a destructive migration against real data without an
  explicit human OK.
- Keep migrations in `db/migrations/` (or your ORM's dir), committed, ordered.
- Re-read the migration sequence before applying — order and numbering matter.
- Secrets/keys never go in a migration.
