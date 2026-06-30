#!/usr/bin/env python3
# Fetcher plugin (layer 1): google via Botasaurus anti-detect browser.
#
# curl and plain headless Chrome hit Google's "unusual traffic" CAPTCHA wall.
# Botasaurus launches an undetected, humanized Chrome that gets past it. This
# fetcher renders the SERP and writes raw HTML to stdout for open-serpapi.
#
#   python3 fetchers/google-botasaurus.py "machin programming language" \
#     | ./open-serpapi parse --engine google
#
# Needs: pip install botasaurus  (already present via the supercli botasaurus-cli).
import sys, contextlib, urllib.parse
from botasaurus.browser import browser, Driver

query = sys.argv[1] if len(sys.argv) > 1 else None
if not query:
    sys.stderr.write('usage: google-botasaurus.py "<query>"\n')
    sys.exit(2)

url = ("https://www.google.com/search?q="
       + urllib.parse.quote(query) + "&num=10&hl=en&gl=us")


@browser(headless=True, block_images=True, output=None, close_on_crash=True)
def fetch(driver: Driver, data):
    driver.get(url)
    # Dismiss a consent dialog if one renders.
    try:
        driver.run_js(
            "var b=document.querySelector('button[aria-label=\"Accept all\"],#L2AGLb');"
            "if(b){b.click();}")
        driver.sleep(1)
    except Exception:
        pass
    return driver.page_html


# Keep stdout clean (Botasaurus logs to it) — only the HTML goes to real stdout.
real_stdout = sys.stdout
with contextlib.redirect_stdout(sys.stderr):
    html = fetch()
real_stdout.write(html or "")
