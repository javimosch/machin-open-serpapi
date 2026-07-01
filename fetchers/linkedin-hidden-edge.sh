#!/usr/bin/env bash
# Start a HIDDEN, authed Edge on a virtual display (Xvfb) for LinkedIn automation.
# Same headful behavior as your visible Edge (clipboard / interaction / anti-bot all
# work), but no window and NO focus stealing on your real display. Injects your
# LinkedIn session cookies (refreshed from the visible Edge on :9222 if running,
# else from ~/.config/intrane-gtm/li-cookies.json). Exposes CDP on :9223.
#
# Then run the fetchers against it, e.g.:
#   CDP_URL=http://localhost:9223 ./fetchers/linkedin-search-threads.sh "CTO de transition" 3
set -uo pipefail
DISP="${XVFB_DISPLAY:-:99}"
PORT="${HIDDEN_CDP_PORT:-9223}"
PROFILE="${HIDDEN_PROFILE:-/tmp/edge-auto}"
COOKIES="$HOME/.config/intrane-gtm/li-cookies.json"
mkdir -p "$(dirname "$COOKIES")"

# 1. virtual display
if ! xdpyinfo -display "$DISP" >/dev/null 2>&1; then
  Xvfb "$DISP" -screen 0 1920x1080x24 >/tmp/xvfb.log 2>&1 &
  sleep 2
fi

# 2. refresh cookies from the visible Edge (:9222) if it's up — raw CDP
#    Storage.getCookies (captures httpOnly cookies like li_at, which Playwright's
#    context.cookies() drops).
if curl -sf http://localhost:9222/json/version >/dev/null 2>&1; then
  python3 - "$COOKIES" <<'PY'
from playwright.sync_api import sync_playwright
import json, sys
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://localhost:9222")
    ck = b.new_browser_cdp_session().send("Storage.getCookies")["cookies"]
    li = [c for c in ck if 'linkedin' in (c.get('domain') or '')]
    json.dump(li, open(sys.argv[1], 'w'))
    print("refreshed", len(li), "cookies (li_at:", any(c['name'] == 'li_at' for c in li), ")")
PY
  chmod 600 "$COOKIES"
fi

# 3. launch the hidden Edge if not already up
if ! curl -sf "http://localhost:$PORT/json/version" >/dev/null 2>&1; then
  DISPLAY="$DISP" setsid microsoft-edge --remote-debugging-port="$PORT" \
    --user-data-dir="$PROFILE" --no-first-run --no-default-browser-check --no-sandbox \
    >/tmp/edge-hidden.log 2>&1 < /dev/null &
  sleep 5
fi

# 4. inject the cookies into the hidden Edge — raw CDP Storage.setCookies
#    (sets httpOnly + sameSite=None cookies verbatim, which add_cookies can't).
python3 - "$PORT" "$COOKIES" <<'PY'
from playwright.sync_api import sync_playwright
import json, sys
port, cf = sys.argv[1], sys.argv[2]
cks = json.load(open(cf))
def cdp(c):
    d = {"name": c["name"], "value": c["value"], "domain": c["domain"], "path": c.get("path", "/"),
         "secure": bool(c.get("secure", False)), "httpOnly": bool(c.get("httpOnly", False))}
    if c.get("sameSite") in ("Strict", "Lax", "None"): d["sameSite"] = c["sameSite"]
    if isinstance(c.get("expires"), (int, float)) and c["expires"] > 0: d["expires"] = c["expires"]
    return d
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(f"http://localhost:{port}")
    b.new_browser_cdp_session().send("Storage.setCookies", {"cookies": [cdp(c) for c in cks]})
    print("injected", len(cks), "cookies (li_at:", any(c['name'] == 'li_at' for c in cks), ")")
PY
echo "hidden Edge ready — CDP_URL=http://localhost:$PORT (display $DISP, invisible)"
