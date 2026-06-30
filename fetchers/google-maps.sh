#!/usr/bin/env bash
# Fetcher plugin: google_maps
#
# THE FETCHER CONTRACT (layer 1, pluggable):
#   argv[1] = query;  stdout = raw bytes that open-serpapi knows how to parse.
#   Any language, any tool. curl, Puppeteer, a cached file — all valid fetchers.
#
# This wrapper reuses the existing Puppeteer Maps scraper under ~/ai as a live
# smoke-test fetcher. It emits the raw record array open-serpapi normalizes into
# SerpApi `local_results`. For CI, prefer the saved fixtures (no network).
set -euo pipefail
QUERY="${1:?usage: google-maps.sh \"<query>\"}"
SCRAPER="${MAPS_SCRAPER:-$HOME/ai/google-maps-scraper/standalone-scraper.js}"
exec node "$SCRAPER" "$QUERY"
