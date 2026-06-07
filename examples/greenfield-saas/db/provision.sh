#!/usr/bin/env bash
# Provision the managed backend for Tasker (backend: supabase).
# One-time, human-confirmed. Demo mode needs no backend. Provisioning touches
# credentials and real infrastructure, so this prints the exact steps rather than
# running them blind — run them yourself / confirm each.
set -euo pipefail

BACKEND="supabase"
if [ -z "$BACKEND" ]; then
  echo "No backend configured (delivery.backend). Demo mode needs none."
  exit 0
fi

echo "Provision backend: $BACKEND"
case "$BACKEND" in
  supabase)
    echo "  1) supabase init"
    echo "  2) supabase link --project-ref <your-ref>"
    echo "  3) set SUPABASE_URL / keys in your env or secret store (never the repo)"
    echo "  4) bash db/migrate.sh apply --yes   # push schema"
    ;;
  neon|postgres|rds)
    echo "  1) create a Postgres database (neon.tech / RDS / Cloud SQL / ...)"
    echo "  2) set DATABASE_URL in your env / secret store"
    echo "  3) bash db/migrate.sh apply --yes"
    ;;
  planetscale)
    echo "  1) pscale database create <name>"
    echo "  2) set DATABASE_URL (pscale connect / branch)"
    echo "  3) bash db/migrate.sh apply --yes"
    ;;
  *)
    echo "  No built-in recipe for '$BACKEND' — see references/backend-provisioning.md."
    ;;
esac
echo "Never commit credentials. Provisioning is a confirmed, one-time step."
