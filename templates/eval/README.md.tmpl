# Eval — probabilistic validation

Agentic output is probabilistic. A feature is **done** only when the factory
produces the right result on a large number of tries. This harness measures that.

## Run

```bash
python3 eval/run.py --runner 'claude -p "{prompt}" --dangerously-skip-permissions'
# or set eval.runner in factory.config.json and just:
python3 eval/run.py
```

Each case runs N times (default 5) in a fresh sandbox. Success rate is compared
to `eval/baseline.json`. Exit code is non-zero if any case falls below the
threshold or regresses vs the baseline.

## Authoring cases (`cases.json`)

```json
[
  {
    "id": "unique-id",
    "prompt": "what to ask the factory",
    "timeout": 600,
    "expect": {
      "mustInvoke":     ["developer", "reviewer"],   // HARD: strings that must appear in runner output
      "mustNotInvoke":  ["planner"],                  // HARD: strings that must NOT appear
      "files":          ["src/feature.ts"],           // HARD: paths that must exist in the sandbox
      "checks":         ["npm test"],                 // HARD: shell commands that must exit 0 (cwd = sandbox)
      "maxDurationMs":  1800000,                      // HARD: wall-clock cap per run
      "maxCostUsd":     6.0,                           // HARD: parsed from runner output's total_cost_usd
      "mustModify":     ["src/feature.ts"],           // WARN: files that should have changed (git diff)
      "mustNotModify":  ["**/auth/**", "**/billing/**"], // WARN: protected globs that must stay untouched
      "expectedDiffStats": { "filesChanged": 4, "linesAdded": 30, "linesRemoved": 0 } // WARN
    }
  }
]
```

**HARD** checks drop the success rate. **WARN** checks (`mustModify`,
`mustNotModify`, `expectedDiffStats`) are reported (`!`) but never fail a run —
same split as crm-builder's `run.js`. Diff-based checks use a git baseline taken
in the sandbox before the runner.

The runner is templated with `{prompt}`, `{id}`, `{sandbox}` and runs with
cwd = the sandbox. It must produce its output there so checks can be evaluated.

## Update the baseline

```bash
python3 eval/run.py --update-baseline
```

Do this only when the new rates are intentionally the new known-good. Commit the
baseline so CI can detect regressions.

## CI

`.github/workflows/factory-ci.yml` runs the validation gates on every PR. Wire
the eval into a scheduled or label-triggered job once a runner is available in CI.
