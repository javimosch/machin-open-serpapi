#!/usr/bin/env python3
# Authed LinkedIn fetcher via CDP attach to YOUR already-running browser.
#
# Drives your real, logged-in Edge/Chrome over the Chrome DevTools Protocol —
# full valid session, real fingerprint, so LinkedIn trusts it (no cookie
# injection, no 429, no redirect loops, no PerimeterX challenge). The browser
# must be started with a debug port:
#
#   microsoft-edge --remote-debugging-port=9222 --profile-directory=Default
#
#   fetchers/linkedin.sh content "staff augmentation Grenoble"
#   fetchers/linkedin.sh url "https://www.linkedin.com/feed/update/<urn>/"
#
# ToS note unchanged: this drives YOUR session; personal, low-volume use only.
import os, sys, urllib.parse
from playwright.sync_api import sync_playwright

KIND = sys.argv[1] if len(sys.argv) > 1 else "content"
ARG = sys.argv[2] if len(sys.argv) > 2 else ""
CDP = os.environ.get("CDP_URL", "http://localhost:9222")


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

# EN + FR + ES: comment-count buttons, "load more comments", "show replies",
# and "see more" text expanders.
REVEAL_JS = r"""() => {
  let n = 0;
  document.querySelectorAll('button,a').forEach(b => {
    const t = ((b.innerText||'') + ' ' + (b.getAttribute('aria-label')||'')).toLowerCase();
    if (/\d+\s*(comment|commentaire|comentario)/.test(t) ||
        /load more comment|more comment|previous comment|voir plus de comment|plus de commentaire|charger plus|cargar más|ver más comentario|más comentario|ver comentario|mostrar más comentario/.test(t) ||
        /show more repl|more repl|voir la réponse|afficher les réponse|ver respuesta|mostrar.*respuesta|cargar.*respuesta/.test(t) ||
        /…\s*more|see more|voir plus|afficher plus|ver más|mostrar más|ver más$/.test(t)) {
      try { b.click(); n++; } catch(e) {}
    }
  });
  return n;
}"""

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP)
    ctx = browser.contexts[0] if browser.contexts else browser.new_context()

    # grab mode: attach to YOUR already-open LinkedIn tab and dump its DOM as-is
    # (you navigated + scrolled, so comments are already loaded). No navigation.
    if KIND == "grab":
        pages = [pg for c in browser.contexts for pg in c.pages]
        liked = [pg for pg in pages if "linkedin.com" in (pg.url or "")
                 and any(k in pg.url for k in ("update", "/posts/", "activity", "feed"))]
        page = (liked or [pg for pg in pages if "linkedin.com" in (pg.url or "")] or pages)[0]
        sys.stderr.write("grabbing tab: " + (page.url or "")[:90] + "\n")
        try:
            page.evaluate(REVEAL_JS)
            page.wait_for_timeout(800)
        except Exception:
            pass
        sys.stdout.write(page.content() or "")
        sys.exit(0)

    page = ctx.new_page()
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        try:
            page.wait_for_selector('[data-testid="expandable-text-box"]', timeout=20000)
        except Exception:
            pass
        # Comments lazy-load via infinite scroll on the detail page; scroll into
        # the comments region and click load-more/reveal buttons over many rounds.
        for _ in range(14):
            try:
                page.mouse.wheel(0, 30000)
            except Exception:
                pass
            page.wait_for_timeout(1500)
            try:
                page.evaluate(REVEAL_JS)
            except Exception:
                pass
            page.wait_for_timeout(1200)
        html = page.content()
    finally:
        try:
            page.close()
        except Exception:
            pass
    sys.stdout.write(html or "")
