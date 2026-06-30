#!/usr/bin/env bash
# Fetcher plugin (layer 1): startpage -> rendered SERP HTML on stdout, for:
#   ./open-serpapi parse --engine startpage
set -euo pipefail
QUERY="${1:?usage: startpage.sh \"<query>\"}"
DIR="$(dirname "$0")"
ENC=$(python3 -c 'import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))' "$QUERY")
exec python3 "$DIR/render-botasaurus.py" "https://www.startpage.com/sp/search?query=$ENC"
