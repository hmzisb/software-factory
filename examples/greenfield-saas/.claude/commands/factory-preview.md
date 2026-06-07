---
description: Run the app live so you can see and try it in the browser.
---

Start a live preview of Tasker.

Run the project's dev server (from `factory.config.json` — `quality.dev_cmd`,
falling back to the starter's dev command):

```

```

If a `preview.py` from the software-factory skill is available, you can also run
`python3 preview.py`. Once it's up, open the printed local URL and try the app.
Report the URL to the user in plain language ("Your app is running at … — take a
look").

If there is no dev command configured, ask the user how they normally run the
app, then save it to `quality.dev_cmd`.
