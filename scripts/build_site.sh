#!/usr/bin/env bash
# Assemble the deployable static site into _site/.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"
python3 scripts/gen_agent_files.py
rm -rf _site && mkdir -p _site/demo _site/data
cp index.html og.png agents.md llms.txt llms-full.txt robots.txt logo.png logo-mark.png _site/
cp -r assets _site/assets
cp data/ecosystem.json data/demos.json _site/data/
cp demo/demo.mp4 demo/demo.webm demo/poster.png demo/demo.cast _site/demo/
# The custom domain. GitHub ignores this file for a site published by Actions; the domain itself is set in
# Settings > Pages. It is kept so the domain is written down with the build.
echo "cancho.dev" > _site/CNAME
echo "built _site/ ($(find _site -type f | wc -l | tr -d ' ') files)"
