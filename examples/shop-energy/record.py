#!/usr/bin/env python3
"""Run the shop-energy story for real and write session.json: each role's command and what it printed.

    python3 record.py <table-dir> <stats-dir> <ml-dir>

Each *-dir holds the project built at the compiler revision its own manifest pins (`build/table`, `build/stats`,
`build/ml`). There is no glue: a role hands the next one a file, and a tool that dislikes the file says why, by rule.
Nothing here is cancho but the tools; `jq` only trims what they print.
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

here = pathlib.Path(__file__).resolve().parent
table_dir, stats_dir, ml_dir = (pathlib.Path(a).resolve() for a in sys.argv[1:4])
work = pathlib.Path(tempfile.mkdtemp())
(work / "bin").mkdir()
for name, src in (("table", table_dir / "build/table"), ("stats", stats_dir / "build/stats"), ("ml", ml_dir / "build/ml")):
    (work / "bin" / name).symlink_to(src)
shutil.copy(here / "shop.csv", work / "shop.csv")
env = dict(os.environ, PATH=f"{work / 'bin'}:{os.environ['PATH']}")
steps = []


def step(at, role, note, cmd):
    r = subprocess.run(["bash", "-c", cmd], cwd=work, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=120)
    steps.append({"at": at, "note": f"{role}: {note}", "cmd": cmd, "out": r.stdout.rstrip("\n")})


step("cancho-ml", "Data scientist (ml)", "I take the file as it came. The tool refuses, and names the row and the rule.",
     "ml fit --model linear --target kwh --output kwh.ml shop.csv | jq -c '.error | {rule, detail}'")
step("cancho-stats", "Statistician (stats)", "What is wrong with it? Three cells are missing in the target.",
     "stats describe shop.csv --cols kwh | jq -c '.data.columns[] | {name, count, missing, mean}'")
step("cancho-table", "Data engineer (table)", "I drop the rows with no reading, and hand the rest on.",
     "table --where \"kwh != ''\" --format csv shop.csv > clean.csv; tail -n +2 clean.csv | wc -l")
step("cancho-stats", "Statistician (stats)", "Same question on the clean file: exact figures, with the quantiles.",
     "stats describe clean.csv --cols kwh,outside_c | jq -c '.data.columns[] | {name, count, missing, mean, sd, median: .quantiles[2].value}'")
step("cancho-ml", "Data scientist (ml)", "Now it fits, and it holds 20% of the rows out to score on.",
     "ml fit --model linear --target kwh --split train=0.8 --seed 1 --output kwh.ml clean.csv | jq -c '.data.summary | {coefficients: [.coefficients[] | {(.name): .value}], holdout: .holdout.metrics}'")
step("cancho-ml", "Reviewer", "Before this ships: what may each tool do? The compilers proved it.",
     "for t in table stats ml; do echo \"$t $($t introspect | jq -c '.authority.effects')\"; done")
(here / "session.json").write_text(json.dumps({
    "title": "A shop's energy, passed between roles",
    "route": ["cancho-ml", "cancho-stats", "cancho-table", "cancho-ml"],
    "summary": "A data scientist, a statistician and a data engineer pass one file between them, each with their own command line. No glue, no new package: a tool that dislikes the file says why, by rule.",
    "source": "A recorded run of the real tools, replayed, on synthetic data (examples/shop-energy/make_data.py): nothing here measures a real shop.",
    "steps": steps}, indent=2, ensure_ascii=False) + "\n")
print("wrote session.json,", len(steps), "steps")
