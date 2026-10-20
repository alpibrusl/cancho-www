#!/usr/bin/env bash
# The text alternative to the recorded demo: the same commands as scripts/record_demo.sh, run for real, written to
# demo/transcript.txt as `$ command` followed by what it printed. scripts/gen_agent_files.py puts the file on the page.
#
#     scripts/demo_transcript.sh <path-to-the-cancho-binary>
#
# Run it again after a change to what the commands print, and commit demo/transcript.txt next to demo.cast.
set -euo pipefail

here=$(cd "$(dirname "$0")/.." && pwd)
cancho=$(cd "$(dirname "${1:?usage: demo_transcript.sh <path-to-the-cancho-binary>}")" && pwd)/$(basename "$1")
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

cp "$here/demo/src/leak.cho" "$here/demo/src/fixed.cho" "$work/"
mkdir "$work/bin"
ln -s "$cancho" "$work/bin/cancho"
echo "some notes" > /tmp/notes.txt
cd "$work"
export PATH="$work/bin:$PATH"

{
  step() {  # step <command>: the command, then its output as it was
    printf '$ %s\n' "$1"
    bash -c "$1" 2>&1 || true
  }
  echo "# A program that opens a file."
  step 'cat leak.cho'
  echo "# It never closes it. The compiler refuses, and says which rule:"
  step 'cancho check leak.cho --std'
  step 'cancho check leak.cho --std --output json | grep -E "\"(rule|message)\""'
  echo "# One line fixes it."
  step 'diff leak.cho fixed.cho'
  step 'cancho build fixed.cho --std -o notes && ./notes'
  echo "# What may it do? The compiler can say, because authority is in the types."
  step 'cancho authority fixed.cho --std'
  echo "# And the compiler can be one written in cancho:"
  step 'cancho build fixed.cho --std --compiler auto -o notes2 && ./notes2'
} > "$here/demo/transcript.txt"
echo "wrote demo/transcript.txt ($(wc -l < "$here/demo/transcript.txt") lines)"
