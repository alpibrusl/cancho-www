#!/usr/bin/env python3
"""Runs the stories of the ecosystem page for real and writes data/stories.json and demo/stories/logger.jsonl; scripts/gen_stories.py draws the page from them and never invents output.

    python3 scripts/record_stories.py <cancho> <table> <stats> <ml> <checkout of cancho-table> <checkout of cancho-stats> <checkout of cancho-ml>

The four programs are the built binaries, the three checkouts are read for the authority manifests they commit (manifests/*.authority.json). The data are invented (a seeded generator below); the runs are real. Run again after a
change to what the commands print, and commit both files. Nothing here is checked in CI, because CI does not have the four programs; the generator is."""
import hashlib
import json
import math
import pathlib
import random
import subprocess
import sys
import tempfile
import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
cancho, table, stats, ml, table_repo, stats_repo, ml_repo = (pathlib.Path(a).resolve() for a in sys.argv[1:8])


def run(argv, cwd, check=True):
    p = subprocess.run([str(a) for a in argv], cwd=cwd, capture_output=True, text=True, timeout=300)
    if check and p.returncode != 0:
        raise SystemExit("record_stories: `%s` exited %d: %s" % (" ".join(map(str, argv)), p.returncode, (p.stdout + p.stderr)[:400]))
    return p


def logger(seed=52):
    """five days of a temperature logger in a mountain hut, a reading every five minutes, as JSON lines; the hut warms by 0.4 degrees a day"""
    r = random.Random(seed)
    t0 = datetime.datetime(2026, 3, 2)
    lines = []
    for i in range(5 * 288):
        ts = t0 + datetime.timedelta(minutes=5 * i)
        temp = 14 + 0.4 * (i // 288 + 1) + 6 * math.sin((ts.hour + ts.minute / 60 - 9) / 24 * 2 * math.pi) + r.gauss(0, 0.5)
        period = "night" if ts.hour < 6 or ts.hour >= 20 else "day"
        lines.append(json.dumps({"ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ"), "day": "d%d" % (i // 288 + 1), "hour": ts.hour, "period": period, "temp_c": round(temp, 2)}))
    return lines


def pipeline(lines, work):
    """the three tools on one logger file; answers every artefact the page shows"""
    (work / "logger.jsonl").write_text("\n".join(lines) + "\n")
    out = {}
    t = [table, "--root", work]
    a1 = ["--input-format", "jsonl", "--fields", "day,hour,period,temp_c", "--group", "day,hour,period", "--agg", "count,mean:temp_c:dec(2)@4", "--sort", "day", "--format", "csv", "logger.jsonl"]
    hourly = run(t + a1, work).stdout
    (work / "hourly.csv").write_text(hourly)
    out["table"] = {"args": a1[:-3] + ["--format", "csv"], "file": "logger.jsonl", "csv": hourly}
    s1 = ["--cols", "mean:temp_c", "--group", "period"]
    t2 = run([stats, "test", "t2"] + s1 + ["--root", work, "hourly.csv"], work).stdout
    cd = run([stats, "ci", "diff"] + s1 + ["--root", work, "hourly.csv"], work).stdout
    out["stats"] = {"args_t2": ["test", "t2"] + s1, "args_ci": ["ci", "diff"] + s1, "t2": json.loads(t2)["data"], "ci": json.loads(cd)["data"], "raw": t2 + cd}
    tr = run(t + ["--where", "day != d5", "--format", "csv", "hourly.csv"], work).stdout
    te = run(t + ["--where", "day = d5", "--format", "csv", "hourly.csv"], work).stdout
    (work / "train.csv").write_text(tr)
    (work / "test.csv").write_text(te)
    m = [ml, "--root", work]
    common = ["--drop", "day,count,period", "--target", "mean:temp_c"]
    fit_c = ["fit", "--model", "constant"] + common + ["--output", "base.ml", "train.csv"]
    fit_f = ["fit", "--model", "forest", "--task", "regression", "--trees", "60", "--max-depth", "6", "--seed", "1"] + common + ["--output", "forest.ml", "train.csv"]
    dc = json.loads(run(m + fit_c, work).stdout)["data"]
    df = json.loads(run(m + fit_f, work).stdout)["data"]
    ev_c = ["eval", "--model-file", "base.ml", "--drop", "day,count,period", "test.csv"]
    ev_f = ["eval", "--model-file", "forest.ml", "--drop", "day,count,period", "test.csv"]
    ec = json.loads(run(m + ev_c, work).stdout)["data"]
    ef = json.loads(run(m + ev_f, work).stdout)["data"]
    pr = json.loads(run(m + ["predict", "--model-file", "forest.ml", "--drop", "day,count,period", "--limit", "100", "test.csv"], work).stdout)["data"]["rows"]
    out["ml"] = {"fit_forest": fit_f, "eval_forest": ev_f, "eval_constant": ev_c, "forest": {"rows": df["rows"], "sha256": df["sha256"]}, "constant": {"rows": dc["rows"]}, "eval_f": ef, "eval_c": ec, "predictions": [float(x[0]) for x in pr]}
    out["test_csv"] = te
    out["digests"] = {
        "hourly.csv": hashlib.sha256(hourly.encode()).hexdigest(),
        "stats test t2": hashlib.sha256(t2.encode()).hexdigest(),
        "ml model file": df["sha256"],
        "ml eval": hashlib.sha256(json.dumps(ef, sort_keys=True).encode()).hexdigest(),
    }
    return out


def campaign(users, purchases, work):
    """the autumn campaign: the experiment tool's per-user export, the shop's purchases; the answers every artefact the page shows"""
    out = {}
    (work / "users.csv").write_text("user_id,arm,bought\n" + "".join("%d,%s,%d\n" % u for u in users))
    (work / "purchases.csv").write_text("purchase_id,user_id,date,amount\n" + "".join("%d,%d,%s,%s\n" % p for p in purchases))
    (work / "arms.csv").write_text("user_id,arm\n" + "".join("%d,%s\n" % (u[0], u[1]) for u in users))
    t = [table, "--root", work]
    a1 = ["--join", "arms.csv", "--on", "user_id", "--where", "date:date >= 2026-09-01", "--group", "arm", "--agg", "count,distinct:user_id,sum:amount:dec(2)", "--sort", "arm", "--format", "csv", "purchases.csv"]
    a2 = ["--group", "arm", "--agg", "count,sum:bought", "--sort", "arm", "--format", "csv", "users.csv"]
    tot = run(t + a1, work).stdout
    exp = run(t + a2, work).stdout
    out["table"] = {"args_totals": a1[:-1], "file_totals": "purchases.csv", "csv_totals": tot, "args_export": a2[:-1], "file_export": "users.csv", "csv_export": exp}
    s1 = ["--cols", "bought", "--success", "1", "--group", "arm"]
    ci = run([stats, "ci", "prop"] + s1 + ["--root", work, "users.csv"], work).stdout
    tp = run([stats, "test", "prop"] + s1 + ["--root", work, "users.csv"], work).stdout
    out["stats"] = {"args_ci": ["ci", "prop"] + s1, "args_test": ["test", "prop"] + s1, "ci": json.loads(ci)["data"], "test": json.loads(tp)["data"]}
    out["digests"] = {"totals": hashlib.sha256(tot.encode()).hexdigest(), "export": hashlib.sha256(exp.encode()).hexdigest(), "stats ci prop": hashlib.sha256(ci.encode()).hexdigest(), "stats test prop": hashlib.sha256(tp.encode()).hexdigest()}
    return out


def campaign_data(seed=11):
    """8000 users, alternately shown the ads or held out; 6.2% and 5.0% buy in September; some bought in August too (before the start)"""
    r = random.Random(seed)
    users, purchases = [], []
    pid = 0
    for u in range(1, 8001):
        arm = "ads" if u % 2 == 0 else "holdout"
        bought = 0
        if r.random() < (0.062 if arm == "ads" else 0.05):
            bought = 1
            for _ in range(1 + (r.random() < 0.15)):
                pid += 1
                purchases.append((pid, u, "2026-09-%02d" % r.randint(1, 28), "%.2f" % r.lognormvariate(3.7, 0.6)))
        if r.random() < 0.03:
            pid += 1
            purchases.append((pid, u, "2026-08-%02d" % r.randint(1, 31), "%.2f" % r.lognormvariate(3.7, 0.6)))
        users.append((u, arm, bought))
    purchases.sort(key=lambda p: (p[2], p[0]))
    return users, [(i,) + p[1:] for i, p in enumerate(purchases, 1)]


def main():
    work = pathlib.Path(tempfile.mkdtemp())
    (work / "bin").mkdir()
    lines = logger()
    result = {"generated_by": "scripts/record_stories.py", "pipeline": pipeline(lines, work)}
    # the same readings in another order of the file
    shuffled = list(lines)
    random.Random(3).shuffle(shuffled)
    work2 = pathlib.Path(tempfile.mkdtemp())
    result["pipeline_shuffled_digests"] = pipeline(shuffled, work2)["digests"]
    reversed_ = list(reversed(lines))
    work3 = pathlib.Path(tempfile.mkdtemp())
    result["pipeline_reversed_digests"] = pipeline(reversed_, work3)["digests"]
    # the programs
    progs = {}
    hello = (ROOT / "demo" / "src" / "hello.cho").read_text()
    for name in ("hello", "fixed", "leak"):
        src = ROOT / "demo" / "src" / ("%s.cho" % name)
        entry = {"source": src.read_text()}
        a = run([cancho, "authority", src, "--std"], work, check=False)
        entry["authority"] = a.stdout.strip()
        c = run([cancho, "check", src, "--std"], work, check=False)
        entry["check_exit"] = c.returncode
        entry["check_out"] = (c.stdout + c.stderr).replace(str(src), "%s.cho" % name).strip()
        progs[name] = entry
    result["programs"] = progs
    users, purchases = campaign_data()
    result["campaign"] = campaign(users, purchases, pathlib.Path(tempfile.mkdtemp()))
    sp = list(purchases)
    random.Random(4).shuffle(sp)
    result["campaign_shuffled_digests"] = campaign(users, sp, pathlib.Path(tempfile.mkdtemp()))["digests"]
    sp.reverse()
    result["campaign_reversed_digests"] = campaign(list(reversed(users)), sp, pathlib.Path(tempfile.mkdtemp()))["digests"]
    # what each tool can touch: the manifests they commit
    auth = {}
    for name, repo in (("table", table_repo), ("stats", stats_repo), ("ml", ml_repo)):
        d = json.loads((repo / "manifests" / ("%s.authority.json" % name)).read_text())
        auth[name] = {"effects": d["effects"], "bounded": d["bounded"], "foreign_symbols": d["foreign_symbols"], "sha256": hashlib.sha256((repo / "manifests" / ("%s.authority.json" % name)).read_bytes()).hexdigest()}
    result["authority"] = auth
    (ROOT / "demo" / "stories").mkdir(exist_ok=True)
    (ROOT / "demo" / "stories" / "logger.jsonl").write_text("\n".join(lines) + "\n")
    (ROOT / "data" / "stories.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print("record_stories: wrote data/stories.json and demo/stories/logger.jsonl")


main()
