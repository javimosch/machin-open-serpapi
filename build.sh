#!/usr/bin/env bash
# Build open-serpapi: mint canonical .mfl from .src, then compile to a native binary.
# Point at a local machin build with MACHIN=/path/to/machin ./build.sh
set -euo pipefail
cd "$(dirname "$0")"
MACHIN="${MACHIN:-machin}"
mkdir -p build
"$MACHIN" encode src/serpapi.src src/css.src > build/serpapi.mfl
"$MACHIN" build build/serpapi.mfl -o open-serpapi
echo "built ./open-serpapi"
