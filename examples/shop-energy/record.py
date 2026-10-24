#!/usr/bin/env python3
"""Run the shop-energy story for real and write session.json: each role's command and what it printed.

    python3 record.py <table-dir> <stats-dir> <ml-dir> <tools-dir>

Each *-dir holds the project built at the compiler revision its own manifest pins (`build/table`, `build/stats`,
`build/ml`, and `build/jsonq` and `build/peek` of cancho-tools). There is no glue: a role hands the next one a file, and a
tool that dislikes the file says why, by rule. Everything that reads an answer is a cancho tool too (`jsonq`, `peek`),
so nothing on the page needs `jq`.
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

here = pathlib.Path(__file__).resolve().parent
table_dir, stats_dir, ml_dir, tools_dir = (pathlib.Path(a).resolve() for a in sys.argv[1:5])
work = pathlib.Path(tempfile.mkdtemp())
(work / "bin").mkdir()
for name, src in (("table", table_dir / "build/table"), ("stats", stats_dir / "build/stats"), ("ml", ml_dir / "build/ml"), ("jsonq", tools_dir / "build/jsonq"), ("peek", tools_dir / "build/peek")):
    (work / "bin" / name).symlink_to(src)
shutil.copy(here / "shop.csv", work / "shop.csv")
env = dict(os.environ, PATH=f"{work / 'bin'}:{os.environ['PATH']}")
steps = []


def step(at, role, note, cmd):
    r = subprocess.run(["bash", "-c", cmd], cwd=work, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=120)
    steps.append({"at": at, "note": f"{role}: {note}", "cmd": cmd, "out": r.stdout.rstrip("\n")})


step("cancho-ml", "Data scientist (ml)", "I take the file as it came. The tool refuses, and names the row and the rule.",
     "ml fit --model linear --target kwh --output kwh.ml shop.csv > refusal.json; jsonq -p /error/rule --format text refusal.json; jsonq -p /error/detail --format text refusal.json")
step("cancho-stats", "Statistician (stats)", "What is wrong with it? Three cells are missing in the target.",
     "stats describe shop.csv --cols kwh > kwh.json; for k in count missing mean; do echo \"$k $(jsonq -p /data/columns/0/$k --format text kwh.json)\"; done")
step("cancho-table", "Data engineer (table)", "I drop the rows with no reading, and hand the rest on. peek counts the lines: the header and 117 rows.",
     "table --where \"kwh != ''\" --format csv shop.csv > clean.csv; peek --count-lines --lines 1:1 clean.csv | jsonq -p /data/total_lines --format text -")
step("cancho-stats", "Statistician (stats)", "Same question on the clean file: exact figures, with the median.",
     "stats describe clean.csv --cols kwh > clean.json; for k in count missing mean sd quantiles/2/value; do echo \"$k $(jsonq -p /data/columns/0/$k --format text clean.json)\"; done")
SEL = "hour,outside_c,open,kwh"
step("cancho-table", "Data engineer (table)", "The readings are in time order, so I hold out the last 24 rows and hand over the 93 before them. peek counts lines, the header included.",
     f"table --select {SEL} --limit 93 --format csv clean.csv > train.csv; table --select {SEL} --from 93 --format csv clean.csv > test.csv; for f in train test; do echo \"$f $(peek --count-lines --lines 1:1 $f.csv | jsonq -p /data/total_lines --format text -) lines\"; done")
step("cancho-ml", "Data scientist (ml)", "I fit on the 93 earlier rows and score on the 24 the model never saw.",
     "ml fit --model linear --target kwh --output kwh.ml train.csv > fit.json; ml eval --model-file kwh.ml test.csv > eval.json; ml predict --model-file kwh.ml test.csv > pred.json; for m in rmse mae r2; do echo \"$m $(jsonq -p /data/metrics/$m --format text eval.json)\"; done")
step("cancho-tools", "Reviewer (jsonq, peek)", "Before this ships: what may each tool do, the reading tools included? The compilers proved it.",
     "for t in table stats ml jsonq peek; do echo \"$t $($t introspect | jsonq -p /authority/effects --format text -)\"; done")
def chart_data():
    import csv
    hist = json.loads((work / "clean.json").read_text())["data"]["columns"][0]["histogram"]
    steps[3]["chart"] = {"type": "histogram", "title": "kwh, the 117 clean readings: stats' exact histogram", "short": "kWh of the 117 clean readings", "unit": "kWh", "edges": hist["edges"], "counts": hist["counts"]}
    actual = [float(r["kwh"]) for r in csv.DictReader(open(work / "test.csv"))]
    pred = [float(r[0]) for r in json.loads((work / "pred.json").read_text())["data"]["rows"]]
    assert len(actual) == len(pred) == 24, (len(actual), len(pred))
    steps[5]["chart"] = {"type": "scatter", "title": "The 24 held-out rows: predicted against actual", "short": "Held-out rows: predicted vs actual", "unit": "kWh", "points": [[a, round(p, 3)] for a, p in zip(actual, pred)]}


chart_data()
(here / "session.json").write_text(json.dumps({
    "title": "A shop's energy, passed between roles",
    "route": ["cancho-ml", "cancho-stats", "cancho-table", "cancho-ml", "cancho-tools"],
    "summary": "A data scientist, a statistician and a data engineer pass one file between them, each with their own command line, and cancho-tools to read what they print. No glue, no new package: a tool that dislikes the file says why, by rule.",
    "source": "A recorded run of the real tools, replayed, on synthetic data (examples/shop-energy/make_data.py): nothing here measures a real shop.",
    "steps": steps}, indent=2, ensure_ascii=False) + "\n")
print("wrote session.json,", len(steps), "steps")
