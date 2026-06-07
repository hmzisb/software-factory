#!/usr/bin/env bash
# End-to-end demo of the software-factory PIPELINE — no API key, fully reproducible.
#
# It proves the parts that are deterministic and ours to guarantee:
#   detect -> scaffold a real factory -> the generated artifacts actually run
#   (gated deploy dry, gated migration dry, guardrail hook blocks a force-push)
#   -> the probabilistic eval harness closes the loop with a model-free runner.
#
# It does NOT call a model: autonomous feature-building quality is model/prompt
# dependent and is measured by the eval YOU configure (see ../../LIMITATIONS.md).
set -u

SKILL_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fail() { echo "DEMO FAILED: $1" >&2; exit 1; }
step() { printf '  %-52s' "$1"; }
ok() { echo "ok"; }

echo "software-factory demo — scaffolding a factory in $TMP"

# 1. A minimal, valid config (stdlib-python stack so the gates run anywhere).
cat > "$TMP/factory.config.json" <<'JSON'
{
  "version": 1,
  "validated": true,
  "mode": "greenfield",
  "project": { "name": "Demo", "one_liner": "A scaffold-pipeline smoke demo." },
  "stack": { "language": "python", "package_manager": "pip", "runtime": "python" },
  "quality": { "test_cmd": "python3 -c pass", "build_cmd": "" },
  "delivery": { "deploy_target": "fly.io", "migration_tool": "alembic", "data_mode": "full" },
  "factory": { "layers": [0] },
  "interview_progress": { "d1_product": "done" }
}
JSON

step "detect"
python3 "$SKILL_DIR/scripts/detect.py" "$TMP" >/dev/null || fail "detect"; ok

step "scaffold (refuses invalid config too)"
python3 "$SKILL_DIR/scripts/scaffold.py" "$TMP/factory.config.json" \
  --target "$TMP" --no-git >/dev/null || fail "scaffold"; ok
cd "$TMP"   # everything below runs from the generated project, like a real factory

step "core artifacts written"
for f in CLAUDE.md CONTEXT.md .gitignore .claude/settings.json \
         .claude/agents/orchestrator.md eval/run.py deploy/deploy.sh db/migrate.sh; do
  test -f "$TMP/$f" || fail "missing $f"
done; ok

step "guardrail hook blocks a force-push"
if echo '{"tool_name":"Bash","tool_input":{"command":"git push --force origin main"}}' \
     | python3 .claude/hooks/block-dangerous-git.py >/dev/null 2>&1; then
  fail "force-push was not blocked"
fi; ok

step "gated deploy is dry by default (never ships red)"
bash deploy/deploy.sh 2>&1 | grep -q "Dry run" || fail "deploy not dry"; ok

step "gated migration is dry by default"
bash db/migrate.sh apply 2>&1 | grep -q "Dry run" || fail "migrate not dry"; ok

step "probabilistic eval closes the loop (5 runs)"
echo '[{"id":"scaffolds-a-file","prompt":"create hello","expect":{"files":["hello.txt"]}}]' \
  > eval/cases.json
python3 eval/run.py --cases eval/cases.json --baseline eval/baseline.json \
  --runner "touch hello.txt" --runs 5 --update-baseline 2>&1 \
  | grep -q "100%" || fail "eval did not reach 100%"; ok

echo
echo "DEMO OK — detect -> scaffold -> generated artifacts run -> eval green."
echo "Next, on a real project: run /software-factory, then drive it with"
echo "/factory-build \"<your feature>\". See ../../LIMITATIONS.md for what is and"
echo "isn't guaranteed."
