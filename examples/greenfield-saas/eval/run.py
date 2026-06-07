#!/usr/bin/env python3
"""Probabilistic eval harness for the factory.

A feature is "done" only when the factory produces the right result on a large
number of tries (marmelab's bar). Each case runs N times in a fresh git sandbox;
success rate is compared to a baseline.

HARD checks (drop the success rate): files exist, checks exit 0, mustInvoke,
mustNotInvoke, maxDurationMs, maxCostUsd.
WARN checks (reported, do not fail): mustModify, mustNotModify, expectedDiffStats
(matching crm-builder's run.js split).

Usage:
    python3 eval/run.py [--cases eval/cases.json] [--baseline eval/baseline.json]
                        [--runner "<cmd>"] [--runs N] [--case <id>]
                        [--update-baseline] [--threshold 0.8]

Runner is templated with {prompt}, {id}, {sandbox}, run with cwd = the sandbox.
Stdlib only. Exit non-zero if any case is below threshold or regressed.
"""
import argparse
import fnmatch
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

TOLERANCE = 0.01
COST_RE = re.compile(r'"?total_cost_usd"?\s*[:=]\s*([0-9]+\.?[0-9]*)')


def load_json(path, default=None):
    p = Path(path)
    return json.loads(p.read_text()) if p.exists() else default


def git(args, cwd):
    return subprocess.run(["git", "-C", str(cwd), *args],
                          capture_output=True, text=True)


def baseline_commit(sandbox):
    git(["init", "-q"], sandbox)
    git(["add", "-A"], sandbox)
    git(["-c", "user.email=eval@local", "-c", "user.name=eval",
         "commit", "-q", "--allow-empty", "-m", "base"], sandbox)


def capture_diff(sandbox):
    git(["add", "-A"], sandbox)
    res = git(["diff", "--cached", "--numstat"], sandbox)
    files, added, removed = [], 0, 0
    for line in res.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        a, r, path = parts
        files.append(path)
        added += int(a) if a.isdigit() else 0
        removed += int(r) if r.isdigit() else 0
    return {"files": files, "added": added, "removed": removed}


def seed_sandbox(case, sandbox):
    """Copy a case's seed tree into the empty sandbox before baseline, so a case
    can test 'modify existing code' rather than only from-scratch generation. The
    seed path is relative to the eval's cwd (the project root)."""
    seed = case.get("seed")
    if not seed:
        return
    src = Path(seed)
    if not src.exists():
        raise SystemExit(f"case {case['id']}: seed path not found: {seed}")
    shutil.copytree(src, sandbox, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(".git", "node_modules",
                                                  "worktrees", ".venv", "__pycache__"))


def eval_run(case, runner, sandbox):
    """One attempt. Returns (ok, hard_notes, warn_notes)."""
    hard, warn = [], []
    seed_sandbox(case, sandbox)
    baseline_commit(sandbox)
    cmd = runner.format(prompt=case.get("prompt", ""), id=case["id"], sandbox=str(sandbox))
    t0 = time.monotonic()
    try:
        proc = subprocess.run(cmd, shell=True, cwd=sandbox, capture_output=True,
                              text=True, timeout=case.get("timeout", 300))
    except Exception as e:
        return False, [f"runner error: {e}"], warn
    duration_ms = (time.monotonic() - t0) * 1000
    out = proc.stdout + proc.stderr
    exp = case.get("expect", {}) or {}
    diff = capture_diff(sandbox)
    ok = True

    # --- HARD checks ---
    for f in exp.get("files", []) or []:
        if not (sandbox / f).exists():
            ok = False; hard.append(f"missing file: {f}")
    for chk in exp.get("checks", []) or []:
        if subprocess.run(chk, shell=True, cwd=sandbox,
                          capture_output=True, text=True).returncode != 0:
            ok = False; hard.append(f"check failed: {chk}")
    for a in exp.get("mustInvoke", []) or []:
        if a not in out:
            ok = False; hard.append(f"missing agent/tool: {a}")
    for a in exp.get("mustNotInvoke", []) or []:
        if a in out:
            ok = False; hard.append(f"forbidden agent/tool: {a}")
    if exp.get("maxDurationMs") and duration_ms > exp["maxDurationMs"]:
        ok = False; hard.append(f"too slow: {duration_ms:.0f}ms > {exp['maxDurationMs']}ms")
    if exp.get("maxCostUsd"):
        m = COST_RE.findall(out)
        if not m:
            warn.append("maxCostUsd set but runner printed no total_cost_usd — "
                        "cost not enforced (use --output-format stream-json)")
        else:
            cost = float(m[-1])
            if cost > exp["maxCostUsd"]:
                ok = False; hard.append(f"too costly: ${cost:.2f} > ${exp['maxCostUsd']}")

    # --- WARN checks (do not fail the run) ---
    changed = set(diff["files"])
    for f in exp.get("mustModify", []) or []:
        if f not in changed:
            warn.append(f"expected to modify but didn't: {f}")
    for pat in exp.get("mustNotModify", []) or []:
        for f in changed:
            if fnmatch.fnmatch(f, pat):
                warn.append(f"modified a protected path: {f} (matched {pat})")
    eds = exp.get("expectedDiffStats")
    if eds:
        if "filesChanged" in eds and len(changed) != eds["filesChanged"]:
            warn.append(f"files changed {len(changed)} != expected {eds['filesChanged']}")
        if "linesAdded" in eds and diff["added"] != eds["linesAdded"]:
            warn.append(f"lines added {diff['added']} != expected {eds['linesAdded']}")
        if "linesRemoved" in eds and diff["removed"] != eds["linesRemoved"]:
            warn.append(f"lines removed {diff['removed']} != expected {eds['linesRemoved']}")

    return ok, hard, warn


def score_case(case, runner, runs):
    passes, hard_notes, warn_notes = 0, [], []
    for i in range(runs):
        sandbox = Path(__import__("tempfile").mkdtemp(prefix=f"eval-{case['id']}-"))
        try:
            ok, hard, warn = eval_run(case, runner, sandbox)
            if ok:
                passes += 1
            hard_notes.extend(f"run{i}: {x}" for x in hard)
            warn_notes.extend(f"run{i}: {x}" for x in warn)
        finally:
            shutil.rmtree(sandbox, ignore_errors=True)
    return passes / runs if runs else 0.0, hard_notes, warn_notes


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default="eval/cases.json")
    ap.add_argument("--baseline", default="eval/baseline.json")
    ap.add_argument("--runner", default=None)
    ap.add_argument("--runs", type=int, default=None)
    ap.add_argument("--case", default=None)
    ap.add_argument("--threshold", type=float, default=None)
    ap.add_argument("--update-baseline", action="store_true")
    args = ap.parse_args(argv[1:])

    cfg = load_json("factory.config.json", {}) or {}
    eval_cfg = cfg.get("eval", {}) or {}
    runner = args.runner or eval_cfg.get("runner")
    runs = args.runs or eval_cfg.get("default_runs", 5)
    threshold = args.threshold if args.threshold is not None else \
        eval_cfg.get("success_threshold", 0.8)

    if not runner:
        print("No runner configured. Pass --runner or set eval.runner in "
              "factory.config.json.", file=sys.stderr)
        return 2
    cases = load_json(args.cases, [])
    if not cases:
        print(f"No cases in {args.cases}.", file=sys.stderr)
        return 2
    if args.case:
        cases = [c for c in cases if c["id"] == args.case]
    baseline = (load_json(args.baseline, {}) or {}).get("cases", {})

    print(f"Running {len(cases)} case(s) x {runs} run(s), threshold {threshold:.0%}\n")
    print(f"{'Case':<24}{'Rate':<10}{'Baseline':<12}{'Status'}")
    print("-" * 64)

    results, failed = {}, False
    for case in cases:
        rate, hard, warn = score_case(case, runner, runs)
        results[case["id"]] = rate
        base = baseline.get(case["id"])
        regressed = base is not None and rate < base - TOLERANCE
        below = rate < threshold
        status = "OK"
        if below:
            status, failed = "BELOW THRESHOLD", True
        if regressed:
            status, failed = f"REGRESSED (was {base:.0%})", True
        base_s = f"{base:.0%}" if base is not None else "-"
        print(f"{case['id']:<24}{rate:<10.0%}{base_s:<12}{status}")
        for n in hard[:5]:
            print(f"    x {n}")
        for n in warn[:5]:
            print(f"    ! {n}")

    if args.update_baseline:
        Path(args.baseline).write_text(
            json.dumps({"threshold": threshold, "cases": results}, indent=2) + "\n")
        print(f"\nBaseline updated: {args.baseline}")
    print()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
