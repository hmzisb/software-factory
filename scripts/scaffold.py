#!/usr/bin/env python3
"""Deterministically scaffold a software factory from a validated config.

Usage:
    python3 scaffold.py [factory.config.json] --target <dir> [--dry-run] [--no-git]

Contract: see references/scaffold-algorithm.md. Same config -> byte-identical
tree. Greenfield writes everything; retrofit merges and never clobbers.

Stdlib only.
"""
import argparse
import copy
import json
import re
import subprocess
import sys
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
SCHEMA = TEMPLATES / "factory.config.schema.json"
PLACEHOLDER = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")
BEGIN = "<!-- BEGIN software-factory -->"
END = "<!-- END software-factory -->"

CLAUDE_DIRS = {"agents", "commands", "skills", "rules", "hooks"}
TARGET_DIRS = {"docs", "specs", "plans", "eval", ".github"}
REQUIRED = {"project.name", "project.one_liner", "stack.language", "quality.test_cmd",
            "factory.layers"}

AGENT_TABLE_MD = """| Agent | Model | Role |
|---|---|---|
| orchestrator | sonnet | Classifies, plans, dispatches, gates, reports. Never edits. |
| planner | sonnet | Decomposes a request into vertical-slice tickets in waves. |
| developer | opus | Implements one ticket in a worktree, TDD-first, commits. |
| reviewer | sonnet | Semantic + security review of the diff. |
| test-validator | sonnet | Confirms the change is adequately tested. |
| merger | haiku | The only agent that merges (`--no-ff`). |
| documentator | sonnet | Updates CONTEXT.md / ADRs / learnings after merge. |"""


# ---- config access ---------------------------------------------------------

def cfg_get(config, dotted):
    cur = config
    for key in dotted.split("."):
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return None
    return cur


def _scalar(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


# ---- computed fragments ----------------------------------------------------

def build_ci_setup(stack):
    """GitHub Actions toolchain-setup steps for the detected stack, 6-space
    indented to sit under `steps:`. Emits real setup so generated CI runs out of
    the box (no TODO stub)."""
    lang = (stack.get("language") or "").lower()
    pm = (stack.get("package_manager") or "").lower()
    if lang in ("typescript", "javascript"):
        lines = []
        if pm == "pnpm":
            lines.append("      - uses: pnpm/action-setup@v4")
        elif pm == "bun":
            lines.append("      - uses: oven-sh/setup-bun@v2")
        if pm != "bun":
            cache = pm if pm in ("npm", "pnpm", "yarn") else "npm"
            lines += ["      - uses: actions/setup-node@v4",
                      "        with:",
                      "          node-version: '20'",
                      f"          cache: '{cache}'"]
        install = {"npm": "npm ci", "pnpm": "pnpm install --frozen-lockfile",
                   "yarn": "yarn install --frozen-lockfile",
                   "bun": "bun install"}.get(pm, "npm install")
        lines += ["      - name: Install dependencies", f"        run: {install}"]
        return "\n".join(lines)
    if lang == "python":
        lines = []
        if pm == "uv":
            lines.append("      - uses: astral-sh/setup-uv@v5")
        lines += ["      - uses: actions/setup-python@v5",
                  "        with:", "          python-version: '3.12'"]
        if pm == "poetry":
            install = "          pipx install poetry\n          poetry install"
        elif pm == "uv":
            install = "          uv sync"
        else:
            install = ("          python -m pip install --upgrade pip\n"
                       "          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi\n"
                       "          if [ -f pyproject.toml ]; then pip install -e . || true; fi")
        lines += ["      - name: Install dependencies", "        run: |", install]
        return "\n".join(lines)
    if lang == "go":
        return ("      - uses: actions/setup-go@v5\n        with:\n"
                "          go-version: 'stable'\n"
                "      - name: Download modules\n        run: go mod download")
    if lang == "rust":
        return ("      - name: Fetch dependencies\n        run: cargo fetch")
    return (f"      # TODO: add toolchain setup for '{lang or 'your language'}' "
            "and install dependencies before the steps below.")


def build_computed(config):
    domain = config.get("domain") or {}
    quality = config.get("quality") or {}
    factory = config.get("factory") or {}
    nfrs = config.get("nfrs") or {}
    uses = config.get("uses_external_skills") or {}

    # entities
    entities = domain.get("entities") or []
    if entities:
        lines = []
        for e in entities:
            line = f"- **{e.get('name','')}**"
            if e.get("description"):
                line += f" — {e['description']}"
            rel = e.get("relationships") or []
            if rel:
                line += f" (related: {', '.join(rel)})"
            lines.append(line)
        entities_md = "\n".join(lines)
    else:
        entities_md = "_No entities defined yet._"

    # glossary (sorted keys for determinism)
    gloss = domain.get("glossary") or {}
    if gloss:
        glossary_md = "\n".join(f"- **{k}** — {gloss[k]}" for k in sorted(gloss))
    else:
        glossary_md = "_No glossary yet._"

    # workflows
    wfs = domain.get("workflows") or []
    workflows_md = "\n".join(f"{i+1}. {w}" for i, w in enumerate(wfs)) if wfs \
        else "_No workflows defined yet._"

    # validation block
    cmds = []
    for label, key in (("Tests", "test_cmd"), ("Typecheck", "typecheck_cmd"),
                       ("Lint", "lint_cmd"), ("Build", "build_cmd")):
        val = quality.get(key)
        if val:
            cmds.append(val)
    validation_block = ("```\n" + "\n".join(cmds) + "\n```") if cmds \
        else "_No validation commands configured._"

    # discipline note
    if uses.get("superpowers") or uses.get("mattpocock"):
        names = []
        if uses.get("superpowers"):
            names.append("`superpowers`")
        if uses.get("mattpocock"):
            names.append("`mattpocock`")
        discipline_note = (f"Detected {', '.join(names)} installed — prefer those "
                           "skills. The vendored copies in `.claude/skills/` are the "
                           "self-contained fallback.")
    else:
        discipline_note = ("Discipline is vendored in `.claude/skills/` "
                           "(tdd, verification, writing-plans, brainstorming, "
                           "worktrees) — no external plugins required.")

    # layers note
    layers = factory.get("layers") or [0]
    if 1 in layers:
        layers_note = ("**Layer 1 (product factory) is enabled** — a self-modifying "
                       "product layer (builder UI + deploy) lives alongside the dev "
                       "harness.")
    else:
        layers_note = "Layer 0 (dev harness) only. Layer 1 (product factory) not generated."

    # wave math
    n = factory.get("agent_team_size") or 3
    wave_math = (f"Wave size **N = {n}**. A wave dispatches **{3*n+1}** agents "
                 f"({n} developers + {2*n} reviewers + 1 merger).")

    # security
    sec = nfrs.get("security") or []
    security_md = "; ".join(sec) if sec else \
        "validate at boundaries; never commit secrets; enforce auth/scope."

    # CI toolchain setup (GitHub Actions, 6-space indent under steps:)
    ci_setup = build_ci_setup(config.get("stack") or {})

    # CI steps (GitHub Actions, 6-space indent under steps:)
    ci_pairs = [("Tests", "test_cmd"), ("Typecheck", "typecheck_cmd"),
                ("Lint", "lint_cmd"), ("Build", "build_cmd")]
    ci_lines = []
    for name, key in ci_pairs:
        val = quality.get(key)
        if val:
            ci_lines.append(f"      - name: {name}\n        run: {val}")
    if not ci_lines:
        ci_lines.append("      - name: No validation commands configured\n"
                        "        run: echo \"set quality.* in factory.config.json\"")
    ci_steps = "\n".join(ci_lines)

    return {
        "entities_md": entities_md,
        "glossary_md": glossary_md,
        "workflows_md": workflows_md,
        "agent_table_md": AGENT_TABLE_MD,
        "validation_block": validation_block,
        "discipline_note": discipline_note,
        "layers_note": layers_note,
        "wave_math": wave_math,
        "security_md": security_md,
        "ci_setup": ci_setup,
        "ci_steps": ci_steps,
    }


# ---- rendering -------------------------------------------------------------

def render(text, config, computed):
    def repl(m):
        key = m.group(1)
        if key.startswith("computed."):
            return computed.get(key[len("computed."):], "")
        return _scalar(cfg_get(config, key))
    return PLACEHOLDER.sub(repl, text)


# ---- destination mapping ---------------------------------------------------

def dest_for(rel, layers):
    """Return the path (relative to target) for a template file, or None to skip."""
    if rel == "factory.config.schema.json":
        return None
    parts = rel.split("/")
    first = parts[0]
    if first == "layer1":
        if 1 not in layers:
            return None
        return dest_for("/".join(parts[1:]), layers)
    if rel == "settings.json.tmpl":
        base = ".claude/settings.json"
    elif first in CLAUDE_DIRS:
        base = ".claude/" + rel
    elif first in TARGET_DIRS:
        base = rel
    else:
        base = rel  # root files (CLAUDE.md.tmpl, CONTEXT.md.tmpl, ...)
    if base.endswith(".tmpl"):
        base = base[:-5]
    return base


# ---- merge helpers (retrofit) ----------------------------------------------

def managed_merge(existing, new_body):
    block = f"{BEGIN}\n{new_body.strip()}\n{END}"
    if BEGIN in existing and END in existing:
        pre = existing.split(BEGIN)[0]
        post = existing.split(END, 1)[1]
        return pre + block + post
    sep = "" if existing.endswith("\n") else "\n"
    return existing + sep + "\n" + block + "\n"


def deep_merge_json(existing, new):
    out = copy.deepcopy(existing)
    for k, v in new.items():
        if k not in out:
            out[k] = v
        elif isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge_json(out[k], v)
        elif isinstance(out[k], list) and isinstance(v, list):
            out[k] = out[k] + [x for x in v if x not in out[k]]
        # else keep existing (user wins)
    return out


# ---- main scaffold ---------------------------------------------------------

def scaffold(config, target, dry_run=False, no_git=False):
    mode = config.get("mode", "greenfield")
    layers = (config.get("factory") or {}).get("layers") or [0]
    computed = build_computed(config)

    report = {"ADDED": [], "MERGED": [], "SKIPPED": [], "BACKED-UP": []}

    files = sorted(p for p in TEMPLATES.rglob("*")
                   if p.is_file() and "__pycache__" not in p.parts
                   and p.suffix != ".pyc")
    for tpl in files:
        rel = tpl.relative_to(TEMPLATES).as_posix()
        dest_rel = dest_for(rel, layers)
        if dest_rel is None:
            continue
        dest = target / dest_rel
        basename = Path(dest_rel).name
        exists = dest.exists()
        is_tmpl = rel.endswith(".tmpl")

        # Non-template static assets (index.html, images, .gitkeep): binary-safe
        # copy. They are never the merge-special files (those are all .tmpl).
        if not is_tmpl:
            if mode == "retrofit" and exists:
                report["SKIPPED"].append(dest_rel)
                continue
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(tpl.read_bytes())
                if dest_rel.endswith(".sh"):
                    dest.chmod(0o755)
            report["ADDED"].append(dest_rel)
            continue

        content = render(tpl.read_text(), config, computed)

        if mode == "retrofit" and exists:
            if basename in ("CLAUDE.md", "CONTEXT.md"):
                if not dry_run:
                    bak = dest.with_suffix(dest.suffix + ".bak")
                    if not bak.exists():  # preserve the ORIGINAL, pre-factory file
                        bak.write_text(dest.read_text())
                    dest.write_text(managed_merge(dest.read_text(), content))
                report["BACKED-UP"].append(dest_rel + ".bak")
                report["MERGED"].append(dest_rel)
            elif dest_rel == ".claude/settings.json":
                if not dry_run:
                    bak = dest.with_suffix(".json.bak")
                    if not bak.exists():  # preserve the ORIGINAL
                        bak.write_text(dest.read_text())
                    merged = deep_merge_json(json.loads(dest.read_text()),
                                             json.loads(content))
                    dest.write_text(json.dumps(merged, indent=2) + "\n")
                report["BACKED-UP"].append(dest_rel + ".bak")
                report["MERGED"].append(dest_rel)
            else:
                report["SKIPPED"].append(dest_rel)
            continue

        # greenfield, or retrofit + file absent
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content)
            if dest_rel.endswith(".sh"):
                dest.chmod(0o755)
        report["ADDED"].append(dest_rel)

    # write the factory config into the target
    if not dry_run:
        (target / "factory.config.json").write_text(
            json.dumps(config, indent=2) + "\n")
    if "factory.config.json" not in report["ADDED"]:
        report["ADDED"].append("factory.config.json")

    # git init for greenfield
    if mode == "greenfield" and not no_git and not dry_run and not (target / ".git").exists():
        try:
            subprocess.run(["git", "init", "-q"], cwd=target, check=True)
        except Exception as e:
            report.setdefault("WARN", []).append(f"git init failed: {e}")

    return report


# ---- minimal JSON-Schema validation (stdlib only) -------------------------

_JSON_TYPES = {
    "object": dict, "array": list, "string": str, "integer": int,
    "number": (int, float), "boolean": bool, "null": type(None),
}


def _type_ok(value, type_spec):
    types = type_spec if isinstance(type_spec, list) else [type_spec]
    for t in types:
        py = _JSON_TYPES.get(t)
        if py is None:
            return True  # unknown type keyword — don't reject
        # bool is a subclass of int — keep them distinct
        if t == "integer" and isinstance(value, bool):
            continue
        if t == "number" and isinstance(value, bool):
            continue
        if isinstance(value, py):
            return True
    return False


def _validate_node(value, schema, path, errors):
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} not in {schema['enum']}")
    if "type" in schema and not _type_ok(value, schema["type"]):
        errors.append(f"{path}: expected type {schema['type']}, got {type(value).__name__}")
        return  # type wrong — deeper checks would be noise
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for req in schema.get("required", []):
            if req not in value:
                errors.append(f"{path}: missing required key '{req}'")
        if schema.get("additionalProperties") is False:
            for k in value:
                if k not in props:
                    errors.append(f"{path}: unknown key '{k}'")
        for k, v in value.items():
            if k in props:
                _validate_node(v, props[k], f"{path}.{k}", errors)
    elif isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: needs at least {schema['minItems']} item(s)")
        item_schema = schema.get("items")
        if item_schema:
            for i, item in enumerate(value):
                _validate_node(item, item_schema, f"{path}[{i}]", errors)
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: {value} < minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: {value} > maximum {schema['maximum']}")


def validate_against_schema(config):
    """Best-effort structural check against factory.config.schema.json. Returns a
    list of human-readable problems (empty = clean). Stdlib only — supports the
    subset of draft-07 the schema uses (type/required/enum/const/items/
    additionalProperties/minItems/min-max)."""
    try:
        schema = json.loads(SCHEMA.read_text())
    except Exception:
        return []  # no schema available — skip structural validation
    errors = []
    _validate_node(config, schema, "config", errors)
    return errors


def validate_config(config):
    missing = [k for k in REQUIRED if cfg_get(config, k) in (None, "")]
    if missing:
        raise SystemExit(f"config missing required keys: {', '.join(sorted(missing))}")
    problems = validate_against_schema(config)
    if problems:
        raise SystemExit("config does not match factory.config.schema.json:\n  - "
                         + "\n  - ".join(problems))
    if not config.get("validated"):
        raise SystemExit("config.validated is not true — finish the interview first.")


def print_report(report, mode, dry_run):
    tag = " (dry-run)" if dry_run else ""
    print(f"\nsoftware-factory scaffold — mode: {mode}{tag}\n")
    for key in ("ADDED", "MERGED", "SKIPPED", "BACKED-UP"):
        items = report.get(key) or []
        if items:
            print(f"{key} ({len(items)}):")
            for it in sorted(items):
                print(f"  {it}")
            print()
    for w in report.get("WARN", []):
        print(f"WARN: {w}")


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("config", nargs="?", help="path to factory.config.json")
    ap.add_argument("--target", default=".", help="target project dir (default: cwd)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-git", action="store_true")
    args = ap.parse_args(argv[1:])

    target = Path(args.target).resolve()
    config_path = Path(args.config) if args.config else target / "factory.config.json"
    if not config_path.exists():
        raise SystemExit(f"config not found: {config_path}")
    config = json.loads(config_path.read_text())

    validate_config(config)
    target.mkdir(parents=True, exist_ok=True)
    report = scaffold(config, target, dry_run=args.dry_run, no_git=args.no_git)
    print_report(report, config.get("mode", "greenfield"), args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
