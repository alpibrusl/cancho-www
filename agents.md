# cancho

> A native systems language in which resource ownership and authority are part of the type, and the ecosystem built with it.

Status: pre-1.0. As of 2026-10-20. Alpha products are built with it; the compiler is the Rust one, and a second compiler written in cancho is being checked against it (it does not yet refuse everything the language refuses).

## The idea

- A value is consumed exactly once. A `res` value must be consumed on every path; there are no destructors, no garbage collector, no exceptions.
- Reaching the outside world (console, file, network, foreign code) requires holding a capability for it. `split(world)` is the only source of authority, and every piece must be handed on or `release`d.
- Effect rows are exact: performing an effect you did not declare, or declaring one you do not perform, is refused.
- Every refusal has a stable rule tag (for example `linear-value-unconsumed`, `effect-not-declared`). Match on the tag, not the prose.
- Dependencies pin to content hashes. There is no version string.

## Commands

```sh
cancho check <file.cho>... [--std] [--output json]   # refuse, or say nothing
cancho build <file.cho>... [-o <output>] [--std]     # native binary
cancho run   <file.cho>... [--std]                   # build, run, exit with the program's status
cancho test  <file.cho>... [--std]                   # run every `fn test_*`; exit 4 if one failed
cancho authority <file.cho> [--std] [--output json]  # what the program may do, and what it never touches
cancho introspect                                    # the command tree, as data
cancho skill                                         # a SKILL.md, as data
```

Start here to write cancho: https://github.com/alpibrusl/cancho/blob/main/AGENTS.md
Docs: https://alpibrusl.github.io/cancho/

## Ecosystem

Stages: `working` = Does what its README claims.; `alpha` = Runs, may change, not for production.; `early` = A library with named gaps.; `built` = Code exists and is documented; its README does not name a stage.; `design` = A design, not built yet.

### Language and compiler

- [cancho](https://github.com/alpibrusl/cancho) `built`: The language and its Rust compiler. A second compiler, written in cancho, is being checked against it. Pre-1.0. Docs: https://alpibrusl.github.io/cancho/
- [cancho-ui](https://github.com/alpibrusl/cancho-ui) `built`: A UI language whose compiler knows what each component is allowed to do. Builds JavaScript and DOM. Authority: a component declares `requires Clock;`; a missing or unused declaration is refused (capability-missing, capability-unused).

### Services

- [cancho-hooks](https://github.com/alpibrusl/cancho-hooks) `alpha`: Webhook delivery: on disk before the 202, signed, retried, dead-lettered and replayable. Not for production yet. Docs: https://alpibrusl.github.io/cancho-hooks/
- [cancho-cache](https://github.com/alpibrusl/cancho-cache) `alpha`: Redis-compatible string cache over RESP2/RESP3, expiry and LRU in a fixed arena. Authority: no FFI; authority report checked in CI. 38 of Redis 7.0's commands; not a Redis replacement.
- [cancho-gateway](https://github.com/alpibrusl/cancho-gateway) `design`: An auditable HTTP/1.1 reverse proxy: a fixed upstream set proven by the authority report.
- [cancho-mqtt](https://github.com/alpibrusl/cancho-mqtt) `design`: An MQTT 3.1.1 broker: one thread, one poller, bounded memory.
- [cancho-dns](https://github.com/alpibrusl/cancho-dns) `design`: A forwarding and caching DNS resolver: bounded parser, fixed arena.
- [cancho-oci](https://github.com/alpibrusl/cancho-oci) `design`: Container images without a daemon: a deterministic OCI image builder and registry client.

### Libraries

- [cancho-pg](https://github.com/alpibrusl/cancho-pg) `early`: PostgreSQL client: v3 protocol, SCRAM-SHA-256, extended queries, TLS, non-blocking pool. Authority: network and heap only; no C or foreign calls.
- [cancho-schema](https://github.com/alpibrusl/cancho-schema) `early`: Schemas as data: validation, problem+json errors and JSON Schema 2020-12 from one value. Authority: heap only; no C.
- [cancho-web](https://github.com/alpibrusl/cancho-web) `early`: Typed routes, validated bodies, problem+json errors and an OpenAPI document from one declaration. Authority: one thread, no FFI. Rests on: cancho-schema.
- [cancho-log](https://github.com/alpibrusl/cancho-log) `early`: A durable, segmented, append-only log with crash-safe recovery that cuts off a torn tail. Authority: no FFI. Append path only; not a Kafka replacement.
- [cancho-stats](https://github.com/alpibrusl/cancho-stats) `design`: Statistics on tabular data as a command line an agent can read: exact sums, tests, intervals, resampling.
- [cancho-ml](https://github.com/alpibrusl/cancho-ml) `design`: Classical ML, pipelines and evaluation: deterministic, bounded, agent-first.

### Command-line tools for agents

- [cancho-tools](https://github.com/alpibrusl/cancho-tools) `working`: Nine small tools for agents: seek, list, peek, jsonq, tally, hash, write, replace, move. JSON out, errors that name a rule. Authority: a compiler-proven authority per binary. Docs: https://alpibrusl.github.io/cancho-tools/
- [cancho-table](https://github.com/alpibrusl/cancho-table) `built`: Select, filter, group and aggregate CSV/TSV for agents; bounded, exact, byte-stable. Rests on: cancho-tools. Docs: https://alpibrusl.github.io/cancho-table/

### Hardware and kernels

- [cancho-robot](https://github.com/alpibrusl/cancho-robot) `design`: A robot arm controller: the Feetech servo bus, SO-101 kinematics and a safety core every motion goes through. Research, design stage. Docs: https://alpibrusl.github.io/cancho-robot/
- [cancho-gpu](https://github.com/alpibrusl/cancho-gpu) `built`: A compiler for lex-gpu's .lx tile kernels to CUDA C and Metal, written in cancho. Byte-identical to lex-gpu's Rust emitter on every test case.

More, including repositories not listed here: https://github.com/orgs/alpibrusl/repositories?q=cancho-&type=public

## Measured

On macOS aarch64, 2026-10-15 (moves as the work does; https://github.com/alpibrusl/cancho/issues/491):

- 697 / 704 conformance tests pass when every build goes through the compiler written in cancho; the other 7 are known differences from the Rust compiler, each listed.
- 256 / 333 programs that must be refused are refused by the cancho compiler with the same rule as the Rust one; it does not yet check everything.
- 62 named rules, stable tags a program can match on.

Record: https://alpibrusl.github.io/cancho/bootstrap.html

## Machine-readable

- https://cancho.dev/data/ecosystem.json: every project above as JSON
- https://cancho.dev/llms.txt and https://cancho.dev/llms-full.txt
