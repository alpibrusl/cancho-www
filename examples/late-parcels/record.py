#!/usr/bin/env python3
"""Run the late-parcels story for real and write session.json: each step's command and what it printed.

    python3 record.py <table-dir> <stats-dir> <ml-dir> <clientgen-binary> <tools-dir>

Each *-dir holds the project built at the compiler revision its own manifest pins (`build/table`, `build/stats`,
`build/ml` and `build/ml-serve`, `build/jsonq`, `build/peek`, `build/tally`). `clientgen` is cancho-client-gen built the
way its CI builds it. The story: look at the data, fit a model, serve it, read what the server logged, see the world
move, retrain, serve again. Everything is a cancho binary except `curl` (the caller) and a little shell.
"""
import csv
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

here = pathlib.Path(__file__).resolve().parent
table_dir, stats_dir, ml_dir, clientgen, tools_dir = (pathlib.Path(a).resolve() for a in sys.argv[1:6])
work = pathlib.Path(tempfile.mkdtemp())
(work / "bin").mkdir()
for name, src in (("table", table_dir / "build/table"), ("stats", stats_dir / "build/stats"), ("ml", ml_dir / "build/ml"),
                  ("ml-serve", ml_dir / "build/ml-serve"), ("clientgen", clientgen), ("jsonq", tools_dir / "build/jsonq"),
                  ("peek", tools_dir / "build/peek"), ("tally", tools_dir / "build/tally")):
    (work / "bin" / name).symlink_to(src)
for f in ("parcels.csv", "next.csv"):
    shutil.copy(here / f, work / f)
env = dict(os.environ, PATH=f"{work / 'bin'}:{os.environ['PATH']}")
steps, servers = [], []
PORT = 18900


def run(cmd):
    r = subprocess.run(["bash", "-c", cmd], cwd=work, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=120)
    return r.stdout.rstrip("\n")


def step(at, note, cmd, before=None):
    """Run cmd (after `before`, a server to start) and record it; `before` is part of the shown command."""
    if before:
        before()  # the server line is started by `before`; only what follows it is run here
    steps.append({"at": at, "note": note, "cmd": cmd, "out": run(cmd.split("\n", 1)[1] if before else cmd)})


def serve(model, log_mode="2>"):
    def go():
        for s in servers:
            s.terminate()
            s.wait(timeout=10)
        servers.clear()
        p = subprocess.Popen(["bash", "-c", f"exec ml-serve --model-file {model} --port {PORT} 2{'>>' if log_mode == '2>>' else '>'} serve.log"],
                             cwd=work, env=env, stdout=subprocess.DEVNULL)
        servers.append(p)
        for _ in range(50):
            if (work / "serve.log").exists() and "listening" in (work / "serve.log").read_text():
                return
            time.sleep(0.1)
        raise SystemExit("ml-serve did not start")
    return go


J = "-H 'Content-Type: application/json'"
try:
    step("cancho-table", "Data engineer: 400 parcels from last month. Three scanner dropouts have no distance; I drop them. peek counts the lines, header included.",
         "table --where \"distance_km != ''\" --format csv parcels.csv > clean.csv; peek --count-lines --lines 1:1 clean.csv | jsonq -p /data/total_lines --format text -")
    step("cancho-stats", "Statistician: how far do parcels travel, and how many are late? (late is 0 or 1, so its mean is the late share)",
         "stats describe clean.csv --cols distance_km,late > desc.json; echo \"distance_km mean $(jsonq -p /data/columns/0/mean --format text desc.json)\"; echo \"late share $(jsonq -p /data/columns/1/mean --format text desc.json)\"")
    step("cancho-ml", "Data scientist: a logistic model for lateness, scored on the fifth of the rows ml holds out.",
         "ml fit --model logistic --target late --split train=0.8 --seed 1 --output late.ml clean.csv > fit.json; for m in accuracy recall roc_auc; do echo \"$m $(jsonq -p /data/summary/holdout/metrics/$m --format text fit.json)\"; done")
    step("cancho-ml", "Deploy: serve the model. It answers on loopback, and /health says which model file it holds, by SHA-256.",
         "ml-serve --model-file late.ml --port 18900 2> serve.log &\ncurl -s localhost:18900/health | jsonq -p /model_sha256 --format text -", before=serve("late.ml"))
    step("cancho-ml", "Asking it to listen on every address is refused unless a token file guards it.",
         "ml-serve --model-file late.ml --bind all 2>&1 | jsonq -p /error/rule --format text -")
    step("cancho-ml", "A parcel (42 km, 5 pm, raining) is predicted late. A distance written as text is refused, and the refusal points at the field.",
         f"curl -s -XPOST {J} -d '{{\"distance_km\":42.5,\"hour\":17,\"rain\":1}}' localhost:18900/predict | jsonq -p /rows/0 --format text -\n"
         f"curl -s -XPOST {J} -d '{{\"distance_km\":\"far\",\"hour\":9,\"rain\":0}}' localhost:18900/predict > bad.json; jsonq -p /rule --format text bad.json; jsonq -p /errors/0 --format text bad.json")
    step("cancho-client-gen", "Frontend: I want a typed client from the server's own OpenAPI document. The generator refuses it.",
         "curl -s localhost:18900/openapi.json > openapi.json; clientgen openapi.json --python -o client.py; echo \"exit $?\"")
    step("cancho-ml", "What did the server log? A line per request, never a payload. Three more calls, then count the statuses.",
         f"for i in 1 2 3; do curl -s -XPOST {J} -d '{{\"distance_km\":10,\"hour\":9,\"rain\":0}}' localhost:18900/predict > /dev/null; done; tail -n +2 serve.log | tally --field 3 --delim ' ' | jsonq -p /data/top --format text -")
    servers[0].terminate(); servers[0].wait(timeout=10); servers.clear()
    step("cancho-stats", "A month later. The rainy season: the parcels are not the ones the model learned from.",
         "for f in clean next; do stats describe $f.csv --cols distance_km,rain > $f.json; echo \"$f: distance_km mean $(jsonq -p /data/columns/0/mean --format text $f.json), rain share $(jsonq -p /data/columns/1/mean --format text $f.json)\"; done")
    step("cancho-ml", "The labels for the new month have come in. Score the model on all 300 new parcels.",
         "ml eval --model-file late.ml next.csv > next_eval.json; for m in accuracy recall; do echo \"$m $(jsonq -p /data/metrics/$m --format text next_eval.json)\"; done")
    step("cancho-table", "Retrain on last month plus the first 200 new parcels, and keep the last 100 aside to judge it.",
         "S=distance_km,hour,rain,late; table --select $S --limit 200 --format csv next.csv > next_train.csv; table --select $S --from 200 --format csv next.csv > next_test.csv; (cat clean.csv; tail -n +2 next_train.csv) > both.csv; for f in both next_test; do echo \"$f $(peek --count-lines --lines 1:1 $f.csv | jsonq -p /data/total_lines --format text -) lines\"; done")
    step("cancho-ml", "Same 100 parcels, old model against the retrained one.",
         "ml fit --model logistic --target late --output late2.ml both.csv > fit2.json; for m in late late2; do ml eval --model-file $m.ml next_test.csv > $m.json; echo \"$m accuracy $(jsonq -p /data/metrics/accuracy --format text $m.json) recall $(jsonq -p /data/metrics/recall --format text $m.json)\"; done")
    step("cancho-ml", "Redeploy. A reload is a restart, and /health shows the model file changed.",
         "ml-serve --model-file late2.ml --port 18900 2>> serve.log &\ncurl -s localhost:18900/health | jsonq -p /model_sha256 --format text -", before=serve("late2.ml", "2>>"))
finally:
    for s in servers:
        s.terminate()
        s.wait(timeout=10)
step("cancho-tools", "Reviewer: what may each tool do? The compilers proved it.",
     "for t in ml-serve ml table stats; do echo \"$t $($t introspect | jsonq -p /authority/effects --format text -)\"; done")


def metric(file, name):
    return float(json.loads((work / file).read_text())["data"]["metrics"][name].strip('"'))


desc = json.loads((work / "desc.json").read_text())["data"]["columns"][0]["histogram"]
steps[1]["chart"] = {"type": "histogram", "title": "Distance of last month's 397 parcels (stats' exact histogram)", "short": "Last month: distance (km)", "unit": "km", "edges": desc["edges"], "counts": desc["counts"]}
def mean(file, col):
    return json.loads((work / file).read_text())["data"]["columns"][col]["mean"]


steps[8]["chart"] = {"type": "bars", "title": "Share of parcels delivered in the rain", "short": "Share of parcels in the rain", "labels": ["last month", "the new month"], "values": [mean("clean.json", 1), mean("next.json", 1)]}
fit = json.loads((work / "fit.json").read_text())["data"]["summary"]["holdout"]["metrics"]
steps[11]["chart"] = {"type": "bars", "title": "Accuracy: the old model against the retrained one", "short": "Accuracy (0 to 1)", "labels": ["old, last month's held-out", "old, the last 100 new", "retrained, the last 100 new"],
                      "values": [float(fit["accuracy"]), metric("late.json", "accuracy"), metric("late2.json", "accuracy")]}
(here / "session.json").write_text(json.dumps({
    "title": "A parcel-lateness service: data, model, deploy, drift, retrain",
    "route": ["cancho-table", "cancho-stats", "cancho-ml", "cancho-client-gen", "cancho-ml", "cancho-tools"],
    "summary": "Data and a model before deploy; the service's own traffic and next month's parcels after. Every step is a real run of a cancho tool, and the seam where cancho-client-gen refuses ml-serve's OpenAPI document is shown as it is.",
    "source": "A recorded run of the real tools, replayed, on synthetic data (examples/late-parcels/make_data.py): nothing here measures a real courier.",
    "steps": steps}, indent=2, ensure_ascii=False) + "\n")
print("wrote session.json,", len(steps), "steps")
