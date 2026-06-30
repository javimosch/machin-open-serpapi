#!/usr/bin/env bash
# Keyword -> posts+comments for LinkedIn (closes the keyword→comments chain).
# Needs your browser on CDP (see ../skills/linkedin.md). ToS: personal, low-volume.
#   linkedin-search-threads.sh "<keywords>" [limit]
set -euo pipefail
exec python3 "$(dirname "$0")/linkedin-search-threads.py" "$@"
