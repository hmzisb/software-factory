#!/usr/bin/env bash
# Install software-factory as a global Claude Code skill.
#   git clone <repo> && bash software-factory/install.sh
# Idempotent. Honors $CLAUDE_SKILLS_DIR (default ~/.claude/skills).
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
NAME="software-factory"
TARGET="$SKILLS_DIR/$NAME"

echo "software-factory installer"
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 is required."; exit 1; }
command -v git >/dev/null 2>&1     || { echo "ERROR: git is required."; exit 1; }

mkdir -p "$SKILLS_DIR"

if [ -L "$TARGET" ]; then
  rm "$TARGET"                       # replace our own old symlink
elif [ -e "$TARGET" ]; then
  echo "ERROR: $TARGET exists and is not a symlink. Remove it manually, then re-run."
  exit 1
fi

ln -s "$SKILL_DIR" "$TARGET"
echo "Installed: $TARGET -> $SKILL_DIR"
echo
echo "Quick check:"
echo "  python3 -m unittest discover -s \"$SKILL_DIR/tests\"   # should pass"
echo
echo "Use it: open any project and run  /software-factory"
