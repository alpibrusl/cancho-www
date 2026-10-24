#!/usr/bin/env python3
"""Run the per-project map demos for real and write data/demos.json (the map plays it back; it never invents output).

    python3 scripts/record_demos.py <cancho-binary> <cancho-ui-binary> <path-to-a-cancho-ui-checkout> [<session.json of a trail>...]

A trail is a session recorded by an example (examples/<name>/record.py) that visits several rocks; it
is copied in as `trail:<name>`.

A project with no entry has no recorded session yet, and the map says so. Run again after a change to what the commands print.
"""
import json, os, pathlib, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
cancho, cui, ui_repo = (pathlib.Path(a).resolve() for a in sys.argv[1:4])


def run(cmd, cwd, env):
    r = subprocess.run(["bash", "-c", cmd], cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=120)
    return r.stdout.rstrip("\n")


def session(files, steps, bins):
    work = pathlib.Path(tempfile.mkdtemp())
    try:
        (work / "bin").mkdir()
        for name, src in bins.items():
            (work / "bin" / name).symlink_to(src)
        for dst, src in files.items():
            shutil.copy(src, work / dst)
        env = dict(os.environ, PATH=f"{work / 'bin'}:{os.environ['PATH']}")
        out = []
        for note, cmd in steps:
            out.append({"note": note, "cmd": cmd, "out": run(cmd, work, env)})
        return out
    finally:
        shutil.rmtree(work)


(pathlib.Path("/tmp/notes.txt")).write_text("some notes\n")
clock = (ui_repo / "examples" / "clock" / "clock.cui").read_text()
bad = "\n".join(l for l in clock.splitlines() if l.strip() != "requires Clock;") + "\n"
tmp = pathlib.Path(tempfile.mkdtemp())
(tmp / "clock_bad.cui").write_text(bad)

demos = {
    "cancho": {
        "title": "A leaked file, refused by name",
        "steps": session(
            {"leak.cho": ROOT / "demo/src/leak.cho", "fixed.cho": ROOT / "demo/src/fixed.cho"},
            [
                ("It opens a file and never closes it. The compiler refuses:", "cancho check leak.cho --std"),
                ("The refusal is data an agent can match on:", 'cancho check leak.cho --std --output json | grep \'"rule"\''),
                ("One added line fixes it, and the program may now run:", "diff leak.cho fixed.cho; cancho build fixed.cho --std -o notes && ./notes"),
                ("What may it do? The types say:", "cancho authority fixed.cho --std"),
            ],
            {"cancho": cancho},
        ),
    },
    "cancho-ui": {
        "title": "A component that asks for the clock",
        "steps": session(
            {"clock.cui": ui_repo / "examples/clock/clock.cui", "clock_bad.cui": tmp / "clock_bad.cui"},
            [
                ("Delete `requires Clock;` and the compiler refuses:", "cancho-ui check clock_bad.cui; echo \"exit $?\""),
                ("With the declaration it is accepted:", "cancho-ui check clock.cui; echo \"exit $?\""),
                ("Ask what it may reach, as data:", "cancho-ui inspect effects clock.cui Clock | grep '\"capability\"'"),
            ],
            {"cancho-ui": cui},
        ),
    },
}
shutil.rmtree(tmp)
for extra in sys.argv[4:]:
    path = pathlib.Path(extra).resolve()
    trail = json.loads(path.read_text())
    demos["trail:" + path.parent.name] = {
        "title": trail["title"],
        "route": trail["route"],
        "summary": trail["summary"],
        "source": trail["source"],
        "steps": trail["steps"],
    }
(ROOT / "data" / "demos.json").write_text(json.dumps(demos, indent=2, ensure_ascii=False) + "\n")
print("wrote data/demos.json:", ", ".join(demos))
