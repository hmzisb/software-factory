#!/usr/bin/env bash
# Deploy Tasker -> vercel.
# Gated + verify-first. Dry by default; pass --yes (or CONFIRM=1) to actually
# deploy. Irreversible steps always require explicit confirmation.
set -euo pipefail

TARGET="vercel"
echo "Deploy target: ${TARGET:-<unset>}"

echo "Verifying before deploy (never ship red)..."
pnpm run build
pnpm test

PLAN_ONLY=
if [ "${1:-}" != "--yes" ] && [ "${CONFIRM:-}" != "1" ]; then
  PLAN_ONLY=1
fi

run_deploy() {
  case "$TARGET" in
    vercel*)                      npx vercel deploy --prod ;;
    netlify*)                     npx netlify deploy --prod ;;
    fly*|fly.io)                  flyctl deploy ;;
    cloudflare*|workers*|pages*)  npx wrangler deploy ;;
    render*)                      echo "Render auto-deploys on push to the connected branch — push to deploy." ;;
    "" )                          echo "No deploy target set. Set delivery.deploy_target in factory.config.json."; return 1 ;;
    *)                            echo "No built-in recipe for '$TARGET' — see references/deploy-recipes.md and add the step."; return 1 ;;
  esac
}

if [ -n "$PLAN_ONLY" ]; then
  echo "Dry run — would deploy to '$TARGET'. Re-run with --yes (or CONFIRM=1) to deploy."
else
  run_deploy
  echo "Deploy step finished. Verify the live URL."
fi
