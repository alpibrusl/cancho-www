#!/usr/bin/env python3
"""Run the model-review story for real and write session.json: each step's command and what it printed.

    python3 record.py <table-dir> <stats-dir> <ml-dir> <tools-dir>

Each *-dir holds the project built at the compiler revision its own manifest pins (`build/table`, `build/stats`,
`build/ml`, and `build/jsonq`, `build/peek`, `build/hash`, `build/write` of cancho-tools). The story: a teammate's agent
proposes a new model and claims a big improvement; a reviewer who never reads the training code checks the claim with the
run records, a join on customer ids, a frozen holdout and a guarded write. Everything is a cancho binary and a little shell. (`hash` is called as `env hash`, because bash has a builtin of that name.)
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
for name, src in (("table", table_dir / "build/table"), ("stats", stats_dir / "build/stats"), ("ml", ml_dir / "build/ml"),
                  ("jsonq", tools_dir / "build/jsonq"), ("peek", tools_dir / "build/peek"), ("hash", tools_dir / "build/hash"),
                  ("write", tools_dir / "build/write")):
    (work / "bin" / name).symlink_to(src)
for f in ("train.csv", "holdout.csv", "candidate_train.csv"):
    shutil.copy(here / f, work / f)
(work / "prod").mkdir()
(work / "runs").mkdir()
env = dict(os.environ, PATH=f"{work / 'bin'}:{os.environ['PATH']}")
steps = []


def step(at, note, cmd):
    r = subprocess.run(["bash", "-c", cmd], cwd=work, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=300)
    steps.append({"at": at, "note": note, "cmd": cmd, "out": r.stdout.rstrip("\n")})


def q(file, pointer):
    return f"$(jsonq -p {pointer} --format text {file})"


CLEAN_DROP = "id,monthly_spend,tickets_90d"
step("cancho-stats", "Reviewer: before judging a model, is the frozen holdout like the data it will be judged against? Compare the churn rate and tenure.",
     "for f in train holdout; do stats describe $f.csv --cols tenure_months,churned > $f.json; echo \"$f: churn rate " + q("$f.json", "/data/columns/1/mean") + ", mean tenure " + q("$f.json", "/data/columns/0/mean") + "\"; done")
step("cancho-ml", "Teammate's agent: the model in production uses tenure only. I trained a forest on every feature, and tracked both runs. (The PR's claim: accuracy 0.977 against 0.758.)",
     f"ml fit --model logistic --target churned --drop {CLEAN_DROP} --track runs --output prod/model.ml train.csv > /dev/null; "
     "ml fit --model forest --task classification --target churned --drop id --track runs --output cand.ml candidate_train.csv > /dev/null; "
     "ml runs list runs > runs.json; echo \"$(ls runs | wc -l) run records\"")
step("cancho-ml", "Reviewer: what do the run records say about each run?",
     "for i in 0 1; do echo \"" + q("runs.json", "/data/runs/$i/model") + " trained on " + q("runs.json", "/data/runs/$i/train_rows") + " rows, scored on " + q("runs.json", "/data/runs/$i/metrics_on") + "\"; done")
step("cancho-ml", "Compare them: the inputs that differ, and the headline numbers. The new model had 80 more training rows, and the 0.977 is a score on training data.",
     "A=$(jsonq -p /data/runs/0/id --format text runs.json | tr -d '\"'); B=$(jsonq -p /data/runs/1/id --format text runs.json | tr -d '\"'); ml runs compare runs $A $B > cmp.json; "
     "echo \"training rows " + q("cmp.json", "/data/inputs/3/a") + " -> " + q("cmp.json", "/data/inputs/3/b") + "\"; echo \"accuracy " + q("cmp.json", "/data/metrics/0/a") + " -> " + q("cmp.json", "/data/metrics/0/b") + "\"")
step("cancho-table", "Where did the 80 extra rows come from? A join on customer id: how many of the candidate's training customers are in the frozen holdout?",
     "table --query \"select count(*) as overlap from 'candidate_train.csv' as a inner join 'holdout.csv' as b on a.id = b.id\" | jsonq -p /data/rows/0/0 --format text -")
step("cancho-table", "So 80 of the 200 holdout customers were trained on. An anti join leaves the customers neither model has seen.",
     "table --query \"select b.id, b.tenure_months, b.monthly_spend, b.tickets_90d, b.churned from 'holdout.csv' as b anti join 'candidate_train.csv' as a on b.id = a.id\" --format csv > clean_holdout.csv; peek --count-lines --lines 1:1 clean_holdout.csv | jsonq -p /data/total_lines --format text -")
step("cancho-ml", "Score on customers it never saw. The honest gain is smaller than the claim, but it is real.",
     f"echo \"production, clean holdout            $(ml eval --model-file prod/model.ml clean_holdout.csv --drop {CLEAN_DROP} | jsonq -p /data/metrics/accuracy --format text -)\"; "
     "echo \"candidate, full holdout (leaked)     $(ml eval --model-file cand.ml holdout.csv --drop id | jsonq -p /data/metrics/accuracy --format text -)\"; "
     "echo \"candidate, clean holdout             $(ml eval --model-file cand.ml clean_holdout.csv --drop id | jsonq -p /data/metrics/accuracy --format text -)\"")
step("cancho-ml", "Teammate's agent: retrained on the training file only, tracked. Reviewer: the run record can be replayed, and the clean holdout is the test.",
     "ml fit --model forest --task classification --target churned --drop id --track runs --output cand2.ml train.csv > fit3.json; R=$(jsonq -p /data/run/id --format text fit3.json | tr -d '\"'); "
     "echo \"replay verifies: $(ml runs verify runs $R | jsonq -p /data/verified --format text -)\"; echo \"clean holdout accuracy $(ml eval --model-file cand2.ml clean_holdout.csv --drop id | jsonq -p /data/metrics/accuracy --format text -)\"")
step("cancho-tools", "Promote it, guarded: the write only happens if production still holds the file the reviewer looked at.",
     "H=$(env hash --root prod model.ml --format text | cut -d' ' -f1); write --root prod --if-sha256 $H --stdin model.ml < cand2.ml > promote.json; echo \"promoted: $(jsonq -p /data/changed --format text promote.json), now $(jsonq -p /data/after_sha256 --format text promote.json)\"; echo $H > old_hash.txt")
step("cancho-tools", "Another agent, which read production before this promotion, tries to promote the original, leaked candidate. The write is refused, and says what the file holds now.",
     "write --root prod --if-sha256 $(cat old_hash.txt) --stdin model.ml < cand.ml > stale.json; jsonq -p /error/rule --format text stale.json; jsonq -p /error/detail/actual_sha256 --format text stale.json")
step("cancho-tools", "Reviewer: what may each tool do? The compilers proved it, and none of them reaches the network.",
     "for t in ml table stats write hash; do echo \"$t $(env $t introspect | jsonq -p /authority/effects --format text -)\"; done")


def acc(line):
    return float(line.split()[-1].strip('"'))


ev = steps[6]["out"].splitlines()
cmpd = json.loads((work / "cmp.json").read_text())["data"]["metrics"][0]
steps[6]["chart"] = {"type": "bars", "title": "Accuracy: the claim against what the review found", "short": "Accuracy (0 to 1)",
                     "labels": ["the claim (on training rows)", "candidate, holdout with the leak", "candidate, clean holdout", "production, clean holdout"],
                     "values": [float(cmpd["b"]), acc(ev[1]), acc(ev[2]), acc(ev[0])]}
(here / "session.json").write_text(json.dumps({
    "title": "Trust a model change you didn't write",
    "route": ["cancho-stats", "cancho-ml", "cancho-table", "cancho-ml", "cancho-tools"],
    "summary": "A teammate's agent retrains a model and claims a big gain. A reviewer who never reads the training code checks the claim with run records, a join on customer ids, a clean holdout and a guarded write.",
    "source": "A recorded run of the real tools, replayed, on synthetic data (examples/model-review/make_data.py): nothing here measures a real service.",
    "steps": steps}, indent=2, ensure_ascii=False) + "\n")
print("wrote session.json,", len(steps), "steps")
