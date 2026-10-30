#!/usr/bin/env python3
"""Generates stories.html from data/stories.json, which scripts/record_stories.py wrote by RUNNING the compiler and the three tools (table, stats, ml). The page draws every number, excerpt and figure from that file; the
narration is checked against it when the page is generated, so a sentence that stops being true stops the build.

    python3 scripts/gen_stories.py [--check]

`--check` regenerates in memory and fails if stories.html differs (CI runs it; CI does not have the four programs, which is why the recording is committed). scripts/storylib.py is the same file as in cancho-stats,
cancho-table and cancho-ml."""
import argparse
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from storylib import W, STORY_CSS, claim, pretty, num, esc, axis, svg, term, story, fig_hashes  # noqa: E402

PAGES = "https://alpibrusl.github.io/"


# ------------------------------------------------------------------------------------------------ figures
def fig_effects(auth):
    """what each tool's authority row lists, against the labels that would let a program reach the network or foreign code"""
    present = ["args", "conc", "dir_read", "dir_write", "err_write", "file_read", "file_write", "fs_read", "heap", "io_read", "io_write"]
    absent = ["net_out", "net_in", "ffi", "clock"]
    tools = ["table", "stats", "ml"]
    body = []
    x0 = 190
    for j, tname in enumerate(tools):
        body.append('<text class="nm" x="%g" y="24" text-anchor="middle">%s</text>' % (x0 + 90 + j * 130, tname))
    for i, e in enumerate(present + absent):
        y = 52 + i * 24
        if i == len(present):
            body.append('<line class="ax" x1="30" y1="%g" x2="%g" y2="%g"/>' % (y - 14, x0 + 90 + 2 * 130 + 40, y - 14))
        body.append('<text class="efl" x="%g" y="%g" text-anchor="end">%s</text>' % (x0 - 10, y, esc(e)))
        for j, tname in enumerate(tools):
            on = e in auth[tname]["effects"]
            cx = x0 + 90 + j * 130
            if on:
                body.append('<circle class="eff on" cx="%g" cy="%g" r="6"/>' % (cx, y - 4))
            else:
                body.append('<circle class="eff off" cx="%g" cy="%g" r="6"/>' % (cx, y - 4))
    body.append('<text class="tk" x="%g" y="%g">&#9679; the tool may do it &#183; &#9675; it may not</text>' % (30, 52 + (len(present) + len(absent)) * 24 + 10))
    return svg(52 + (len(present) + len(absent)) * 24 + 26, "\n".join(body), "The effects each tool may use, and the four it may not")


def fig_flow(steps):
    n = len(steps)
    bw = (W - 40 - (n - 1) * 34) / n
    body = ['<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="context-stroke"/></marker></defs>']
    for k, (title, sub, cls) in enumerate(steps):
        x = 20 + k * (bw + 34)
        body.append('<rect class="fbox %s" x="%g" y="20" width="%g" height="92" rx="10"/><text class="nm" x="%g" y="48" text-anchor="middle">%s</text>' % (cls, x, bw, x + bw / 2, esc(title)))
        for i, line in enumerate(sub):
            body.append('<text class="tk" x="%g" y="%g" text-anchor="middle">%s</text>' % (x + bw / 2, 70 + i * 16, esc(line)))
        if k < n - 1:
            body.append('<line class="arrow" x1="%g" y1="66" x2="%g" y2="66"/>' % (x + bw + 4, x + bw + 30))
    return svg(132, "\n".join(body), "A program, the compiler's refusal, the fix and the build")


def parse_hourly(csv):
    rows = [ln.split(",") for ln in csv.strip().split("\n")[1:]]
    return [(r[0], int(r[1]), r[2], int(r[3]), float(r[4])) for r in rows]


def fig_hourly(rows):
    days = sorted({r[0] for r in rows})
    ax, sx = axis(70, 610, 250, 0, 23, [0, 6, 12, 18, 23], "hour of the day", fmt=lambda v: "%d" % v)
    sy = lambda v: 230 - (v - 6) / 20 * 200
    body = [ax, '<line class="ax" x1="70" y1="30" x2="70" y2="250"/>']
    for t in (10, 15, 20, 25):
        body.append('<text class="tk" x="62" y="%g" text-anchor="end">%d</text>' % (sy(t) + 4, t))
    body.append('<text class="lb" x="16" y="140" transform="rotate(-90 16 140)" text-anchor="middle">hourly mean, &#176;C</text>')
    body.append('<rect class="night" x="70" y="30" width="%g" height="220"/><rect class="night" x="%g" y="30" width="%g" height="220"/>' % (sx(5.5) - 70, sx(19.5), 610 - sx(19.5)))
    shades = ["d1", "d2", "d3", "d4", "d5"]
    for k, d in enumerate(days):
        pts = sorted((r[1], r[4]) for r in rows if r[0] == d)
        body.append('<polyline class="ln %s" points="%s"/>' % (shades[k], " ".join("%g,%g" % (sx(h), sy(v)) for h, v in pts)))
    body.append('<text class="tk" x="610" y="22" text-anchor="end">five days, one line each (darker is later) &#183; shaded: the hours the logger calls night</text>')
    return svg(300, "\n".join(body), "Hourly mean temperature of the five days")


def fig_interval(est, lo_, hi_, xlo=0, xhi=9, ticks=(0, 2, 4, 6, 8), label="mean of the day hours minus mean of the night hours, °C", aria="The difference of day and night temperature with its 95% interval", zero="no difference"):
    ax, sx = axis(60, 610, 110, xlo, xhi, list(ticks), label)
    body = [ax, '<line class="zero" x1="%g" y1="30" x2="%g" y2="110"/><text class="tk" x="%g" y="24" text-anchor="middle">%s</text>' % (sx(0), sx(0), sx(0), zero)]
    body.append('<line class="ciline" x1="%g" y1="70" x2="%g" y2="70"/><line class="ciline" x1="%g" y1="62" x2="%g" y2="78"/><line class="ciline" x1="%g" y1="62" x2="%g" y2="78"/>' % (sx(lo_), sx(hi_), sx(lo_), sx(lo_), sx(hi_), sx(hi_)))
    body.append('<circle class="pt" cx="%g" cy="70" r="6"/><text class="tk" x="%g" y="56" text-anchor="middle">%.2f</text>' % (sx(est), sx(est), est))
    return svg(160, "\n".join(body), aria)


def fig_forecast(actual, forest, base):
    ax, sx = axis(70, 610, 250, 0, 23, [0, 6, 12, 18, 23], "hour of the last day (held out)", fmt=lambda v: "%d" % v)
    sy = lambda v: 230 - (v - 6) / 20 * 200
    body = [ax, '<line class="ax" x1="70" y1="30" x2="70" y2="250"/>']
    for t in (10, 15, 20, 25):
        body.append('<text class="tk" x="62" y="%g" text-anchor="end">%d</text>' % (sy(t) + 4, t))
    body.append('<line class="zero" x1="70" y1="%g" x2="610" y2="%g"/>' % (sy(base), sy(base)))
    body.append('<polyline class="ln la" points="%s"/>' % " ".join("%g,%g" % (sx(h), sy(v)) for h, v in forest))
    for h, v in actual:
        body.append('<circle class="dot pb" cx="%g" cy="%g" r="4"/>' % (sx(h), sy(v)))
    body.append('<text class="nm" x="90" y="46" style="fill:var(--accent)">forest</text><text class="nm" x="150" y="46" style="fill:var(--good)">&#9679; what the logger measured</text><text class="nm" x="360" y="46" style="fill:var(--bad)">- - the mean of the other days</text>')
    return svg(300, "\n".join(body), "The forest's prediction of the last day against the measurements")


STORY_EXTRA = """
:root { --term-dim: #8b95a5; --term-acc: #8ec0ff; --term-good: #5fd3a6; --term-bad: #ff9a92; }
header.top { position: sticky; top: 0; z-index: 5; background: color-mix(in srgb, var(--bg) 88%, transparent); backdrop-filter: blur(8px); border-bottom: 1px solid var(--line); }
header.top .wrap { display: flex; align-items: center; gap: 1.2rem; height: 3.4rem; }
header.top .brand { display: inline-flex; align-items: center; gap: .5rem; font: 700 1rem var(--mono); color: var(--fg); text-decoration: none; }
header.top nav { display: flex; gap: 1.1rem; margin-left: auto; flex-wrap: wrap; }
header.top nav a { color: var(--muted); text-decoration: none; font-size: .93rem; }
@media (max-width: 40rem) { header.top nav a.opt { display: none; } }
.hero { padding: 3.2rem 0 1.5rem; text-align: center; } .hero h1 { font-size: clamp(2rem, 6vw, 3.2rem); line-height: 1.1; margin: 0 auto 1rem; letter-spacing: -.03em; max-width: 20ch; }
.hero .sub { font-size: 1.15rem; color: var(--muted); max-width: 40rem; margin: 0 auto 1.4rem; }
section { margin: 0; padding: 3rem 0; } section.alt { background: var(--soft); }
h2 { font-size: clamp(1.4rem, 3vw, 1.9rem); margin: 0 0 .6rem; letter-spacing: -.02em; }
.lead { color: var(--muted); max-width: 40rem; margin: 0 auto 1.6rem; text-align: center; }
.term { background: var(--term-bg); color: var(--term-fg); border-radius: 12px; border: 1px solid var(--line); overflow: hidden; }
.term .bar { display: flex; align-items: center; gap: .4rem; padding: .55rem .8rem; border-bottom: 1px solid #1f2a30; font: .78rem var(--mono); color: var(--term-dim); }
.term .bar i { width: .7rem; height: .7rem; border-radius: 50%; background: #2c3a41; display: inline-block; }
.term pre { margin: 0; padding: 1rem 1.1rem; overflow-x: auto; font: .8rem/1.55 var(--mono); }
code { font: .9em var(--mono); background: var(--soft); padding: .1em .35em; border-radius: 5px; }
.ax { stroke: var(--muted); } .fig .ln.d1 { stroke: #9bbbe0; } .fig .ln.d2 { stroke: #6f9fd0; } .fig .ln.d3 { stroke: #4a82c0; } .fig .ln.d4 { stroke: #2b66a8; } .fig .ln.d5 { stroke: #16406e; }
.fig .night { fill: var(--ink); opacity: .08; } .fig .efl { fill: var(--fg); font: 12px var(--mono); }
.fig .eff.on { fill: var(--accent); } .fig .eff.off { fill: none; stroke: var(--muted); stroke-width: 1.5; }
.fig .fbox { fill: var(--surface); stroke-width: 2; } .fig .fbox.q { stroke: var(--accent); } .fig .fbox.r { stroke: var(--bad); } .fig .fbox.ok { stroke: var(--good); }
.fig .arrow { stroke: var(--muted); stroke-width: 1.8; marker-end: url(#ar); }
.fig .ln { fill: none; stroke-width: 2.2; } .fig .ln.la { stroke: var(--accent); stroke-width: 2.8; }
.fig .dot.pb { fill: var(--good); } .fig .zero { stroke: var(--bad); stroke-width: 1.5; stroke-dasharray: 5 4; }
.fig .ciline { stroke: var(--accent); stroke-width: 3; } .fig .pt { fill: var(--accent); }
.fig .hash { fill: var(--soft); stroke: var(--good); stroke-width: 1.5; } .fig .hx { fill: var(--fg); font: 12px var(--mono); }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); gap: 1rem; margin-top: 1.4rem; }
.card { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 1rem 1.1rem; }
.card h3 { margin: 0 0 .5rem; font-size: 1.02rem; } .card ul { margin: 0; padding-left: 1.1rem; } .card li { margin: .25rem 0; font-size: .94rem; }
"""


def build(data):
    P = data["pipeline"]
    S = []
    prog = data["programs"]
    # 1 ----------------------------------------------------------------------------------------------------
    claim("io_write" in prog["hello"]["authority"] and "the filesystem" in prog["hello"]["authority"] and "fs_read" in prog["fixed"]["authority"] and "the network" in prog["fixed"]["authority"], "story 1: the authority of the two programs")
    S.append(story(1, "A program says what it can touch", "the language", ["cancho authority"],
        "&#8220;Before I run anything: what can this program reach?&#8221;",
        ["<p>The compiler derives, from the source alone, what a program may do to the world, and prints it. The first program only writes to standard output. The second opens one file under <code>/tmp</code>, and says so. Neither can reach the network: the capability to do so was never handed to <code>main</code>, so there is nothing to reach with.</p>",
         term("cancho authority hello.cho --std", prog["hello"]["authority"]),
         term("cancho authority fixed.cho --std", prog["fixed"]["authority"]),
         '<div class="read"><b>Reading it.</b> The first program performs <code>io_write</code> and &#8220;never touches the filesystem, the network, the heap&#8221;. The second adds <code>fs_read("/tmp")</code> and nothing else. These are statements about every possible run of the program, not about a test run, and the compiler is the one that makes them.</div>']))
    # 2 ----------------------------------------------------------------------------------------------------
    claim(prog["leak"]["check_exit"] != 0 and "still live" in prog["leak"]["check_out"], "story 2: the compiler refuses the program that does not close its file")
    S.append(story(2, "The compiler says no", "the language", ["cancho check"],
        "&#8220;I opened a file and forgot to close it. Does it matter?&#8221;",
        ["<p>A resource that is opened has to be consumed. The program below opens a file and never closes it; the compiler does not warn, it refuses, and it names the value and the line.</p>",
         term("cancho check leak.cho --std", "exit %d\n%s" % (prog["leak"]["check_exit"], prog["leak"]["check_out"])),
         fig_flow([("leak.cho", ["opens a file,", "never closes it"], "q"), ("the compiler", ["refuses", "exit %d" % prog["leak"]["check_exit"]], "r"), ("fixed.cho", ["file_close(f)"], "ok"), ("the program", ["builds and runs"], "ok")]),
         '<div class="read"><b>Reading it.</b> The error is about a value, <code>f</code>, that is still live at the end of its block. Fixing it is one line (<code>file_close(f)</code>), and the fixed program is the one whose authority you read in story 1. Everything below is built from programs that compile under rules like this one.</div>']))
    # 3 ----------------------------------------------------------------------------------------------------
    auth = data["authority"]
    for name in ("table", "stats", "ml"):
        claim(not ({"net_out", "net_in", "ffi", "clock"} & set(auth[name]["effects"])) and auth[name]["bounded"] and auth[name]["foreign_symbols"] == [], "story 3: %s has no network, no foreign code and no clock" % name)
    claim("io_read" in auth["table"]["effects"] and "io_read" not in auth["stats"]["effects"] and "file_write" in auth["ml"]["effects"] and "file_write" not in auth["table"]["effects"] and "file_write" not in auth["stats"]["effects"], "story 3: only ml writes files; stats has no standard input")
    S.append(story(3, "Three tools, three authorities", "the tools", ["table", "stats", "ml"],
        "&#8220;I am going to feed my data to three command-line tools. What may each of them do with it?&#8221;",
        ["<p>The three tools are written in cancho, so each one has an authority row, derived by the compiler and committed in its repository (<code>manifests/*.authority.json</code>); CI fails if the built program differs from it. Here they are side by side.</p>",
         fig_effects(auth),
         '<div class="read"><b>Reading it.</b> None of the three can open a network connection, call foreign code or read a clock. <code>table</code> may read standard input and use threads; <code>stats</code> needs neither; only <code>ml</code> may write files (the model it fits). The rows are the committed manifests, read when this page was recorded; their SHA-256 begin %s (table), %s (stats) and %s (ml).</div>' % (auth["table"]["sha256"][:10], auth["stats"]["sha256"][:10], auth["ml"]["sha256"][:10])]))
    # 4 ----------------------------------------------------------------------------------------------------
    rows = parse_hourly(P["table"]["csv"])
    claim(len(rows) == 120 and all(r[3] == 12 for r in rows), "story 4: five days of 24 hours with 12 readings each")
    t2 = P["stats"]["t2"]["tests"][0]
    ci = P["stats"]["ci"]["intervals"][0]["interval"]
    claim(P["stats"]["t2"]["levels"] == {"a": "day", "b": "night"} and t2["p_value"] < 1e-3 and ci["low"] > 0, "story 4: the day hours are warmer than the night hours, p below 0.001, the interval above zero")
    ef, ec = P["ml"]["eval_f"]["metrics"], P["ml"]["eval_c"]["metrics"]
    rmse_f, rmse_c = float(ef["rmse"]), float(ec["rmse"])
    claim(rmse_f < rmse_c / 2, "story 4: the forest has less than half the error of the mean")
    test_rows = parse_hourly(P["test_csv"])
    actual = sorted((r[1], r[4]) for r in test_rows)
    pred_by_row = list(zip([r[1] for r in test_rows], P["ml"]["predictions"]))
    forest = sorted(pred_by_row)
    base = float(ec["prediction"])
    claim(len(actual) == 24 and len(forest) == 24, "story 4: 24 hours held out")
    t_args = ["table"] + P["table"]["args"]
    S.append(story(4, "One logger, three tools", "the pipeline", ["table", "stats", "ml"],
        "&#8220;The logger in the hut writes a reading every five minutes, as JSON lines. Is it colder at night? And can a model tell me tomorrow&#8217;s temperatures?&#8221; &#8212; the keeper of a mountain hut",
        ["<p>Five days of readings, 1,440 lines (<a href=\"demo/stories/logger.jsonl\">demo/stories/logger.jsonl</a>). First <code>table</code> turns them into one row per hour, with the mean computed from exact decimals; its CSV is the input of the other two. <code>stats</code> compares the day hours with the night hours; <code>ml</code> learns the daily cycle from the first four days and predicts the fifth.</p>",
         term(" ".join(t_args + ["> hourly.csv"]).replace("table --input", "table --input"), "day,hour,period,count,mean:temp_c\n" + "\n".join(P["table"]["csv"].strip().split("\n")[1:5]) + "\n...  (120 rows)"),
         fig_hourly(rows),
         term("stats " + " ".join(P["stats"]["args_ci"]) + " hourly.csv", pretty({"levels": P["stats"]["ci"]["levels"], "intervals": [{"column": "mean:temp_c", "estimate": ci["estimate"], "interval": {k: ci[k] for k in ("low", "high", "level")}}]})),
         fig_interval(ci["estimate"], ci["low"], ci["high"]),
         term("ml " + " ".join(P["ml"]["fit_forest"][:4] + ["..."] + P["ml"]["fit_forest"][-2:]), pretty({"model": "forest", "rows": P["ml"]["forest"]["rows"], "sha256": P["ml"]["forest"]["sha256"]})),
         term("ml eval ...  (constant, then forest)", pretty({"constant": ec, "forest": ef})),
         fig_forecast(actual, forest, base),
         '<div class="read"><b>Reading it.</b> The day hours are %s &#176;C warmer than the night hours on average, with a 95%% interval from %s to %s (<code>test t2</code> says p = %s). On the fifth day, which the model never saw, the forest is wrong by %s &#176;C (root mean square) where the mean of the other days is wrong by %s: it learnt the daily cycle. Three programs, three authorities, one CSV between them.</div>' % (num(ci["estimate"], 3), num(ci["low"], 3), num(ci["high"], 3), "{:.1e}".format(t2["p_value"]), num(rmse_f, 3), num(rmse_c, 3))]))
    # 5 ----------------------------------------------------------------------------------------------------
    d0, d1, d2 = P["digests"], data["pipeline_shuffled_digests"], data["pipeline_reversed_digests"]
    claim(d0 == d1 == d2, "story 5: the artefacts of the pipeline are the same bytes whatever the order of the logger's lines")
    hr = []
    for label, d in (("as logged", d0), ("lines shuffled", d1), ("lines reversed", d2)):
        for k in ("hourly.csv", "stats test t2", "ml model file"):
            hr.append(("%s: %s" % (label, k), d[k][:48]))
    S.append(story(5, "The same bytes, in any order", "determinism", ["table", "stats", "ml"],
        "&#8220;I merged two loggers&#8217; files and the lines are in another order. Will the answers change?&#8221;",
        ["<p>The whole pipeline of story 4 again, three times: the logger&#8217;s lines in the order they were written, shuffled, and reversed. For each run, the SHA-256 of the hourly CSV, of the statistics document and of the fitted model file:</p>",
         fig_hashes(hr),
         '<div class="read"><b>Reading it.</b> Nine digests, three distinct values, each repeated three times: the order of the lines changes nothing. The means are exact decimals, so adding them in another order cannot change a digit; the groups come out sorted by key; the forest&#8217;s trees draw from streams derived from a seed. (A bootstrap, by design, is a function of the file&#8217;s bytes and its seed: row order <em>does</em> matter there, and the answer says so.)</div>']))
    # 6 marketing ----------------------------------------------------------------------------------------------
    C = data["campaign"]
    tot = [r.split(",") for r in C["table"]["csv_totals"].strip().split("\n")]
    exp = [r.split(",") for r in C["table"]["csv_export"].strip().split("\n")]
    buyers = {r[0]: int(r[2]) for r in tot[1:]}
    exported = {r[0]: int(r[2]) for r in exp[1:]}
    claim(buyers == exported and set(buyers) == {"ads", "holdout"}, "story 6: the buyers counted from the purchases are the buyers of the experiment tool's export, in each arm")
    ci6 = C["stats"]["ci"]["intervals"][0]
    tp6 = C["stats"]["test"]["tests"][0]
    claim(ci6["interval"]["low"] > 0 and tp6["p_value"] < 0.01 and ci6["levels"] == {"a": "ads", "b": "holdout"}, "story 6: the lift is positive, its interval excludes zero and the test is below 0.01")
    c0, c1, c2 = C["digests"], data["campaign_shuffled_digests"], data["campaign_reversed_digests"]
    claim(c0 == c1 == c2, "story 6: the totals and the statistics are the same bytes whatever the order of the purchases and of the users")
    ch = []
    for label, d in (("as exported", c0), ("shuffled", c1), ("reversed", c2)):
        for k in ("totals", "stats ci prop"):
            ch.append(("%s: %s" % (label, k), d[k][:48]))
    S.append(story(6, "Did the campaign work, and can finance check it?", "marketing", ["table", "stats"],
        "&#8220;Finance counts buyers from the purchase ledger, the growth team counts them from the experiment tool. Do they agree, and is the lift real?&#8221; &#8212; the analyst who has to sign the report",
        ["<p>Two sources, one question. <code>table</code> joins the shop&#8217;s purchases to the arm of each user, leaves out what was bought before the campaign started (a <code>--where</code> on the date), and counts distinct buyers and the exact revenue per arm. The experiment tool&#8217;s export has one row per user with a 0 or 1; <code>table</code> adds that column up. If the two ledgers differ by one buyer, the report does not go out.</p>",
         term("table " + " ".join(C["table"]["args_totals"]) + " " + C["table"]["file_totals"], C["table"]["csv_totals"].rstrip("\n")),
         term("table " + " ".join(C["table"]["args_export"]) + " " + C["table"]["file_export"], C["table"]["csv_export"].rstrip("\n")),
         "<p>They agree, arm by arm. Now the experiment itself, with the export as input: the difference in conversion between the arm shown the ad and the held-out arm, with its interval (the Newcombe one, for a difference of two proportions), and the test.</p>",
         term("stats " + " ".join(C["stats"]["args_ci"]) + " users.csv", pretty({"estimate": ci6["estimate"], "interval": {k: ci6["interval"][k] for k in ("method", "low", "high")}})),
         term("stats " + " ".join(C["stats"]["args_test"]) + " users.csv", pretty({k: tp6[k] for k in ("statistic", "p_value", "p_method")})),
         fig_interval(ci6["estimate"] * 100, ci6["interval"]["low"] * 100, ci6["interval"]["high"] * 100, -1, 3, (-1, 0, 1, 2, 3), "extra buyers per 100 users shown the ad (95% interval)", "The difference in conversion with its 95% interval", "no effect"),
         '<p>And for the file that goes to finance: the SHA-256 of the exact totals and of the statistics document, with the purchases in the order exported, shuffled, and reversed (with the users reversed as well):</p>',
         fig_hashes(ch),
         '<div class="read"><b>Reading it.</b> Both counts of buyers agree: %d in the arm shown the ad and %d in the held-out arm. The ad adds %s points of conversion (95%% interval %s to %s, p = %s). Six digests, two distinct values, each repeated three times: another order of the same rows is the same report, byte for byte. The cancho-stats page goes on to revenue, to the dashboard that overstates the lift, and to a regional experiment; cancho-ml to who the ad moves.</div>' % (buyers["ads"], buyers["holdout"], num(ci6["estimate"] * 100, 2), num(ci6["interval"]["low"] * 100, 2), num(ci6["interval"]["high"] * 100, 2), num(tp6["p_value"], 3))]))
    # the tour -----------------------------------------------------------------------------------------------
    cards = [("Biology", [("stats", "Six mice against six", "exact rank and permutation tests"), ("table", "A growth plate", "exact means of replicates"), ("ml", "Tumour or normal?", "which genes matter")]),
             ("Chemistry", [("stats", "Two methods, one sample set", "correlation is not agreement"), ("table", "Burette readings", "a declared precision"), ("ml", "A calibration curve", "fit once, apply to unknowns")]),
             ("Physics", [("stats", "Same source, two detectors", "a shape the means cannot see"), ("table", "Two days of a logger", "JSON lines by the hour"), ("ml", "Two kinds of pulse", "clusters with no labels")]),
             ("Social science", [("stats", "What does the town think?", "intervals for a share, ordinal tests"), ("table", "Who answered twice?", "counts and duplicates"), ("ml", "Who supports the tram line?", "a model to read")])]
    html_cards = []
    for field, items in cards:
        lis = "".join('<li><a href="%scancho-%s/stories.html">%s</a>: %s <span style="color:var(--muted)">(%s)</span></li>' % (PAGES, t_, esc(title), esc(sub), t_) for t_, title, sub in items)
        html_cards.append('<div class="card"><h3>%s</h3><ul>%s</ul></div>' % (field, lis))
    S.append('<section class="alt story" id="s7"><div class="wrap"><h2>7 &middot; From the sciences</h2><div class="badge"><span class="lvl">go further</span></div><p>Each of the three tools has its own page of stories, in increasing complexity, with a figure for each and a section from biology, chemistry, physics and the social sciences. Every number on them is drawn from a real run, like the ones above.</p><div class="cards">%s</div></div></section>' % "".join(html_cards))
    return S


def page(sections):
    nav = " ".join('<a class="opt" href="#s%d">%d</a>' % (i, i) for i in range(1, 8))
    toc = "".join('<a href="#s%d">%d &middot; %s</a>' % (i, i, esc(nm)) for i, nm in enumerate(("Authority", "A refusal", "Three tools", "A pipeline", "Same bytes", "Campaign", "Sciences"), 1))
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>cancho: seven stories across the ecosystem</title>
<meta name="description" content="Seven end-to-end examples across cancho, table, stats and ml, in increasing complexity: what a program can touch, a refusal, three tools in a row, the same bytes in any order, and a marketing campaign checked by two ledgers. Every number is drawn from a real run.">
<meta name="color-scheme" content="light dark">
<link rel="stylesheet" href="assets/site.css">
<style>%s%s</style>
</head>
<body>
<header class="top"><div class="wrap">
  <a class="brand" href="./"><img src="logo-mark.png" width="28" height="28" alt="">cancho</a>
  <nav>%s<a href="./">Home</a><a href="https://github.com/alpibrusl/cancho">GitHub</a></nav>
</div></header>
<div class="wrap hero">
  <h1>Seven stories across the ecosystem.</h1>
  <p class="sub">From what a program can touch, to a refusal by the compiler, to three tools passing one CSV along a pipe and giving the same bytes in any order. Every number and every figure comes from a real run, recorded by <code>scripts/record_stories.py</code> and drawn by <code>scripts/gen_stories.py</code>; the data are invented and the narration is checked against the numbers.</p>
  <div class="toc">%s</div>
</div>
%s
<footer><div class="wrap" style="text-align:center;padding:1.5rem 0 2rem;color:var(--muted)">cancho &middot; <a href="./">home</a> &middot; the data are invented; the runs, the digits and the figures are real</div></footer>
</body>
</html>
""" % (STORY_CSS, STORY_EXTRA, nav, toc, "\n".join(sections))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    data = json.loads((ROOT / "data" / "stories.json").read_text())
    text = page(build(data))
    out = ROOT / "stories.html"
    if a.check:
        if not out.exists() or out.read_text() != text:
            print("gen_stories: stories.html is stale")
            return 1
        print("gen_stories: up to date")
        return 0
    out.write_text(text)
    print("gen_stories: wrote stories.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
