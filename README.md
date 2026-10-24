# cancho-www

The home page of the cancho ecosystem: the language ([cancho](https://github.com/alpibrusl/cancho)) and every public `cancho-*` repository, as one page. Plain HTML, CSS and JavaScript; no framework, and the only build step is a Python script that derives the agent files.

The concept is La Pedriza (Sierra de Guadarrama): granite boulders resting on one another with no mortar, as a picture of pieces that each state what they rest on. The hero, the cairn dividers and the ecosystem map are drawn procedurally from a seed (`assets/rocks.js`), so the same page always draws the same rocks.

## Where things are

| | |
|---|---|
| `data/ecosystem.json` | **The one source of truth**: every project, its stage, summary and links, plus the measured self-hosting figures. The map and the proof section are drawn from it. `page` is a project's landing page, `url` its repository. |
| `index.html`, `assets/` | The page. `assets/site.js` has the hero, the authority animation, the map and the proof charts. |
| `data/ecosystem.json` → `verifies`, `paths` | What cancho verifies today (each claim with its evidence link, in three lists: compiler, tests, still being established) and the three exploration paths. Rendered into the page and `agents.md` by the generator, so the two cannot disagree. Re-count the fixture numbers (`tests/reject`, `tests/accept`) when you change them, and update the stamp. |
| `demo/transcript.txt` | The recorded demo as text, from a real run: `scripts/demo_transcript.sh <cancho-binary>`. Embedded in the page by the generator. |
| `data/demos.json` | The per-project sessions the map replays ("Walk here"), from real runs: `scripts/record_demos.py <cancho> <cancho-ui> <cancho-ui checkout>`. A project with no entry says so. |
| `examples/` | The recorded stories the map replays (shop-energy, late-parcels), with their data and recorders ([examples/README.md](examples/README.md)). |
| `agents.md`, `llms.txt`, `llms-full.txt` | The agent version of the page. **Generated** from `data/ecosystem.json` by `scripts/gen_agent_files.py`; do not edit by hand. The `agent` switch in the header shows `agents.md`. |
| `ui/agent-files.cui`, `assets/agent-files.js` | The agent-files pane, **written in [cancho-ui](https://github.com/alpibrusl/cancho-ui)**: `requires Network;` and nothing else. `assets/agent-files.js` is its compiled output (do not edit); rebuild it with `cancho-ui build ui/agent-files.cui -o assets/agent-files.js` and replay the behaviour with `cancho-ui test ui/agent-files.cui ui/agent-files.trace.json`. Everything else on the page is plain JS because cancho-ui has no SVG, media or styling primitives yet. |
| `assets/scene.js`, `og.png`, `assets/img/` | The hero scene is drawn by `scene.js`. `og.png` (the link-preview card) is rendered by `node scripts/make_og.js` (needs `playwright`) from `scripts/og/og.html`; re-render it when the tagline changes. `assets/img/` holds the gallery and agents-band images, generated with Mistral AI (see `THIRD_PARTY.md`). |
| `demo/`, `assets/media/` | The recorded videos (`scripts/record_demo.sh` makes the first). |

Fonts (Plus Jakarta Sans, JetBrains Mono; SIL OFL) are served from `assets/fonts/`, so the page makes no third-party requests; see `THIRD_PARTY.md`.

`scripts/github_about.sh` holds the GitHub About text for the repositories that had none; run it once with `gh` logged in.

## Changing it

```sh
$EDITOR data/ecosystem.json          # add a project, change a stage, update the figures
python3 scripts/gen_agent_files.py   # regenerate agents.md, llms.txt, llms-full.txt, the list under the map
bash scripts/build_site.sh           # assemble _site/
python3 -m http.server -d _site      # the page fetches data/ecosystem.json, so serve it, do not open the file
```

CI (on pull requests and before every deploy) fails if the generated files are stale (`gen_agent_files.py --check`) or if `data/ecosystem.json` lists a repository that is not public (`scripts/check_public.py`, an anonymous `git ls-remote` per repository, and an HTTP check that each `page` answers). A `page` is only listed when the repository's own README or website field links it. Stages are `working`, `alpha`, `early`, `built`, `design`; use a stage only if the project's own README says so, and `built` when it does not name one. A figure that turns out wrong is corrected in `data/ecosystem.json`, the way the rest of this project corrects claims.

## Deploying

`.github/workflows/pages.yml` deploys `_site/` to GitHub Pages on push to `main`, at `alpibrusl.github.io/cancho-www/` (all links are relative).

Custom domain, once bought (planned: `cancho.dev`): add `echo "<domain>" > _site/CNAME` to `scripts/build_site.sh`, point the apex at GitHub Pages (A records 185.199.108.153, .109.153, .110.153, .111.153; AAAA 2606:50c0:8000::153 to 8003::153; `www` CNAME to `alpibrusl.github.io`), then set the custom domain and enforce HTTPS in Pages settings. Update `<link rel="canonical">`, `og:url` and `og:image` in `index.html`, and `site` in `data/ecosystem.json` (it feeds the URLs in the generated `agents.md` and `llms.txt`; run `scripts/gen_agent_files.py`).
