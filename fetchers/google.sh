#!/usr/bin/env bash
# Default fetcher for engine=google: Botasaurus anti-detect browser.
# Bypasses the CAPTCHA wall that curl + plain headless Chrome hit. Emits
# rendered SERP HTML on stdout for: ./open-serpapi parse --engine google
set -euo pipefail
QUERY="${1:?usage: google.sh \"<query>\"}"
exec python3 "$(dirname "$0")/google-botasaurus.py" "$QUERY"
