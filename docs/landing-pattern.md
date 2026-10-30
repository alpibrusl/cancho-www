# The landing pattern of the cancho tools

Status: **a pattern with a checker, applied to the home pages of cancho-stats, cancho-table and cancho-ml** (the ecosystem page in this repository follows it where it applies). Written 2026-10-30 after the three pages were seen to diverge: three section orders, three footers, three ways to reach the stories (a section, a nav link, a card hidden in the small print).

## 1. Why a pattern

A reader who has seen one tool's page should find the same things in the same places on the next: what the promise is and what it does not cover, a story with real data, how it works, what was measured and by whom, what exists and what does not, how to try it. Differences should be the tool's own content, not its layout.

## 2. The sections

On a tool's home page, in this relative order. The **id** is the anchor; a header link and a section have the same id.

| id | section | rule |
|---|---|---|
| `why` | the promise in three or four cards | **recommended.** Followed by one paragraph saying what the promise does *not* establish (the digits, the plan, the model; not the question, the assumptions or the interpretation) and pointing at the stories. |
| `stories` | the stories, by topic | **required.** The block between `<!--stories-->` and `<!--/stories-->` is generated from the stories page by `storylib.fill_stories` (so the home page and the stories page cannot differ); the page may instead hold a short static section when a size budget forbids the chips (cancho-ml). |
| `how` | how it works | **required.** |
| `watch` | a real run, replayed | recommended. |
| `status` | what exists today, and what does not | recommended. Built verbs, the ones designed and not built, and what a reader cannot yet do. |
| `results` | "Measured, not promised" | **required.** Every number says what was run, where, and by whom: a CI job on every push, or a run made by hand and reported in a document. A count of mutants or machines is never given without that. |
| `try` | install, first command | **required.** |
| `agent` | the page as an agent reads it | optional (cancho-ml calls it `agent-view`). |
| `docs` | go deeper | **required.** |

Only the relative order of the required sections is checked: `stories` < `how` < `results` < `try` < `docs`.

## 3. The header

Links, in this order: *How it works*, *Stories*, then the tool's own pages or anchors, *Try it*, *Docs*, *GitHub*. **Stories is always present.** A tool with several pages (cancho-ml has seven) lists them; the header is the same list on every page, at most nine links, and the optional ones are hidden at phone width with the class `opt`.

## 4. The footer

`name · EUPL-1.2 · written in cancho · the sibling tools`.

## 5. What is shared, and how

* `scripts/storylib.py` (page skeleton pieces, the stories submenu, the grouped table of contents, `fill_stories`) is **one file copied into four repositories**. That is the weak point: the copies can drift. The design for a shared cancho library, pinned by commit, is `docs/stories-in-cancho.md` in cancho-stats; until it is built, a change to `storylib.py` is made in all four.
* The design tokens (colours, fonts) are the same on every page; the accent colour is the tool's own variable.

## 6. Checking it

`python3 scripts/check_landing_pattern.py PATH-TO-HOME-PAGE...` (this repository) reads home pages and reports a missing required id, a wrong relative order, a missing *Stories* link in the header and a missing `stories` region marker. It needs no build and no network. CI here cannot see the other repositories, so it is run by hand when a home page changes; each tool's own CI keeps its own checks (`gen_stories.py --check`, and in cancho-ml `check_landing.py`).

## 7. Where the three pages stand

| | why | stories | how | watch | status | results | try | docs | agent |
|---|---|---|---|---|---|---|---|---|---|
| cancho-stats | yes | generated block | yes | yes | yes | yes | yes | yes | no |
| cancho-table | yes | generated block | yes | yes | `does` and `cannot` | yes | yes | yes | yes |
| cancho-ml | no | short static section | yes | yes | in the small print | yes | yes | yes | `agent-view` |

Open: cancho-ml has no `why` section (its hero carries the promise) and no `status` section outside the small print; its page is held to 32 KiB by its own landing check, so both are content decisions for that project, not layout ones.
