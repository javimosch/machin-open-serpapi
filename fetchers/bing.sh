#!/usr/bin/env bash
# Fetcher plugin (layer 1): bing -> rendered Bing SERP HTML on stdout, for:
#   ./open-serpapi parse --engine bing
set -euo pipefail
QUERY="${1:?usage: bing.sh \"<query>\"}"
DIR="$(dirname "$0")"
ENC=$(python3 -c 'import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))' "$QUERY")
exec python3 "$DIR/render-botasaurus.py" "https://www.bing.com/search?q=$ENC&setlang=en&cc=US"
