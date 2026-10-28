#!/usr/bin/env bash
# Build the cancho-ui version of the home page into _site/next/, beside the live page.
#
# The page is written in cancho-ui (docs/www-port/ in alpibrusl/cancho-ui) and compiled with
# `cancho-ui build --page`. It is a preview: robots.txt keeps crawlers out of /next/ and the page's
# canonical link names the live page. Run scripts/build_site.sh first (it creates _site/).
#
# CANCHO_UI_REV pins the cancho-ui commit, so a build is the same build every time. Change it on
# purpose, in a pull request, when the port changes.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"

CANCHO_UI_REV="${CANCHO_UI_REV:-ada7200ec75cc7412aafb802f0e8537970435ddd}"
[ -d _site ] || { echo "_site/ is missing: run scripts/build_site.sh first" >&2; exit 1; }

WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
git clone --quiet https://github.com/alpibrusl/cancho-ui "$WORK/cancho-ui"
git -C "$WORK/cancho-ui" checkout --quiet "$CANCHO_UI_REV"
(cd "$WORK/cancho-ui" && cargo build --quiet --release -p cancho-ui)

"$WORK/cancho-ui/target/release/cancho-ui" build "$WORK/cancho-ui/docs/www-port/site/home.cui" --page -o "$WORK/out"

# The preview must work under /next/: nothing may point at the root of the host.
if grep -Eq '(href|src|srcset|poster)="/[^/]' "$WORK/out/index.html"; then
  echo "the built index.html has a root-relative URL; it would not work under /next/" >&2
  exit 1
fi

# Only a finished, checked build is put in place: a failure above leaves _site/ as it was.
rm -rf _site/next
mv "$WORK/out" _site/next

# The port carries its own copy of the data, taken from a given cancho-www commit. Say so when the
# live data has moved on; this is a warning, not a failure, so a data change is never blocked by it.
if ! cmp -s data/ecosystem.json "$WORK/cancho-ui/docs/www-port/site/data/ecosystem.json"; then
  echo "warning: data/ecosystem.json differs from the copy the preview was built with; /next/ is out of date until the port is synced (see docs/www-port/status.md in cancho-ui)" >&2
fi
echo "built _site/next/ ($(find _site/next -type f | wc -l | tr -d ' ') files, cancho-ui $CANCHO_UI_REV)"
