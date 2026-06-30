#!/usr/bin/env python3
# Generic layer-1 renderer:  render-botasaurus.py <url>  ->  rendered HTML stdout
#
# Anti-detect, humanized Chrome (Botasaurus). Bypasses the bot/CAPTCHA walls
# that curl and naive headless browsers hit (Google, DuckDuckGo, ...). Engine
# fetcher scripts build the URL and pipe this into the right parser.
#
# Needs: pip install botasaurus  (present via the supercli botasaurus-cli).
import sys, contextlib
from botasaurus.browser import browser, Driver

url = sys.argv[1] if len(sys.argv) > 1 else None
if not url:
    sys.stderr.write("usage: render-botasaurus.py <url>\n")
    sys.exit(2)


@browser(headless=True, block_images=True, output=None, close_on_crash=True)
def fetch(driver: Driver, data):
    driver.get(url)
    driver.sleep(1)
    return driver.page_html


real_stdout = sys.stdout
with contextlib.redirect_stdout(sys.stderr):
    html = fetch()
real_stdout.write(html or "")
