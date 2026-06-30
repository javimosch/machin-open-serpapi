#!/usr/bin/env bash
# Offline, deterministic parser tests: run every saved raw fixture through the
# parser and diff (order-insensitively, via `jq -S`) against its golden JSON.
# No network, no fetcher, no proxy — fixtures are frozen raw bytes.
#
# Refresh a golden after an intentional schema change:
#   ./open-serpapi parse --engine <engine> < fixtures/<engine>/<name>.raw.json \
#     | jq . > golden/<engine>/<name>.json
set -euo pipefail
cd "$(dirname "$0")"
[ -x ./open-serpapi ] || ./build.sh
pass=0; fail=0
for raw in fixtures/*/*.raw.*; do
  engine=$(basename "$(dirname "$raw")")
  name=$(basename "$raw"); name=${name%.raw.*}
  golden="golden/$engine/$name.json"
  got=$(./open-serpapi parse --engine "$engine" < "$raw")
  if diff <(jq -S . "$golden") <(printf '%s' "$got" | jq -S .) >/dev/null 2>&1; then
    echo "PASS  $engine/$name"; pass=$((pass+1))
  else
    echo "FAIL  $engine/$name"
    diff <(jq -S . "$golden") <(printf '%s' "$got" | jq -S .) | head -20 || true
    fail=$((fail+1))
  fi
done
echo "---"
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
