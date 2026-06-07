---
description: Capture a screenshot of the running app so the user can see a change.
argument-hint: "<path or URL> [text to expect]"
---

Show the user the app, visually. For: **$ARGUMENTS**

1. Make sure the app is running (`/factory-preview` or `python3 scripts/preview.py`).
2. Capture the screen with the visual checker (`.claude/skills/visual-testing`):
   ```
   python3 eval/visual_check.py <url> --has-text "<expected text>" --screenshot proof.png
   ```
3. Show `proof.png` to the user and describe, in plain language, what's visible
   ("Here's the new priority badge on your tasks").

Never tell a non-technical user "the tests pass" — show them the screen.
