# Examples

Whole problems solved with cancho tools, recorded from real runs. The map on the project page replays them
(`data/demos.json`, written by `scripts/record_demos.py`).

## shop-energy

A data scientist (`ml`), a statistician (`stats`) and a data engineer (`table`) pass one CSV between them, each with
their own command line, and everything that reads an answer is a cancho tool too (`jsonq`, `peek` from cancho-tools),
so nothing here needs `jq`. There is no glue and no new package: a role hands the next one a file, and a tool that dislikes
the file says why, by rule.

1. `ml fit` on the raw file refuses by rule `ml.input.non-numeric`, naming row 17.
2. `stats describe` finds 3 missing cells in `kwh`.
3. `table --where "kwh != ''"` drops those rows.
4. `stats describe` on the clean file gives exact figures and a histogram: two humps, the shop closed and open.
5. `table --limit` and `--from` hold out the last 24 rows, because the data is in time order.
6. `ml fit` on the 93 earlier rows, `ml eval` on the 24 it never saw, and a predicted-against-actual plot of those 24.
7. `introspect` on each tool, the reading tools included, says what its compiler proved it can reach.

**The data is synthetic.** `make_data.py` writes `shop.csv` from fixed formulas, with no randomness, and empties three
cells on purpose. Nothing here measures a real shop. The scores are `ml eval` on the 24 held-out rows (rmse 0.318, r2 0.971), not on the
training rows. The charts on the page are drawn from numbers the tools printed (`stats`' histogram, `ml predict`),
copied into the session by `record.py`; nothing is estimated.

Each tool is built as its own README says, at the compiler revision its own manifest pins (they differ), then:

    python3 examples/shop-energy/record.py <table-dir> <stats-dir> <ml-dir> <cancho-tools-dir>
    python3 scripts/record_demos.py <cancho> <cancho-ui> <cancho-ui checkout> examples/shop-energy/session.json

The recorder needs the built tools, so CI does not run it; the recorded `session.json` is what is checked in.
