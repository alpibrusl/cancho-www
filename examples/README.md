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

## late-parcels

A small courier's lateness model, from data to deploy and back again. It needs no API key and no network: every step
is a real run of a cancho tool on the machine (plus `curl` as the caller and a little shell).

1. `table` drops three scanner dropouts, `stats` describes the parcels (a histogram of distances).
2. `ml fit` fits a logistic model and scores it on the fifth of the rows it holds out (accuracy 0.9375, ROC-AUC 0.982).
3. **Deploy:** `ml-serve` serves it. `/health` names the model file by SHA-256; `--bind all` is refused without a token
   file (`serve.no-token`); a distance written as text is refused with a pointer at the field (`ml.schema.mismatch`).
4. **The seam:** `clientgen` is asked for a typed client from the server's own OpenAPI document and refuses it. The
   record schema lists the target column as an open value (`"late": {}`) and the generator models only typed schemas.
   All nine OpenAPI documents in `cancho-ml/docs/serving/` are refused (two causes, measured: empty schemas `{}`
   and `type: [T, "null"]` arrays; both removed from a copy, all nine pass). Filed as alpibrusl/cancho-ml#95. The example shows the refusal as it
   is; it does not edit the document. (Related: `cancho-client-gen`'s `scripts/build.sh` builds only `clientgen.cho`
   and fails with "no module `model`"; its CI lists all six source files, and so does `record.py`.)
5. **After deploy:** the server's access log (a line per request, no payload) is counted with `tally`.
6. **The world moves:** next month is the rainy season. `stats` shows the rain share doubling; `ml eval` on the new
   labels drops accuracy to 0.853 (recall 0.81).
7. **Retrain and redeploy:** `table` splits the new month, `ml fit` retrains on last month plus the first 200 new
   parcels, and on the last 100 the old model scores 0.83 against 0.89 for the retrained one. `ml-serve` is restarted
   with it and `/health` shows a different model SHA-256.

**The data is synthetic.** `make_data.py` writes `parcels.csv` (400 parcels) and `next.csv` (300) from fixed formulas, with
no randomness; the new month is built to drift (longer trips, more rain, rain delays more). Nothing here measures a
real courier, and the 0.83 to 0.89 gap is one 100-row comparison, not a benchmark.

    python3 examples/late-parcels/record.py <table-dir> <stats-dir> <ml-dir> <clientgen> <cancho-tools-dir>
    python3 scripts/record_demos.py <cancho> <cancho-ui> <cancho-ui checkout> examples/shop-energy/session.json examples/late-parcels/session.json

## model-review

A teammate's agent retrains a model and claims a big gain; a reviewer who never reads the training code checks the claim
using only the tools' structured answers. No API key and no network.

1. `stats` compares the frozen holdout with the training data (churn rate 0.59 against 0.53, same mean tenure).
2. The teammate's two runs are tracked with `ml fit --track`. `ml runs list` and `ml runs compare` show what changed:
   400 training rows became 480, and the claimed accuracy (0.758 to 0.977) is `metrics_on: train`, a score on rows the
   model was fitted to.
3. `table --query` joins the candidate's training file to the holdout on customer id: **80** of the 200 holdout customers
   were trained on. An `anti join` leaves the 120 customers neither side has seen.
4. On those 120: production 0.725, the candidate 0.85 (0.895 on the leaked holdout). The gain is real and about half the claim.
5. The teammate retrains on the training file only; `ml runs verify` replays the record (`verified: true`), and the model
   scores 0.867 on the clean holdout.
6. `write --if-sha256` promotes it only if production still holds the file the reviewer looked at. A second agent that
   read production before the promotion tries to promote the old, leaked candidate and is refused
   (`precondition.hash-mismatch`), with the hash the file holds now. An identical write is a no-op, not a conflict.

**The data is synthetic.** `make_data.py` writes 600 customers from fixed formulas, with no randomness; the leak is built
in (the candidate's training file is the training rows plus 80 of the holdout). The review finds what was put there.
The figures are single runs on 120 and 200 rows, not benchmarks. `hash` is called as `env hash` because bash has a
builtin of that name.

    python3 examples/model-review/record.py <table-dir> <stats-dir> <ml-dir> <cancho-tools-dir>
