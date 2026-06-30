#!/usr/bin/env bash
# Authed LinkedIn fetcher → rendered HTML on stdout, for:
#   ./open-serpapi parse --engine linkedin
# Needs your li_at session cookie in $LI_AT or ~/.config/intrane-gtm/li_at.
#   fetchers/linkedin.sh content "staff augmentation Grenoble"
#   fetchers/linkedin.sh url "https://www.linkedin.com/posts/<...>"
set -euo pipefail
KIND="${1:?usage: linkedin.sh <content|people|company|url> \"<query-or-url>\"}"
ARG="${2:?missing query/url}"
exec python3 "$(dirname "$0")/linkedin-botasaurus.py" "$KIND" "$ARG"
