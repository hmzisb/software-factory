#!/usr/bin/env python3
"""Visual check: load a URL, assert what a user should see, optionally screenshot.

Used as an eval `checks` entry and by the visual-testing skill. If Playwright
isn't installed it SKIPS (exit 0 + a note) so it never blocks a non-visual env —
install Playwright where you want the gate enforced.

Usage:
    python3 eval/visual_check.py <url> [--has-text T]... [--selector S]...
                                        [--screenshot path] [--timeout MS]

Exit 0 = all assertions held (or skipped). Exit 1 = an assertion failed.
"""
import argparse
import sys


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--has-text", action="append", default=[])
    ap.add_argument("--selector", action="append", default=[])
    ap.add_argument("--screenshot")
    ap.add_argument("--timeout", type=int, default=15000)
    args = ap.parse_args(argv[1:])

    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        print("playwright not installed — visual check skipped "
              "(`pip install playwright && playwright install chromium`).",
              file=sys.stderr)
        return 0

    failures = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            page.goto(args.url, timeout=args.timeout, wait_until="load")
            if args.screenshot:
                page.screenshot(path=args.screenshot, full_page=True)
            body = page.content()
            for t in args.has_text:
                if t not in body:
                    failures.append(f"text not found: {t!r}")
            for sel in args.selector:
                if page.query_selector(sel) is None:
                    failures.append(f"selector not found: {sel}")
        except Exception as e:
            failures.append(f"navigation/render error: {e}")
        finally:
            browser.close()

    if failures:
        for f in failures:
            print(f"visual check FAILED: {f}", file=sys.stderr)
        return 1
    print(f"visual check OK: {args.url}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
