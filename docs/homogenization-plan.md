# Homogenizing the READMEs and landing pages: the plan

Status: **plan, nothing applied beyond the first wave.** Written 2026-10-31. It follows `package-structure.md` (the standard) and `landing-pattern.md` (the page layout); the mechanism is `cancho-kit`. Marks: **[measured]** printed by a script today, **[choice]**, **[open]**.

## 1. Where things stand **[measured]**

The kit checker (`scripts/check_package_kit.py` in cancho-kit) was run over the 22 public packages other than the three done, **as if each were a tier-2 package of kind `cli`**. That is a rough yardstick, not a verdict: the kinds and tiers below are not yet assigned. The counts are problems under that yardstick.

| package | problems | README lines | landing page |
|---|---:|---:|---|
| cancho-mqtt | 1 | 216 | yes |
| cancho-tools | 2 | 244 | no |
| cancho-cache, -gpu, -hooks, -schema, -web | 4 | 187 / 188 / 110 / 260 / 444 | cache, gpu, hooks, web yes; schema no |
| cancho-client-gen, -hdl, -log | 5 | 164 / 113 / 155 | client-gen, hdl yes; log no |
| cancho-dns, -forge, -pg, -robot | 6 | 47 / 90 / 487 / 53 | dns, forge, robot yes; pg no |
| cancho-code, -diff, -fetch, -oci | 7 | 71 / 41 / 54 / 52 | code yes; the others no |
| cancho-gateway | 8 | 68 | yes |
| cancho-mqtt-client, -opt | 9 | 28 / 36 | no |
| cancho-quantum | 10 | 79 | yes |

The problems are of three kinds: sections missing (mostly *For humans, for agents*, *Compared with*, *Use it with an AI agent*, and the kind line), files missing (`AGENTS.md`, `llms.txt`), and the order of sections. Nine packages (diff, fetch, log, mqtt-client, oci, opt, pg, schema, tools) have **no landing page**; the 13 that have one (cache, client-gen, code, dns, forge, gateway, gpu, hdl, hooks, mqtt, quantum, robot, web) **none passes the pattern check** (each lacks a Stories link and three to five of the five required section ids (`stories`, `how`, `results`, `try`, `docs`)): each has its own design. The three done (stats, table, ml) conform.

## 2. Waves **[choice]**

One pull request per package, each small enough to review: the README to the template of its kind, `AGENTS.md` and `llms.txt`, and the landing page.

| wave | packages | work |
|---|---|---|
| 0, done | stats, table, ml | READMEs and landing pages; kit checker, renderer |
| 1 | **cancho-tools** (tier 1) | README sections (flow, audience, compare), agent file, `llms.txt`, a landing page from a manifest (the first tier-1 consumer of the renderer) |
| 2 | libraries: cache, log, schema, pg, web, client-gen, mqtt-client, diff | the `library` template; a manifest page where there is none |
| 3 | services and tools: gateway, mqtt, hooks, dns, oci, robot, fetch, opt, forge, code | the `service` or `cli` template; the *Deploy* and *Operate* sections for services |
| 4 | platforms: gpu, hdl, quantum | the `platform` template, with the oracle each result is checked against |

Each wave is merged before the next starts, so that what is learned (the template that turns out too strict, the figure that does not read) is applied once.

## 3. The landing pages: generate, or keep **[open]**

`render_landing.py` renders a page from a `landing.json` in the pattern's layout; to change the look of every page, change one stylesheet and re-render. That is the "easy to change" the standard asks for. But 13 packages have hand-written pages with their own designs (some may have features a manifest cannot express; that has not been read page by page). Proposal:

* a package **with no page** gets a generated one (nine packages);
* a package **with a page that fails the pattern** adopts the generated layout *unless its page has a feature the renderer lacks that the maintainer wants to keep*; in that case the page keeps its design and gains the required ids and the Stories link (the two things the checker needs), which is a small edit;
* nothing is replaced without that decision for that package.

## 4. What every package PR contains

1. `README.md` in the section order of its kind template, with the *Kind/Tier/Stage* line, visuals with alt text, and a comparison with a "where it is worse" column (nothing about speed or accuracy that was not measured).
2. `AGENTS.md` and `llms.txt` (or `docs/agents.md`, `docs/llms.txt`).
3. `landing.json` and the rendered `docs/index.html`, with `render_landing.py --check` and the kit checker run in CI against the pinned kit.
4. The tier-1 and tier-2 packages state whether an MCP server exists, and when it does not, say so.

How a package **pins the kit in CI** is not built: the proposal is a step that clones `cancho-kit` at a commit named in the package (a file `kit.rev`) and runs both checkers. **[open]**

## 5. Decisions

1. Approve the waves, or reorder them.
2. The kind and tier of each package (the table in `package-structure.md` section 2.9 is a proposal).
3. Section 3: which existing pages keep their design.
4. Fan-out: each package PR needs the repository attached to the session with push access (22 repositories). I would do wave 1 and wait for your review of the first PR before the rest.
5. The nine private repositories were not read and are not in the plan.
