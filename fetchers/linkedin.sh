#!/usr/bin/env bash
# Authed LinkedIn fetcher → rendered HTML on stdout, for:
#   ./open-serpapi parse --engine linkedin
#   fetchers/linkedin.sh content "staff augmentation Grenoble"
#   fetchers/linkedin.sh url "https://www.linkedin.com/feed/update/<urn>/"
#
# Prefers attaching to YOUR real running browser over CDP (full session, no
# bot-detection / 429 / redirect loops) — start the browser with:
#   microsoft-edge --remote-debugging-port=9222 --profile-directory=Default
# Falls back to the standalone botasaurus + li_at fetcher if no debug port.
set -euo pipefail
KIND="${1:?usage: linkedin.sh <content|people|company|url|grab> [<query-or-url>]}"
ARG="${2:-}"   # not needed for 'grab' (reads your active tab)
DIR="$(dirname "$0")"
CDP="${CDP_URL:-http://localhost:9222}"
if curl -sf "$CDP/json/version" >/dev/null 2>&1; then
  exec python3 "$DIR/linkedin-cdp.py" "$KIND" "$ARG"
else
  exec python3 "$DIR/linkedin-botasaurus.py" "$KIND" "$ARG"
fi
