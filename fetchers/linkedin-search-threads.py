#!/usr/bin/env python3
# Close the keyword -> comments chain for LinkedIn.
#
#   linkedin-search-threads.py "<keywords>" [limit]
#
# 1. CDP-search the keyword in YOUR logged-in browser; capture each post's
#    activity URN from the search API responses (LinkedIn keeps URNs out of the
#    DOM, but they're in the Voyager JSON).
# 2. For each URN, open the post-detail page (/feed/update/<urn>/), load its
#    comments, and parse it through `open-serpapi --engine linkedin`.
# 3. Emit one combined JSON: { search_parameters:{q}, posts:[ {post + comments} ] }.
#
# Needs the browser on CDP (see skills/linkedin.md). ToS: your session, personal,
# low-volume only.
import os, re, sys, json, subprocess
from playwright.sync_api import sync_playwright

KEYWORDS = sys.argv[1] if len(sys.argv) > 1 else ""
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 3
if not KEYWORDS:
    sys.stderr.write('usage: linkedin-search-threads.py "<keywords>" [limit]\n'); sys.exit(2)

CDP = os.environ.get("CDP_URL", "http://localhost:9222")
HERE = os.path.dirname(os.path.abspath(__file__))
OSAPI = os.environ.get("OSAPI", os.path.join(HERE, "..", "open-serpapi"))

import urllib.parse
SEARCH = ("https://www.linkedin.com/search/results/content/?keywords="
          + urllib.parse.quote(KEYWORDS) + "&origin=GLOBAL_SEARCH_HEADER")

REVEAL_JS = r"""() => { let n=0;
  document.querySelectorAll('button,a').forEach(b=>{ const t=((b.innerText||'')+' '+(b.getAttribute('aria-label')||'')).toLowerCase();
    if(/\d+\s*(comment|commentaire|comentario)/.test(t)||/load more comment|more comment|voir plus de comment|plus de commentaire|cargar más|ver más comentario|más comentario|show more repl|more repl|ver respuesta|mostrar.*respuesta/.test(t)||/…\s*more|see more|voir plus|ver más|mostrar más/.test(t)){try{b.click();n++}catch(e){}} });
  return n; }"""


def log(m): sys.stderr.write(m + "\n")


def parse_linkedin(html):
    r = subprocess.run([OSAPI, "parse", "--engine", "linkedin"],
                       input=html, capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"posts": []}


with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP)
    ctx = browser.contexts[0]

    # --- 1. search + capture URNs from the API responses ---
    urns = []
    def on_resp(resp):
        u = resp.url
        if any(k in u for k in ("voyager", "graphql", "/api/")):
            try:
                for m in re.findall(r"urn:li:activity:\d+", resp.text()):
                    if m not in urns:
                        urns.append(m)
            except Exception:
                pass
    sp = ctx.new_page()
    sp.on("response", on_resp)
    sp.goto(SEARCH, wait_until="domcontentloaded", timeout=60000)
    try:
        sp.wait_for_selector('[data-testid="expandable-text-box"]', timeout=20000)
    except Exception:
        pass
    for _ in range(3):                       # scroll to pull more result pages
        sp.mouse.wheel(0, 25000); sp.wait_for_timeout(1800)
        if len(urns) >= LIMIT * 2:
            break
    sp.close()
    log(f"captured {len(urns)} URNs; fetching {min(LIMIT, len(urns))} threads")

    # --- 2+3. per-URN detail page -> parse post + comments ---
    posts = []
    for urn in urns[:LIMIT]:
        url = f"https://www.linkedin.com/feed/update/{urn}/"
        dp = ctx.new_page()
        try:
            dp.goto(url, wait_until="domcontentloaded", timeout=60000)
            try:
                dp.wait_for_selector('.update-components-text', timeout=15000)
            except Exception:
                pass
            for _ in range(8):
                dp.mouse.wheel(0, 30000); dp.wait_for_timeout(1200)
                try: dp.evaluate(REVEAL_JS)
                except Exception: pass
                dp.wait_for_timeout(900)
            parsed = parse_linkedin(dp.content())
            if parsed.get("posts"):
                post = parsed["posts"][0]
                post["url"] = url
                post["urn"] = urn
                posts.append(post)
                log(f"  {urn}: {post.get('comment_count', 0)} comments")
        except Exception as e:
            log(f"  {urn}: error {str(e)[:70]}")
        finally:
            try: dp.close()
            except Exception: pass

out = {
    "search_metadata": {"status": "Success", "engine": "linkedin"},
    "search_parameters": {"engine": "linkedin", "type": "content_threads", "q": KEYWORDS},
    "post_count": len(posts),
    "posts": posts,
}
sys.stdout.write(json.dumps(out, ensure_ascii=False))
