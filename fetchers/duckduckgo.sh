#!/usr/bin/env bash
# Fetcher plugin (layer 1): duckduckgo -> DDG html-endpoint markup on stdout.
# DDG anomaly-blocks datacenter IPs, so we render via the anti-detect browser.
# From a clean residential IP, plain curl on this endpoint also works:
#   curl -sL -A '<UA>' --data-urlencode "q=$QUERY" https://html.duckduckgo.com/html/
set -euo pipefail
QUERY="${1:?usage: duckduckgo.sh \"<query>\"}"
DIR="$(dirname "$0")"
ENC=$(python3 -c 'import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))' "$QUERY")
exec python3 "$DIR/render-botasaurus.py" "https://html.duckduckgo.com/html/?q=$ENC"
