# One structure for the cancho packages (proposal)

Status: **proposal, nothing applied.** Written 2026-10-30 from a survey of the repositories as they are today. Marks: **[read]** seen in the repositories, **[choice]** a decision the maintainer can overturn, **[open]** not decided. It extends `docs/landing-pattern.md` (the layout of a home page) to the whole package: README, agent surface, examples, comparison, numbers.

## 1. What the survey found

28 repositories were read (shallow clones of the public ones, plus the six this work touched): the two languages (`cancho`, `cancho-ui`), the site (`cancho-www`), and 25 packages. Nine private repositories were not opened. **[read]**

**Four kinds of package.** Command-line tools (`cancho-stats`, `-table`, `-ml`, `-opt`, `-fetch`, `-tools`, `-diff`, `-oci`, `-dns`), libraries (`-pg`, `-mqtt-client`, `-log`, `-cache`, `-schema`, `-web`, `-client-gen`), services and applications (`-gateway`, `-mqtt`, `-hooks`, `-robot`, `-forge`, `-code`), and platforms (`-gpu`, `-hdl`, `-quantum`).

**Four generations of README.**

| style | repositories | section order |
|---|---|---|
| product | `-ml`, `-table`, `-tools`, `-mqtt` | One complete flow, Why X, Quick start, What you can do, Built to be read by an agent, What it cannot do, How fast, Learn more |
| library | `-pg`, `-web`, `-cache`, `-log`, `-schema`, `-gpu` | Status, Requirements, Quick start, Examples, Usage or API, Tests, Layout, Limitations |
| intent | `-oci`, `-robot`, `-gateway`, `-fetch` | Why, Intended scope, what we expect stated before measuring, open questions |
| minimal | `-hdl`, `-code`, `-forge`, `-ui`, `-opt`, `-quantum` | Try it, More (or no headings) |

`cancho-stats` has **an empty README** (0 lines) although it is the project with the most documentation. **[read]**

**What exists, by feature** (of the 25 packages plus `cancho`, `cancho-ui`, `cancho-www`; a rough scan of files and README text):

* A landing page: 17. An agent document (`AGENTS.md`, `agents.md` or skills): 8. `llms.txt`: 8. An MCP server: 3 (`-table`, `-ml`, `-tools`). A benchmark directory or page: 9. A comparison with another tool in the README: 21, of which a measured table in 3. A stories page: 3 (stats, table, ml).
* Product-style READMEs state numbers with their conditions; library-style READMEs mostly state none; `cancho-ml` says plainly that **no speed is claimed** for its command line and gives the library timings with machine, load and minimum of N.
* The agent surface of the three data tools is `NAME skill`, `NAME introspect`, an authority manifest, rule-tagged JSON refusals, and (table, ml) an MCP server. `cancho-stats` has the first four and no agent document, no `llms.txt`, no MCP server.

## 2. The shape: a package kit

A package is **README + docs/ + agent surface + examples + checks**, in a fixed layout. Every package has the required items; the tier says how many of the optional ones. **[choice]**

### 2.1 Files

```
README.md            the front door; fixed section order (2.2), at most about 200 lines
AGENTS.md            for agents; short; says to ask the tool (skill, introspect), not this file
llms.txt             the page as an agent reads it
CLAUDE.md            the project's rules (design before code, measured claims, the gate)
LICENSE, NOTICE
docs/
  index.html         landing page, following docs/landing-pattern.md
  stories.html       the cases (2.4); generated from real runs, --check in CI
  agents.md          generated from the binary or the library's introspection
  agent-example.md   the transcript of 2.6; generated from a scripted run
  comparison.md      how it compares (2.5)
  benchmarks.*       the numbers (2.7), with conditions and how to rerun
  design.md          the design, each feature marked [measured] [choice] [open]
  status.md          what exists, what does not
examples/            small runnable inputs and expected outputs (the basic examples)
bench/               scripts that regenerate every number the README quotes
scripts/check_*.py   the checks of this kit
```

### 2.2 README sections, in this order

1. **Name, one sentence, stage.** The promise in a line, and the stage: `design`, `built` or `measured`.
2. **One complete flow.** A real run of ten lines or fewer: input, command, output, and a refusal with its repair.
3. **What is special.** Three or four points, each with its evidence and **what it does not cover** (the digits, not the model; the plan, not the question). The cancho points are the same everywhere and are the reason to use a cancho package: *the authority row* (what the program can reach, derived by the compiler, committed and checked), *refusals are data* (a rule tag, an exit code, a repair), *exactness and same bytes* where a sum decides, *pinned dependencies, never copied*.
4. **For humans, for agents.** Two short columns, side by side: the human path (quick start, the landing page, the stories) and the agent path (`skill`, `introspect`, MCP, `AGENTS.md`).
5. **Quick start.** Two minutes, copy-paste.
6. **Examples.** Three basic ones, then a link to the cases.
7. **Compared with.** Two or three alternatives (2.5).
8. **How fast.** Three to five numbers (2.7), or the sentence *no speed is claimed*.
9. **Use it with an AI agent.** The configuration and a link to the transcript (2.6).
10. **What exists, what cannot yet.** Built, designed and not built, refused on purpose.
11. **Learn more, Contributing, Licence.**

A library replaces *One complete flow* with a ten-line program and *For agents* with how an agent writes code against it (the compiler's JSON diagnostics, `cancho check`, `inspect`).

### 2.3 Tiers

| tier | meaning | required | optional |
|---|---|---|---|
| 1, flagship | stats, table, ml, tools | everything above | none left out |
| 2, library or service | pg, web, cache, log, schema, mqtt, gateway, ... | README 1, 2, 3, 5, 6, 10, 11; AGENTS.md; examples; one benchmark with conditions | landing page, stories, MCP |
| 3, intent | oci, robot, fetch, gpu, quantum ... | README 1, 3, 10, 11 and the stage `design` stated first | everything else |

The tier is written in `README.md` (line one under the title) and checked.

### 2.4 Examples and business cases, shared

**Basic examples** live in `examples/` of the package: small, runnable, with expected output, every one run by a check.

**Business cases** are the stories: one narrative, one seeded dataset, real runs, figures, the narration checked against the numbers. They are **shared**: a case has an id, and each package renders the slice it can do. The marketing case already works this way by accident: the ledger in `cancho-table`, the holdout and the dashboard that lies in `cancho-stats`, the uplift in `cancho-ml`, the three in a row in `cancho-www`. The proposal makes it a list: **[choice]**

* `data/cases.json` in `cancho-www`: `{id, vertical, title, steps: [{package, story, what it does}]}`. Each package's stories page links the others' steps; the ecosystem page draws the list.
* **Verticals**: marketing, finance, medicine and pharma, science (biology, chemistry, physics), social science, industrial and IoT (`-mqtt`, `-hooks`, `-hdl`, `-robot`), infrastructure and data services (`-pg`, `-gateway`, `-log`, `-cache`, `-oci`), software engineering (`-forge`, `-code`).
* A case is **invented and seeded**, says so, and plants its effects on purpose; it never claims to be a measurement of the world.

### 2.5 Compared with

One table per package, `docs/comparison.md`, and the README carries the short one. Rules, taken from the projects' own CLAUDE.md files: **[choice]**

* The alternatives are the two or three that a reader would otherwise use (for table: DuckDB, csvtk, Miller; for ml: scikit-learn; for stats: SciPy, R; for a client library: the usual client of its language).
* Each row is a *difference*, not a score: what the other tool does better, what this one does differently, and the evidence. A column "where cancho-X is worse" is required.
* A claim of speed or accuracy against another tool carries the measurement here (machine, versions, load, minimum of N) or it is not made. *Never state a speed against another library that was not measured here.*
* "Matches" is only used within a bound that was fixed in advance and measured.

### 2.6 Use it with an AI agent

`docs/agent-example.md`, generated by a script that drives the real binary (or MCP server) and writes the transcript, so it is checked like the stories: **[choice]**

1. The configuration: the MCP server entry, or the one-line `skill` command, for the usual agent runtimes.
2. A task in a sentence, the calls the agent makes, a refusal with its rule tag and repair, the repaired call, the answer. For a data tool the task is a case of 2.4; for a library, the agent writes a short program and the compiler's diagnostics steer it.
3. What the agent could **not** do, because of the authority row (no network, no write by path), shown as a refusal.

### 2.7 Numbers

Every number in a README has its conditions beside it: the machine, threads, load average, minimum of N, the version of any other tool, and *where cancho is slower*. They come from `bench/` scripts, and a check fails when the README quotes a number that the last recorded run does not contain. A package with no measurement says so in one sentence, as `cancho-ml` does. **[choice]**

### 2.8 The check

`scripts/check_package_kit.py` (shared, run by hand across repositories as `check_landing_pattern.py` is, and by each package's CI for its own files): the files of 2.1 for its tier, the README sections of 2.2 in order, the tier line, every relative link, every quoted number present in the recorded benchmark output, and the stories `--check`. **[open]** where the shared checker lives (see 4).

## 3. Where the packages stand against it

First wave, the four tier-1 packages:

| | README | AGENTS.md | llms.txt | MCP | examples dir | comparison | numbers | agent example | stories |
|---|---|---|---|---|---|---|---|---|---|
| cancho-stats | **empty** | no | no | no | readings.csv only | no | S0 accuracy only; no speed | no | yes |
| cancho-table | product style | no (docs/mcp.md) | no | yes (one tool) | no (stories) | DuckDB, csvtk in README | yes | partly (MCP design) | yes |
| cancho-ml | product style | yes | yes | yes | yes (gallery, examples) | scikit-learn, numpy | library timings, no CLI speed claim | agents.md, no transcript | yes |
| cancho-tools | product style | no | no | yes (several tools) | in README | `instead of` column | yes | two-agents flow | no |

The biggest single gap is the empty `cancho-stats` README; the biggest shared gap is a **transcript of an agent using the tool** (nobody has one that is checked). Tier 2 and 3 packages need an inventory pass, not new content: most have the library-style README and need the tier line, the *What is special* section and one benchmark with conditions.

## 4. Decisions

1. **Adopt the kit for the first wave** (stats, table, ml, tools) and tiers 2 and 3 afterwards? **[open]**
2. **Where the shared parts live**: the README skeleton, the checker, the agent-transcript driver, `storylib` (today copied four times), `cases.json`. Candidates: `cancho-tools` (it already holds the pinned contract package) or a new `cancho-kit`. Neither is among this session's writable repositories; see `cancho-stats/docs/stories-in-cancho.md` for the cancho-port of the generators. **[open]**
3. **Whether the libraries adopt the library variant** or are left as they are until they have users. **[open]**
4. **The nine private repositories** were not read; whether the kit applies to them is the maintainer's call. **[open]**

## 5. What would go wrong

* **Copy drift** (the `storylib` problem again): the shared parts must be pinned, not copied. That is why decision 2 comes first.
* **Claims without a run**: the comparison and numbers rules are the point of the kit; a template that is filled with unmeasured numbers is worse than a short README.
* **Over-prescription**: a tier-3 package with a design and no code should say so and stop; the kit must not push it to invent benchmarks.
* **Sameness hiding the product**: the *What is special* section is where each package says what only it does; the pattern fixes the place, not the content.
