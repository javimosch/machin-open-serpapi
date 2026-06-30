#!/usr/bin/env python3
# Close the keyword -> comments chain for LinkedIn, human-like.
#
#   linkedin-search-threads.py "<keywords>" [limit]
#
# In YOUR logged-in browser (CDP), for each rendered search result we mimic a
# human: open the post's "⋯" menu, click "Copy link to post" (→ clipboard), pause
# a few seconds, then open that exact link in a new tab, let comments load, and
# parse it through `open-serpapi --engine linkedin`. Using the real copied URL
# (not a reconstructed one) avoids "this post can't be shown", and the pacing
# avoids non-human-activity detection.
#
# Emits: { search_parameters:{q}, post_count, posts:[ {post + comments[]} ] }.
# Needs the browser on CDP (see skills/linkedin.md). ToS: personal, low-volume.
import os, re, sys, json, time, random, subprocess, urllib.parse
from playwright.sync_api import sync_playwright

KEYWORDS = sys.argv[1] if len(sys.argv) > 1 else ""
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 3
if not KEYWORDS:
    sys.stderr.write('usage: linkedin-search-threads.py "<keywords>" [limit]\n'); sys.exit(2)

CDP = os.environ.get("CDP_URL", "http://localhost:9222")
HERE = os.path.dirname(os.path.abspath(__file__))
OSAPI = os.environ.get("OSAPI", os.path.join(HERE, "..", "open-serpapi"))
SEARCH = ("https://www.linkedin.com/search/results/content/?keywords="
          + urllib.parse.quote(KEYWORDS) + "&origin=GLOBAL_SEARCH_HEADER")
MENU_SEL = ('button[aria-label*="publicación de"], button[aria-label*="post by"], '
            'button[aria-label*="publication de"], button[aria-label*="Beitrag von"]')
COPY_SEL = ('div[role="menuitem"]:has-text("enlace"), div[role="menuitem"]:has-text("lien"), '
            'div[role="menuitem"]:has-text("link"), :text("Copiar enlace"), :text("Copy link")')

REVEAL_JS = r"""() => { let n=0;
  document.querySelectorAll('button,a').forEach(b=>{ const t=((b.innerText||'')+' '+(b.getAttribute('aria-label')||'')).toLowerCase();
    if(/\d+\s*(comment|commentaire|comentario)/.test(t)||/load more comment|more comment|voir plus de comment|plus de commentaire|cargar más|ver más comentario|más comentario|show more repl|more repl|ver respuesta|mostrar.*respuesta/.test(t)||/…\s*more|see more|voir plus|ver más|mostrar más/.test(t)){try{b.click();n++}catch(e){}} });
  return n; }"""


def log(m): sys.stderr.write(m + "\n")
def nap(a, b): time.sleep(random.uniform(a, b))


def parse_linkedin(html):
    r = subprocess.run([OSAPI, "parse", "--engine", "linkedin"], input=html,
                       capture_output=True, text=True)
    try: return json.loads(r.stdout)
    except Exception: return {"posts": []}


with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP)
    ctx = browser.contexts[0]
    try:
        ctx.grant_permissions(["clipboard-read", "clipboard-write"], origin="https://www.linkedin.com")
    except Exception:
        pass

    sp = ctx.new_page()
    sp.goto(SEARCH, wait_until="domcontentloaded", timeout=60000)
    try:
        sp.wait_for_selector('[data-testid="expandable-text-box"]', timeout=20000)
    except Exception:
        pass
    nap(1.5, 2.5)
    for _ in range(3):                              # load enough result cards
        if sp.locator(MENU_SEL).count() >= LIMIT:
            break
        sp.mouse.wheel(0, random.randint(15000, 22000)); nap(1.2, 2.0)

    menus = sp.locator(MENU_SEL)
    cnt = menus.count()
    log(f"{cnt} result cards; collecting up to {LIMIT} threads")

    posts = []
    seen = set()
    for i in range(cnt):
        if len(posts) >= LIMIT:
            break
        url = ""
        try:
            menus.nth(i).scroll_into_view_if_needed(timeout=4000)
            nap(0.6, 1.4)
            menus.nth(i).click(timeout=6000)             # open ⋯ menu
            nap(0.7, 1.3)
            sp.locator(COPY_SEL).first.click(timeout=5000)  # "Copy link to post"
            nap(0.4, 0.8)
            url = sp.evaluate("() => navigator.clipboard.readText()") or ""
        except Exception:
            try: sp.keyboard.press("Escape")
            except Exception: pass
            continue

        if "linkedin.com" not in url or url in seen:
            continue
        seen.add(url)

        nap(3.0, 5.0)                                 # human pause before opening
        tab = ctx.new_page()
        try:
            tab.goto(url, wait_until="domcontentloaded", timeout=60000)
            try:
                tab.wait_for_selector(".update-components-text", timeout=15000)
            except Exception:
                pass
            for _ in range(6):                        # scroll naturally to load comments
                tab.mouse.wheel(0, random.randint(1500, 3200)); nap(1.0, 1.8)
                try: tab.evaluate(REVEAL_JS)
                except Exception: pass
            parsed = parse_linkedin(tab.content())
            if parsed.get("posts"):
                post = parsed["posts"][0]
                post["url"] = url
                posts.append(post)
                log(f"  ✓ {post.get('author','?')}: {post.get('comment_count',0)} comments")
            else:
                log(f"  – no post parsed from {url[:70]}")
        except Exception as e:
            log(f"  – error on {url[:60]}: {str(e)[:60]}")
        finally:
            try: tab.close()
            except Exception: pass
        nap(1.0, 2.0)

    sp.close()

out = {
    "search_metadata": {"status": "Success", "engine": "linkedin"},
    "search_parameters": {"engine": "linkedin", "type": "content_threads", "q": KEYWORDS},
    "post_count": len(posts),
    "posts": posts,
}
sys.stdout.write(json.dumps(out, ensure_ascii=False))
