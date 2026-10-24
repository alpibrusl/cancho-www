# Examples

Whole problems solved with cancho tools, recorded from real runs. The map on the project page replays them
(`data/demos.json`, written by `scripts/record_demos.py`).

## shop-energy

A data scientist (`ml`), a statistician (`stats`) and a data engineer (`table`) pass one CSV between them, each with
their own command line. There is no glue and no new package: a role hands the next one a file, and a tool that dislikes
the file says why, by rule.

1. `ml fit` on the raw file refuses by rule `ml.input.non-numeric`, naming row 17.
2. `stats describe` finds 3 missing cells in `kwh`.
3. `table --where "kwh != ''"` drops those rows.
4. `stats describe` on the clean file gives exact figures.
5. `ml fit` fits a linear model and scores it on rows it held out.
6. `introspect` on each tool says what its compiler proved it can reach.

**The data is synthetic.** `make_data.py` writes `shop.csv` from fixed formulas, with no randomness, and empties three
cells on purpose. Nothing here measures a real shop. The scores are the fit's own held-out rows (24), not `ml eval` on
the training rows.

Each tool is built as its own README says, at the compiler revision its own manifest pins (they differ), then:

    python3 examples/shop-energy/record.py <table-dir> <stats-dir> <ml-dir>
    python3 scripts/record_demos.py <cancho> <cancho-ui> <cancho-ui checkout> examples/shop-energy/session.json

The recorder needs the built tools and `jq`, so CI does not run it; the recorded `session.json` is what is checked in.
