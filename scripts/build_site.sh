#!/usr/bin/env bash
# Assemble the deployable static site into _site/:
#
#   /          the home page written in cancho-ui (docs/www-port/ in alpibrusl/cancho-ui), built by
#              `cancho-ui build docs/www-port/site/home.cui --page` at the commit named in CANCHO_UI_REV
#   /classic/  the previous hand-written page (index.html + assets/), unchanged: the rollback
#   /next/     a redirect to /, for the preview URL that was published before the switch
#
# CANCHO_UI_REV pins the cancho-ui commit, so a build is the same build every time. Change it on
# purpose, in a pull request, when the port changes.
#
# Only a finished, checked build is put in place: everything is assembled in a temporary directory,
# checked (scripts/check_site.py), and only then does it replace _site/. Any failure leaves _site/ as it was.
#
# Environment:
#   CANCHO_UI_REV  the commit to build (default: the pin below)
#   CANCHO_UI_DIR  a cancho-ui checkout to use instead of cloning; it must be at CANCHO_UI_REV
#                  (set CARGO_TARGET_DIR to reuse an existing build directory)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"

CANCHO_UI_REV="${CANCHO_UI_REV:-b974c492bdffc4d7fa3f32479b6f267f111bca97}"

WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
fail() { echo "build_site: $*" >&2; exit 1; }

python3 scripts/gen_agent_files.py

# 1. The classic page, as it has always been assembled: every URL in it is relative, so it works under /classic/ as is.
C="$WORK/classic"
mkdir -p "$C/demo" "$C/data"
cp index.html og.png agents.md llms.txt llms-full.txt robots.txt logo.png logo-mark.png "$C/"
cp -r assets "$C/assets"
cp data/ecosystem.json data/demos.json "$C/data/"
cp demo/demo.mp4 demo/demo.webm demo/poster.png demo/demo.cast "$C/demo/"

# 2. The cancho-ui source at the pinned commit, and the binary.
if [ -n "${CANCHO_UI_DIR:-}" ]; then
  UI="$CANCHO_UI_DIR"
  [ "$(git -C "$UI" rev-parse HEAD)" = "$CANCHO_UI_REV" ] || fail "$UI is not at $CANCHO_UI_REV"
else
  UI="$WORK/cancho-ui"
  git clone --quiet https://github.com/alpibrusl/cancho-ui "$UI"
  git -C "$UI" checkout --quiet "$CANCHO_UI_REV"
fi
PORT_DATA="$UI/docs/www-port/site/data/ecosystem.json"

# 3. The live page must not go stale. The port carries its own copy of the data (docs/www-port/site/data/, from a
#    given cancho-www commit); when data/ecosystem.json has moved on, the build fails until the copy is synced in
#    cancho-ui and CANCHO_UI_REV is moved (docs/www-port/status.md in cancho-ui).
cmp -s data/ecosystem.json "$PORT_DATA" || fail "data/ecosystem.json differs from the copy in cancho-ui $CANCHO_UI_REV (docs/www-port/site/data/ecosystem.json). The page at / would show stale data. Sync the copy (and agents.md, llms.txt, llms-full.txt, and the hash in home.cui) in a cancho-ui pull request, then move CANCHO_UI_REV here."

(cd "$UI" && cargo build --quiet --release -p cancho-ui)
BIN="${CARGO_TARGET_DIR:-$UI/target}/release/cancho-ui"
"$BIN" build "$UI/docs/www-port/site/home.cui" --page -o "$WORK/root"

# 4. What the old site served at the root and the port does not carry stays served at the same URL.
echo "cancho.dev" > "$WORK/root/CNAME"
cp robots.txt "$WORK/root/robots.txt"
mkdir -p "$WORK/root/data" "$WORK/root/assets/fonts"
cp data/demos.json "$WORK/root/data/demos.json"
cp assets/fonts/OFL-*.txt "$WORK/root/assets/fonts/"

# 5. The tree: root, /classic/ (without the two files that only mean something at the root) and /next/.
mv "$WORK/root" "$WORK/site"
rm -f "$C/robots.txt"
mv "$C" "$WORK/site/classic"
mkdir "$WORK/site/next"
cat > "$WORK/site/next/index.html" <<'HTML'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>cancho</title>
<meta http-equiv="refresh" content="0; url=../">
<link rel="canonical" href="https://cancho.dev/">
<meta name="robots" content="noindex">
</head>
<body>
<p>The preview that was here is now the home page: <a href="../">cancho.dev</a>.</p>
</body>
</html>
HTML

# 6. Check it; a failure leaves _site/ as it was.
python3 scripts/check_site.py "$WORK/site" || fail "the built tree failed scripts/check_site.py; _site/ is unchanged"

rm -rf _site
mv "$WORK/site" _site
echo "built _site/ ($(find _site -type f | wc -l | tr -d ' ') files; cancho-ui $CANCHO_UI_REV)"
