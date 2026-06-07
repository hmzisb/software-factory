#!/usr/bin/env python3
"""Clone a starter template as the base app, then strip its git history.

The factory specializes a working starter instead of building from zero
(marmelab's 'don't reinvent the wheel'). After this runs, scaffold.py stamps the
harness on top in retrofit mode, and a fresh `git init` makes it the user's repo.

Usage:
    python3 fetch_starter.py --id <starter-id> --target <dir>
    python3 fetch_starter.py --repo <url> [--ref <ref>] --target <dir>
    python3 fetch_starter.py --list

Prints a JSON line with the resolved starter (stack + dev_cmd) so the interview
can pre-fill answers. Stdlib only.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

REGISTRY = Path(__file__).resolve().parent / "starters.json"


def load_registry():
    return json.loads(REGISTRY.read_text()).get("starters", [])


def find(starter_id):
    for s in load_registry():
        if s["id"] == starter_id:
            return s
    return None


def clone(repo, ref, target):
    target = Path(target)
    target.mkdir(parents=True, exist_ok=True)
    if any(target.iterdir()):
        raise SystemExit(f"target not empty: {target} (clone needs an empty dir)")
    cmd = ["git", "clone", "--depth", "1"]
    if ref:
        cmd += ["--branch", ref]
    cmd += [repo, str(target)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise SystemExit(f"clone failed: {res.stderr.strip()}")
    shutil.rmtree(target / ".git", ignore_errors=True)  # detach from upstream


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--id")
    ap.add_argument("--repo")
    ap.add_argument("--ref")
    ap.add_argument("--target")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv[1:])

    if args.list:
        for s in load_registry():
            print(f"{s['id']:<20} {s['title']}")
        return 0

    repo, ref, resolved = args.repo, args.ref, {}
    if args.id:
        s = find(args.id)
        if not s:
            raise SystemExit(f"unknown starter id: {args.id} (try --list)")
        resolved = s
        if s.get("repo") is None:  # blank
            print(json.dumps({"id": s["id"], "starter": False, **s}))
            return 0
        repo, ref = s["repo"], s.get("ref")

    if not repo:
        raise SystemExit("need --id or --repo")
    if not args.target:
        raise SystemExit("need --target")

    clone(repo, ref, args.target)
    print(json.dumps({"starter": True, "repo": repo, "ref": ref,
                      "dev_cmd": resolved.get("dev_cmd", ""),
                      "stack": resolved.get("stack", {})}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
