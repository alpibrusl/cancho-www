#!/usr/bin/env bash
# Assemble the deployable static site into _site/.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"
rm -rf _site && mkdir -p _site
cp index.html llms.txt robots.txt logo.png logo-mark.png _site/
mkdir -p _site/demo && cp demo/demo.mp4 demo/demo.webm demo/poster.png demo/demo.cast _site/demo/
echo "built _site/ ($(find _site -type f | wc -l | tr -d ' ') files)"
