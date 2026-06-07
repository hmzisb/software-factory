#!/usr/bin/env python3
"""Run the project's dev server so a non-coder can see the app live.

Resolves the dev command from factory.config.json (quality.dev_cmd, else
starter.dev_cmd) and runs it in the project dir. Use --dry to print without
running. Stdlib only.

Usage:
    python3 preview.py [--target <dir>] [--dry]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def get_dev_cmd(config):
    quality = config.get("quality") or {}
    if quality.get("dev_cmd"):
        return quality["dev_cmd"]
    starter = config.get("starter") or {}
    return starter.get("dev_cmd") or ""


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default=".")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args(argv[1:])

    target = Path(args.target).resolve()
    cfg_path = target / "factory.config.json"
    if not cfg_path.exists():
        print(f"no factory.config.json in {target}", file=sys.stderr)
        return 2
    config = json.loads(cfg_path.read_text())
    cmd = get_dev_cmd(config)
    if not cmd:
        print("No dev command configured (set quality.dev_cmd in "
              "factory.config.json).", file=sys.stderr)
        return 2

    print(f"Starting preview: {cmd}  (cwd: {target})")
    if args.dry:
        return 0
    try:
        return subprocess.run(cmd, shell=True, cwd=target).returncode
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
