#!/usr/bin/env bash
# Fetcher plugin (layer 1): brave -> rendered SERP HTML on stdout, for:
#   ./open-serpapi parse --engine brave
set -euo pipefail
QUERY="${1:?usage: brave.sh \"<query>\"}"
DIR="$(dirname "$0")"
ENC=$(python3 -c 'import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))' "$QUERY")
exec python3 "$DIR/render-botasaurus.py" "https://search.brave.com/search?q=$ENC"
