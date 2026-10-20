#!/usr/bin/env bash
# Sets the GitHub "About" description of the cancho-* repositories that have none (2026-10-20).
# The text comes from each repository's own README. Run it once, logged in with `gh auth login` as someone who can
# edit those repositories:   bash scripts/github_about.sh
set -euo pipefail
about() { gh repo edit "alpibrusl/$1" --description "$2"; echo "described $1"; }

about cancho-ui "A UI language whose compiler knows what each component is allowed to do: a component declares the authority it needs, and the program is refused when the declaration and the code disagree. Builds JavaScript and DOM."
about cancho-code "An AI coding assistant that proves its work: the cancho compiler checks every piece the model writes, and a task is done only when the compiler and the task's own examples say so."
about cancho-forge "An agent-run software company you can audit: state, budgets, approvals and evidence are kept by the runtime, and a worker cannot accept its own work. Written in cancho."
about cancho-hdl "One file for the software/hardware boundary: a .chw contract is checked, and a C header, device tree, SystemVerilog register RTL and CMSIS-SVD are generated from it."
about cancho-client-gen "Typed clients generated from the OpenAPI 3.1 document that cancho-web produces: the contract, both ways. Written in cancho."
about cancho-fetch "An agent-safe fetch: HTTP and HTTPS to a fixed, built-in list of hosts, listed in the binary's authority row instead of a flag. Written in cancho. Design only."
about cancho-mqtt-client "An MQTT 3.1.1 client library for cancho, written in cancho: connect, publish, subscribe, will, QoS 0 and 1, reconnect with bounded backoff. Design only."

# Optional: the repositories whose landing page is not yet set as the repository's website (shown under About on GitHub).
# Uncomment to set them.
# for r in ui cache gateway mqtt dns web ml gpu code forge hdl; do gh repo edit "alpibrusl/cancho-$r" --homepage "https://alpibrusl.github.io/cancho-$r/"; done
