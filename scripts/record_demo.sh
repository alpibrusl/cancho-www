#!/usr/bin/env bash
# Records the demo on the front page (index.html): a real terminal session of cancho refusing a program that leaks a
# file handle, accepting the one-line fix, running it, printing what it may do, and building it again with the compiler
# written in cancho. Every command is run for real and its output is what is recorded; only the typing is simulated (a
# fixed delay per character), so the recording does not depend on who is at the keyboard.
#
#     scripts/record_demo.sh <path-to-the-cancho-binary>
#
# The binary must be built from a checkout of https://github.com/alpibrusl/cancho (`--compiler auto` builds the compiler
# in cancho from that checkout's `examples/selfhost`). Writes demo/demo.cast (asciicast v2), demo.mp4, demo.webm and
# poster.png. Needs asciinema, agg and ffmpeg. Run it again after a change to what the commands print, and commit the
# result: the page shows what was recorded.
set -euo pipefail

here=$(cd "$(dirname "$0")/.." && pwd)
cancho=$(cd "$(dirname "${1:?usage: record_demo.sh <path-to-the-cancho-binary>}")" && pwd)/$(basename "$1")
out="$here/demo"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

cp "$out/src/leak.cho" "$out/src/fixed.cho" "$work/"
mkdir "$work/bin"
ln -s "$cancho" "$work/bin/cancho"
export CANCHO_CACHE="$work/cache"
echo "some notes" > /tmp/notes.txt

# The first `--compiler auto` builds the compiler written in cancho (about a minute); do it before recording.
(cd "$work" && PATH="$work/bin:$PATH" cancho build fixed.cho --std --compiler auto -o warm >/dev/null)

cat > "$work/session.sh" <<'SESSION'
export TERM=xterm-256color
cd "$WORK"
export PATH="$WORK/bin:$PATH"
green=$'\033[32m'; dim=$'\033[2m'; off=$'\033[0m'
typed() {  # typed <text>: the text, a character at a time
  local s=$1 i
  for ((i = 0; i < ${#s}; i++)); do printf '%s' "${s:i:1}"; sleep 0.045; done
}
note() { printf '%s' "$dim"; typed "# $1"; printf '%s\n' "$off"; sleep 0.8; }
run() {    # run <pause-after> <command>: typed, then run for real
  printf '%s$%s ' "$green" "$off"; typed "$2"; sleep 0.5; printf '\n'
  bash -c "$2" || true
  sleep "$1"
}
clear
note "A program that opens a file."
run 3.5 'cat leak.cho'
note "It never closes it. The compiler refuses, and says which rule:"
run 3.5 'cancho check leak.cho --std'
run 3 'cancho check leak.cho --std --output json | grep -E "\"(rule|message)\""'
note "One line fixes it."
run 2.5 'diff leak.cho fixed.cho'
run 2 'cancho build fixed.cho --std -o notes && ./notes'
note "What may it do? The compiler can say, because authority is in the types."
run 5 'cancho authority fixed.cho --std'
note "And the compiler can be one written in cancho:"
run 2.5 'cancho build fixed.cho --std --compiler auto -o notes2 && ./notes2'
sleep 1.5
SESSION

WORK="$work" asciinema rec --overwrite --quiet --cols 96 --rows 34 --command "bash $work/session.sh" "$out/demo.cast"
agg --theme monokai --font-size 16 "$out/demo.cast" "$work/demo.gif" >/dev/null 2>&1
ffmpeg -y -loglevel error -i "$work/demo.gif" -movflags +faststart -pix_fmt yuv420p \
  -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -c:v libx264 -crf 26 "$out/demo.mp4"
ffmpeg -y -loglevel error -i "$work/demo.gif" -c:v libvpx-vp9 -crf 38 -b:v 0 -pix_fmt yuv420p "$out/demo.webm" || rm -f "$out/demo.webm"
# The poster is the moment the compiler refuses (about 22 s in), so a page that has not loaded the video still shows the point.
ffmpeg -y -loglevel error -ss 22 -i "$out/demo.mp4" -frames:v 1 "$out/poster.png"
ls -l "$out"/demo.* "$out/poster.png"
