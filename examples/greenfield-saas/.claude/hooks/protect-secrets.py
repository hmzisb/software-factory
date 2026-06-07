#!/usr/bin/env python3
"""PreToolUse/Write|Edit guardrail: block committing secret-shaped values.

Reads the Claude Code hook JSON on stdin. Exit 2 + stderr blocks the write.
Allows obvious placeholders and *.example / test / fixture files. Fail-open on
malformed input.
"""
import json
import re
import sys

SECRET_PATTERNS = [
    r"AKIA[0-9A-Z]{16}",                                  # AWS access key id
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",               # private key block
    r"gh[pousr]_[A-Za-z0-9]{20,}",                       # GitHub token
    r"xox[baprs]-[A-Za-z0-9-]{10,}",                     # Slack token
    r"sk_live_[A-Za-z0-9]{16,}",                         # Stripe live secret key
    r"AIza[0-9A-Za-z_\-]{35}",                           # Google API key
    r'"type"\s*:\s*"service_account"',                   # GCP service-account JSON
    r"(?i)(?:api[_-]?key|secret|token|password|passwd|client[_-]?secret)\s*[:=]\s*['\"][^'\"]{12,}['\"]",
]
PLACEHOLDER = re.compile(
    r"(?i)(your|example|placeholder|changeme|dummy|sample|xxxx|<[^>]+>|\.\.\.)")
# Only example/sample files are exempt — NOT whole test/ or fixtures/ trees, where
# real keys frequently leak. Placeholder VALUES stay allowed everywhere via the
# PLACEHOLDER check below. This is a heuristic gate, not a substitute for a real
# scanner (gitleaks/trufflehog) — see rules/security.md.
ALLOW_FILE = re.compile(r"(?i)(\.example$|\.sample$|\.env\.example$|\.env\.sample$)")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("tool_name") not in ("Write", "Edit", "MultiEdit"):
        return 0
    ti = data.get("tool_input") or {}
    path = ti.get("file_path", "") or ""
    if ALLOW_FILE.search(path):
        return 0
    content = ti.get("content") or ti.get("new_string") or ""
    if isinstance(ti.get("edits"), list):
        content += "\n".join(e.get("new_string", "") for e in ti["edits"])
    for pattern in SECRET_PATTERNS:
        for m in re.finditer(pattern, content):
            if PLACEHOLDER.search(m.group(0)):
                continue
            sys.stderr.write(
                "BLOCKED by protect-secrets: a secret-shaped value is being "
                f"written to {path or 'a file'}.\n"
                f"Match: {m.group(0)[:60]}...\n"
                "Move secrets to an env var / secret store, or use a placeholder "
                "in an .example file.\n")
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
