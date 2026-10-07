#!/usr/bin/env bash
# Assemble the deployable static site into _site/.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"
rm -rf _site && mkdir -p _site
cp index.html llms.txt robots.txt logo.png _site/
echo "built _site/ ($(find _site -type f | wc -l | tr -d ' ') files)"
