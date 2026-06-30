#!/usr/bin/env python3
# Authed LinkedIn fetcher (layer 1) for open-serpapi's `linkedin` engine.
#
# Renders LOGGED-IN LinkedIn with YOUR li_at session cookie, scrolls to load
# lazy content, expands "see more" text and comment threads, and dumps the
# rendered HTML to stdout for: ./open-serpapi parse --engine linkedin
#
#   fetchers/linkedin.sh content "staff augmentation Grenoble"   # post search
#   fetchers/linkedin.sh url "https://www.linkedin.com/posts/...." # a post + comments
#
# ⚠️  ToS / RISK: scraping logged-in LinkedIn violates their User Agreement and
# can get your account restricted. Personal, low-volume, self-host research only
# — your account, your call. The cookie never leaves your machine and is never
# committed (read from $LI_AT or ~/.config/intrane-gtm/li_at, chmod 600).
import os, sys, urllib.parse, contextlib
from botasaurus.browser import browser, Driver


def read_cookie():
    v = os.environ.get("LI_AT", "").strip()
    if v:
        return v
    p = os.path.expanduser("~/.config/intrane-gtm/li_at")
    if os.path.exists(p):
        return open(p).read().strip()
    sys.stderr.write("No li_at cookie: set $LI_AT or write ~/.config/intrane-gtm/li_at\n")
    sys.exit(3)


KIND = sys.argv[1] if len(sys.argv) > 1 else "content"
ARG = sys.argv[2] if len(sys.argv) > 2 else ""
LI_AT = read_cookie()


def build_url(kind, arg):
    if kind == "url" or arg.startswith("http"):
        return arg
    q = urllib.parse.quote(arg)
    base = "https://www.linkedin.com/search/results"
    return {
        "content": f"{base}/content/?keywords={q}&origin=GLOBAL_SEARCH_HEADER",
        "people":  f"{base}/people/?keywords={q}",
        "company": f"{base}/companies/?keywords={q}",
    }.get(kind, f"{base}/content/?keywords={q}")


URL = build_url(KIND, ARG)

# Click every "see more" / "load more comments" style button (FR + EN).
EXPAND_JS = r"""
let n=0;
document.querySelectorAll('button').forEach(b=>{
  const t=((b.innerText||'')+' '+(b.getAttribute('aria-label')||'')).toLowerCase();
  if(/more comment|load more|see more|…\s*more|plus de commentaire|charger|voir plus|afficher plus|afficher les|réponse|reply/.test(t)){
    try{b.click();n++;}catch(e){}
  }
});
return n;
"""


@browser(headless=True, block_images=True, output=None, close_on_crash=True)
def fetch(driver: Driver, data):
    driver.get("https://www.linkedin.com")
    driver.add_cookies([{
        "name": "li_at", "value": LI_AT, "domain": ".linkedin.com",
        "path": "/", "secure": True, "httpOnly": True,
    }])
    driver.get(URL)
    driver.sleep(3)
    for _ in range(6):
        try:
            driver.run_js("window.scrollTo(0, document.body.scrollHeight)")
        except Exception:
            pass
        driver.sleep(2)
        try:
            driver.run_js(EXPAND_JS)
        except Exception:
            pass
        driver.sleep(1)
    html = driver.page_html
    low = (html or "").lower()
    if "authwall" in low or ("sign in" in low and "global-nav" not in low):
        sys.stderr.write("WARNING: looks like a login wall — is the li_at cookie valid/fresh?\n")
    return html


real_stdout = sys.stdout
with contextlib.redirect_stdout(sys.stderr):
    html = fetch()
real_stdout.write(html or "")
