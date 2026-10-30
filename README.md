# cancho-www

The home page of the cancho ecosystem: the language ([cancho](https://github.com/alpibrusl/cancho)) and every public `cancho-*` repository, as one page.

**Since the switch, `cancho.dev/` is the page written in [cancho-ui](https://github.com/alpibrusl/cancho-ui)** (`docs/www-port/` there), built at the commit pinned in `scripts/build_site.sh`. The previous hand-written page (plain HTML, CSS and JavaScript, no framework; everything below up to "Deploying" describes it) is kept, unchanged, at **`cancho.dev/classic/`** as the rollback. See "How the site is built" and "Rolling back".

The concept is La Pedriza (Sierra de Guadarrama): granite boulders resting on one another with no mortar, as a picture of pieces that each state what they rest on. The hero, the cairn dividers and the ecosystem map are drawn procedurally from a seed (`assets/rocks.js`), so the same page always draws the same rocks.

## Where things are

| | |
|---|---|
| `data/ecosystem.json` | **The one source of truth**: every project, its stage, summary and links, plus the measured self-hosting figures. The map and the proof section are drawn from it. `page` is a project's landing page, `url` its repository. |
| `index.html`, `assets/` | The page. `assets/site.js` has the hero, the authority animation, the map and the proof charts. |
| `data/ecosystem.json` → `verifies`, `paths` | What cancho verifies today (each claim with its evidence link, in three lists: compiler, tests, still being established) and the three exploration paths. Rendered into the page and `agents.md` by the generator, so the two cannot disagree. Re-count the fixture numbers (`tests/reject`, `tests/accept`) when you change them, and update the stamp. |
| `demo/transcript.txt` | The recorded demo as text, from a real run: `scripts/demo_transcript.sh <cancho-binary>`. Embedded in the page by the generator. |
| `data/demos.json` | The per-project sessions the map replays ("Walk here"), from real runs: `scripts/record_demos.py <cancho> <cancho-ui> <cancho-ui checkout>`. A project with no entry says so. |
| `examples/` | The recorded stories the map replays (shop-energy, late-parcels, model-review, ship-an-api), with their data and recorders ([examples/README.md](examples/README.md)). |
| `agents.md`, `llms.txt`, `llms-full.txt` | The agent version of the page. **Generated** from `data/ecosystem.json` by `scripts/gen_agent_files.py`; do not edit by hand. The `agent` switch in the header shows `agents.md`. |
| `ui/agent-files.cui`, `assets/agent-files.js` | The agent-files pane, **written in [cancho-ui](https://github.com/alpibrusl/cancho-ui)**: `requires Network;` and nothing else. `assets/agent-files.js` is its compiled output (do not edit); rebuild it with `cancho-ui build ui/agent-files.cui -o assets/agent-files.js` and replay the behaviour with `cancho-ui test ui/agent-files.cui ui/agent-files.trace.json`. Everything else on the page is plain JS because cancho-ui has no SVG, media or styling primitives yet. |
| `assets/scene.js`, `og.png`, `assets/img/` | The hero scene is drawn by `scene.js`. `og.png` (the link-preview card) is rendered by `node scripts/make_og.js` (needs `playwright`) from `scripts/og/og.html`; re-render it when the tagline changes. `assets/img/` holds the gallery and agents-band images, generated with Mistral AI (see `THIRD_PARTY.md`). |
| `stories.html`, `data/stories.json`, `demo/stories/` | Six stories across the ecosystem (what a program can touch, a refusal, three tools passing one CSV along a pipe, the same bytes in any order). `data/stories.json` is **recorded** by running the compiler and the three tools: `python3 scripts/record_stories.py <cancho> <table> <stats> <ml> <table checkout> <stats checkout> <ml checkout>`; `scripts/gen_stories.py` draws the page from it (CI runs `--check`; the narration is checked against the numbers). `scripts/storylib.py` is shared with cancho-stats, cancho-table and cancho-ml. |
| `demo/`, `assets/media/` | The recorded videos (`scripts/record_demo.sh` makes the first). |

Fonts (Plus Jakarta Sans, JetBrains Mono; SIL OFL) are served from `assets/fonts/`, so the page makes no third-party requests; see `THIRD_PARTY.md`.

`scripts/github_about.sh` holds the GitHub About text for the repositories that had none; run it once with `gh` logged in.

## Changing it

```sh
$EDITOR data/ecosystem.json          # add a project, change a stage, update the figures
python3 scripts/gen_agent_files.py   # regenerate agents.md, llms.txt, llms-full.txt, the list under the map
bash scripts/build_site.sh           # assemble _site/ (needs cargo; see below)
python3 -m http.server -d _site      # the pages fetch data, so serve it, do not open the file; / is the port, /classic/ the old page
```

**`data/ecosystem.json` is also copied into cancho-ui** (`docs/www-port/site/data/`), because the page at `/` is compiled from it there. The build **fails** when the two differ, so the live page cannot go stale: change the data here, sync the copies (and `agents.md`, `llms.txt`, `llms-full.txt`, and the data's hash in `home.cui`) in a cancho-ui pull request, then move `CANCHO_UI_REV` in `scripts/build_site.sh` to that commit in the same pull request that changes the data. `/classic/` reads the data at run time and is always current.

CI (on pull requests and before every deploy) fails if the generated files are stale (`gen_agent_files.py --check`) or if `data/ecosystem.json` lists a repository that is not public (`scripts/check_public.py`, an anonymous `git ls-remote` per repository, and an HTTP check that each `page` answers). A `page` is only listed when the repository's own README or website field links it. Stages are `working`, `alpha`, `early`, `built`, `design`; use a stage only if the project's own README says so, and `built` when it does not name one. A figure that turns out wrong is corrected in `data/ecosystem.json`, the way the rest of this project corrects claims.

## How the site is built

`bash scripts/build_site.sh` is the one build script; `pages.yml` (deploy, on push to `main`) and `checks.yml` (pull requests) both run it. It assembles, in a temporary directory:

| URL | What |
|---|---|
| `/` | `cancho-ui build docs/www-port/site/home.cui --page`, from the cancho-ui commit named by `CANCHO_UI_REV` (default in the script; cloned and built with `cargo`), plus what the old site served at the root and the port does not carry: `CNAME`, `robots.txt`, `data/demos.json`, `assets/fonts/OFL-*.txt` |
| `/classic/` | the previous page: `index.html`, `assets/`, `data/`, `demo/`, `agents.md`, `llms*.txt`, the logos and `og.png`, byte for byte what the old build served at `/`. Every URL in it is relative, so it needed no edit to work under `/classic/`. Not indexed: `robots.txt` disallows it and its canonical link names `/` |
| `/next/` | a one-file redirect to `/` (the preview that was published before the switch) |

It then runs `scripts/check_site.py` on the finished tree (title, one h1, canonical, no root-relative URL anywhere, no resource from another origin, every internal link and resource resolves, the data files exist and are this repository's bytes, any file served at both `/` and `/classic/` is the same bytes, the projects of the data are in the HTML with JavaScript off, `/classic/` is disallowed). **Only a finished, checked build is put in place:** a failure at any step leaves `_site/` as it was, and in `pages.yml` stops the deploy, so the site that is live stays live. `scripts/check_site_browser.js` (CI, and locally with `playwright`) loads `/` and `/classic/` in Chromium, light and dark, at 1280 and 412 px, and fails on a request outside the origin, a console or page error, a failed request, or a broken internal link.

Needs `cargo` (and network access to clone cancho-ui and fetch its crates). To build against a checkout you already have: `CANCHO_UI_DIR=<checkout at the pinned commit> CARGO_TARGET_DIR=<a build dir> bash scripts/build_site.sh`.

## Rolling back

Either, whichever is quicker:

1. **Revert the switch**: `git revert -m 1 <the merge commit of the go-live pull request>` (or `git revert <the squash commit>`), open it as a pull request, merge it. That restores the previous build script, workflows and `robots.txt`: the old page is at `/` again, as before, and `/classic/` and the redirect at `/next/` go away. One commit.
2. **Keep the machinery, serve the old page at `/`** (an outline; not exercised, and `scripts/check_site.py` would need the same change): in `scripts/build_site.sh`, build the classic tree directly into the root (replace the `mv "$WORK/root" "$WORK/site"` / `mv "$C" ...` pair with `mv "$C" "$WORK/site"` plus the `CNAME` and `robots.txt` it needs) and skip the cancho-ui steps. `/classic/` can then be left out or kept.

Either way, deploy is a push to `main`, and `workflow_dispatch` on `pages.yml` redeploys without a commit.

## Deploying

`.github/workflows/pages.yml` builds the site (above) and deploys `_site/` to GitHub Pages on push to `main`, at `cancho.dev` (all links are relative, so it also works under `alpibrusl.github.io/cancho-www/`).

Custom domain: **cancho.dev** (registered at OVHcloud). The page, `og:url`, `og:image`, the canonical link, the share card and the URLs in `agents.md` / `llms.txt` (`site` in `data/ecosystem.json`) all use it. DNS, at the registrar: apex `A` records 185.199.108.153, .109.153, .110.153, .111.153; `AAAA` 2606:50c0:8000::153 to 8003::153; `www` as a `CNAME` to `alpibrusl.github.io`. Then, in the repository's Settings > Pages, set the custom domain to `cancho.dev` and tick Enforce HTTPS once the certificate is issued. The other projects' landing pages stay on `alpibrusl.github.io/<repo>/`.

The layout the tools' own landing pages share (sections, ids, header, footer, how it is checked) is written in [`docs/landing-pattern.md`](docs/landing-pattern.md); `scripts/check_landing_pattern.py` checks a home page against it.
