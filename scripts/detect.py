#!/usr/bin/env python3
"""Detect the target project's mode and stack for the software-factory interview.

Usage:
    python3 detect.py [target-dir]      # default: cwd

Prints a JSON object to stdout:
    {
      "mode": "greenfield" | "retrofit",
      "config_exists": bool,
      "stack": {"language","framework","database","package_manager","runtime"},
      "commands": {"test_cmd","build_cmd","lint_cmd","typecheck_cmd"},
      "ci_exists": bool
    }

Stdlib only. Best-effort detection — every field is a starting point the
interview confirms with the user.
"""
import json
import os
import sys
from pathlib import Path

try:
    import tomllib  # py3.11+
except Exception:  # pragma: no cover
    tomllib = None


def _read_json(p: Path):
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def _is_empty_project(root: Path) -> bool:
    """Empty = no source-ish files (ignoring VCS, the factory config, dotfiles)."""
    ignore = {".git", ".hg", ".svn", "factory.config.json", ".DS_Store"}
    for entry in root.iterdir():
        if entry.name in ignore:
            continue
        if entry.name.startswith(".") and entry.is_file():
            continue
        return False
    return True


def _detect_node(root: Path, stack, commands):
    pkg = _read_json(root / "package.json")
    if pkg is None:
        return False
    stack["language"] = "typescript" if (root / "tsconfig.json").exists() else "javascript"
    # package manager from lockfile
    if (root / "pnpm-lock.yaml").exists():
        pm = "pnpm"
    elif (root / "yarn.lock").exists():
        pm = "yarn"
    elif (root / "bun.lockb").exists():
        pm = "bun"
    else:
        pm = "npm"
    stack["package_manager"] = pm
    stack["runtime"] = "node"
    run = f"{pm} run" if pm != "npm" else "npm run"
    scripts = pkg.get("scripts", {}) or {}
    if "test" in scripts:
        commands["test_cmd"] = f"{pm} test"
    if "build" in scripts:
        commands["build_cmd"] = f"{run} build"
    if "lint" in scripts:
        commands["lint_cmd"] = f"{run} lint"
    for tc in ("typecheck", "type-check", "tsc"):
        if tc in scripts:
            commands["typecheck_cmd"] = f"{run} {tc}"
            break
    else:
        if stack["language"] == "typescript":
            commands["typecheck_cmd"] = "npx tsc --noEmit"
    # framework guess from deps
    deps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {})}
    for name, label in (("next", "next"), ("react", "react"), ("vue", "vue"),
                        ("svelte", "svelte"), ("@angular/core", "angular"),
                        ("express", "express"), ("fastify", "fastify")):
        if name in deps:
            stack["framework"] = label
            break
    return True


def _detect_python(root: Path, stack, commands):
    markers = ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"]
    if not any((root / m).exists() for m in markers):
        return False
    stack["language"] = "python"
    stack["runtime"] = "python"
    deps_text = ""
    pyproject = root / "pyproject.toml"
    data = {}
    if pyproject.exists() and tomllib:
        try:
            data = tomllib.loads(pyproject.read_text())
        except Exception:
            data = {}
        deps_text = pyproject.read_text()
    for req in ("requirements.txt", "requirements-dev.txt"):
        if (root / req).exists():
            deps_text += "\n" + (root / req).read_text()
    # test
    if "pytest" in deps_text or (root / "tests").exists() or (root / "test").exists():
        commands["test_cmd"] = "pytest"
    else:
        commands["test_cmd"] = "python -m unittest"
    if "ruff" in deps_text:
        commands["lint_cmd"] = "ruff check ."
    elif "flake8" in deps_text:
        commands["lint_cmd"] = "flake8"
    if "mypy" in deps_text:
        commands["typecheck_cmd"] = "mypy ."
    # package manager
    if (root / "poetry.lock").exists():
        stack["package_manager"] = "poetry"
    elif (root / "uv.lock").exists():
        stack["package_manager"] = "uv"
    else:
        stack["package_manager"] = "pip"
    # framework
    for name, label in (("django", "django"), ("flask", "flask"),
                        ("fastapi", "fastapi")):
        if name in deps_text.lower():
            stack["framework"] = label
            break
    return True


def _detect_go(root: Path, stack, commands):
    if not (root / "go.mod").exists():
        return False
    stack["language"] = "go"
    stack["runtime"] = "go"
    stack["package_manager"] = "go modules"
    commands["test_cmd"] = "go test ./..."
    commands["build_cmd"] = "go build ./..."
    commands["lint_cmd"] = "go vet ./..."
    return True


def _detect_rust(root: Path, stack, commands):
    if not (root / "Cargo.toml").exists():
        return False
    stack["language"] = "rust"
    stack["runtime"] = "cargo"
    stack["package_manager"] = "cargo"
    commands["test_cmd"] = "cargo test"
    commands["build_cmd"] = "cargo build"
    commands["lint_cmd"] = "cargo clippy"
    return True


def detect(root: Path) -> dict:
    stack = {"language": "", "framework": "", "database": "",
             "package_manager": "", "runtime": ""}
    commands = {"test_cmd": "", "build_cmd": "", "lint_cmd": "", "typecheck_cmd": ""}

    config_exists = (root / "factory.config.json").exists()
    empty = _is_empty_project(root)

    if not empty:
        for fn in (_detect_node, _detect_python, _detect_go, _detect_rust):
            if fn(root, stack, commands):
                break

    ci_exists = (root / ".github" / "workflows").is_dir() or (root / ".gitlab-ci.yml").exists()

    # A validated config already present means the factory is set up — resume.
    mode = "greenfield" if empty else "retrofit"
    if config_exists:
        cfg = _read_json(root / "factory.config.json") or {}
        if cfg.get("validated"):
            mode = "resume"

    return {
        "mode": mode,
        "config_exists": config_exists,
        "stack": stack,
        "commands": commands,
        "ci_exists": ci_exists,
    }


def main(argv):
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path.cwd()
    if not root.exists():
        print(json.dumps({"error": f"target not found: {root}"}))
        return 1
    print(json.dumps(detect(root), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
