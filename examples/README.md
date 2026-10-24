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
   All nine OpenAPI documents in `cancho-ml/docs/serving/` are refused the same way. The example shows the refusal as it
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

## ship-an-api

One declaration is a service, its OpenAPI document and the source of a typed client; an app uses it, the data it
generates is analysed, an agent changes the contract, and the service is packaged as an image. No API key and no network.
The service is `cancho-web`'s own `users` example; nothing here writes a service.

1. `cancho-web` builds the service (at the compiler revision it pins), and a bad request is refused with every error at
   once, each with its JSON Pointer, as problem+json. `GET /openapi.json` comes from the same declaration.
2. `clientgen` (cancho-client-gen) reads that document, lists 5 operations and 4 components, and writes a Python client.
3. **A seam, shown as it is:** the client annotates its responses as dataclasses (`-> Page`), but at runtime they are
   plain `dict`s (`dict {'total': 0, 'items': []}`). Its README says the types are strict; the `cast` that makes
   `mypy --strict` pass hides this. Not filed anywhere yet.
4. An app (the only Python on the path, a stand-in for the customer) registers 200 users through the client: 186 accepted,
   14 refused (`/age` 9 times, `/name` 5 times). `table` counts the statuses and the refused fields from what the app wrote.
5. `stats` describes the ages the service holds (an exact histogram) and `table` counts the users over 120 (4); a column is
   text to `table` unless it says `:int`, so `age > 120` would silently compare text and `age:int > 120` is right.
6. An agent proposes a tighter limit. `replace` edits the one line of the declaration and refuses unless it matches exactly
   once; the service is rebuilt (static, through the linker wrapper) and the served document says 120 instead of 150. The
   generated client does not change (`client unchanged`: the limit lives in the server's schema), and a 130-year-old
   customer, valid before, is now refused at `/age` with `maximum`.
7. `oci-build` refuses the dynamically linked build by rule (`elf-dynamic`), accepts the static one, and builds the image
   twice into two directories: identical. **Measured:** two builds of the *source* differ by 2 bytes, in one directory or
   two, so the digest changes with each fresh build; the claim is that the same binary gives the same image. I have not
   looked for the cause.
8. `cancho authority` on the service: it may accept connections and read the clock, and never touches the filesystem,
   signals, other programs or foreign code.

**The data is synthetic.** `app.py` makes users from fixed formulas with no randomness; some are invalid on purpose and a
few are very old but valid. Nothing here measures a real service.

    python3 examples/ship-an-api/record.py --web DIR --schema DIR --compiler-checkout DIR --compiler BIN --clientgen BIN --oci DIR --table DIR --stats DIR --tools DIR
