#!/usr/bin/env python3
"""Run the ship-an-api story for real and write session.json: each step's command and what it printed.

    python3 record.py --web DIR --schema DIR --compiler-checkout DIR --compiler BIN --clientgen BIN --oci DIR \\
                      --table DIR --stats DIR --tools DIR

--web is a cancho-web checkout (it is copied, so the edit step does not touch it), --schema a cancho-schema checkout,
--compiler-checkout and --compiler the cancho compiler cancho-web pins (a checkout, for its packages, and the binary),
--clientgen the cancho-client-gen binary built the way its CI builds it, --oci a built cancho-oci (build/oci-build and
scripts/static-cc), and --table, --stats, --tools built cancho-table, cancho-stats and cancho-tools.

The story: build a service whose whole contract is one declaration, generate a client from its own OpenAPI document, let an
app use it, analyse what the app generated, change the contract, and package the service as a reproducible image. Everything
is a cancho tool except `curl` (the caller) and app.py (the customer: a stand-in for whatever uses the service).
"""
import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

here = pathlib.Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
for a in ("web", "schema", "compiler-checkout", "compiler", "clientgen", "oci", "table", "stats", "tools"):
    ap.add_argument("--" + a, required=True)
args = ap.parse_args()
d = {k: pathlib.Path(v).resolve() for k, v in vars(args).items()}
work = pathlib.Path(tempfile.mkdtemp())
(work / "bin").mkdir()
for name, src in (("table", d["table"] / "build/table"), ("stats", d["stats"] / "build/stats"), ("clientgen", d["clientgen"]),
                  ("oci-build", d["oci"] / "build/oci-build"), ("jsonq", d["tools"] / "build/jsonq"), ("seek", d["tools"] / "build/seek"),
                  ("replace", d["tools"] / "build/replace"), ("cancho", d["compiler"])):
    (work / "bin" / name).symlink_to(src)
shutil.copy(d["oci"] / "scripts/static-cc", work / "bin/static-cc")
os.chmod(work / "bin/static-cc", 0o755)
shutil.copytree(d["web"], work / "cancho-web", ignore=shutil.ignore_patterns("build", ".git"))
shutil.copy(here / "app.py", work / "app.py")
env = dict(os.environ, PATH=f"{work / 'bin'}:{os.environ['PATH']}", CANCHO=str(d["compiler"]),
           CANCHO_DIR=str(d["compiler_checkout"]), SCHEMA_DIR=str(d["schema"]))
steps, servers = [], []
PORT = 18950


def run(cmd):
    r = subprocess.run(["bash", "-c", cmd], cwd=work, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=600)
    return r.stdout.rstrip("\n")


def serve(binary):
    for s in servers:
        s.terminate()
        s.wait(timeout=10)
    servers.clear()
    (work / "serve.log").write_text("")
    p = subprocess.Popen(["bash", "-c", f"exec ./{binary} {PORT} 2> serve.log"], cwd=work, env=env, stdout=subprocess.DEVNULL)
    servers.append(p)
    for _ in range(50):
        if "listening" in (work / "serve.log").read_text():
            return
        time.sleep(0.1)
    raise SystemExit("the service did not start")


def step(at, note, cmd):
    steps.append({"at": at, "note": note, "cmd": cmd, "out": run(cmd)})


def record(at, note, cmd, out):
    steps.append({"at": at, "note": note, "cmd": cmd, "out": out})


J = "-H 'Content-Type: application/json'"
URL = f"localhost:{PORT}"
try:
    build = run("(cd cancho-web && scripts/build.sh examples/users/users.cho ../users-v1)")
    serve("users-v1")
    record("cancho-web", "Build the service from its one declaration (routes, bodies, errors), and start it. The compiler is the revision cancho-web pins.",
           f"(cd cancho-web && scripts/build.sh examples/users/users.cho ../users-v1); ./users-v1 {PORT} 2> serve.log &  curl -s {URL}/health",
           (build + "\n" + run(f"curl -s {URL}/health")).strip())
    step("cancho-web", "A bad request is refused with every error at once, each with its JSON Pointer, as problem+json.",
         f"curl -s -XPOST {J} -d '{{\"name\":\"\",\"age\":151}}' {URL}/users > refusal.json; for p in /count /errors/0 /errors/1; do jsonq -p $p --format text refusal.json; done")
    step("cancho-web", "The OpenAPI 3.1 document comes from the same declaration, so a route cannot be served and undocumented.",
         f"curl -s {URL}/openapi.json > openapi.json; jsonq -p /paths --keys --format text openapi.json")
    step("cancho-client-gen", "Frontend: a typed client from the server's own document. clientgen reads it, lists what it found, and writes Python.",
         "clientgen openapi.json --check; clientgen openapi.json --model | head -3; clientgen openapi.json --python -o client.py")
    step("cancho-client-gen", "The client's annotations promise a dataclass. Does it return one? (A read-only call, so the service stays empty. An earlier build of clientgen returned a plain dict here; that is fixed in cancho-client-gen#15.)",
         f"seek --format text 'def listUsers' client.py; python3 -c \"import client; r = client.Client('http://127.0.0.1:{PORT}').listUsers(limit=1); print(type(r).__name__, r)\"")
    step("cancho-client-gen", "The app (a stand-in for whatever uses the service) registers 200 users through the client. Some are invalid on purpose.",
         f"python3 app.py http://127.0.0.1:{PORT}")
    step("cancho-table", "What did the launch traffic get back, and which fields were refused?",
         "table --group status --agg count --sort status --format csv requests.csv; table --where \"status = 422\" --group field --agg count --sort -count --format csv requests.csv")
    step("cancho-stats", "What does the service hold now? Ages of the registered users, and how many are over 120. (table compares text unless a column says :int.)",
         "stats describe users.csv --cols age > ages.json; for k in count mean max; do echo \"$k $(jsonq -p /data/columns/0/$k --format text ages.json)\"; done; echo \"older than 120: $(table --where 'age:int > 120' --agg count --format csv users.csv | tail -1)\"")
    step("cancho-tools", "An agent proposes a tighter limit: no age above 120. replace edits the one line of the declaration, and refuses unless it matches exactly once.",
         "replace --root cancho-web --old 'schema.new_int(heap, s2, 0, 150)' --new 'schema.new_int(heap, s2, 0, 120)' --expect 1 examples/users/users.cho | jsonq -p /data/replacements --format text -")
    out = run("(cd cancho-web && CC=static-cc scripts/build.sh examples/users/users.cho ../users-v2)")
    serve("users-v2")
    out2 = run(f"curl -s {URL}/openapi.json > openapi2.json; for f in openapi openapi2; do echo \"$f: max age $(jsonq -p /components/schemas/NewUser/properties/age/maximum --format text $f.json)\"; done")
    record("cancho-web", "Rebuild it as a static executable (the linker wrapper adds -static) and restart. The served document now says 120.",
           f"(cd cancho-web && CC=static-cc scripts/build.sh examples/users/users.cho ../users-v2); ./users-v2 {PORT} 2> serve.log &  curl -s {URL}/openapi.json > openapi2.json; for f in openapi openapi2; do echo \"$f: max age $(jsonq -p /components/schemas/NewUser/properties/age/maximum --format text $f.json)\"; done",
           (out + "\n" + out2).strip())
    step("cancho-client-gen", "Does the client need regenerating? The limit lives in the server's schema.",
         "clientgen openapi2.json --python -o client2.py; diff client.py client2.py > /dev/null && echo 'client unchanged'")
    step("cancho-web", "A 130-year-old customer, who was valid yesterday.",
         f"curl -s -XPOST {J} -d '{{\"name\":\"Old\",\"age\":130}}' {URL}/users > old.json; jsonq -p /errors/0 --format text old.json")
    for s in servers:
        s.terminate()
        s.wait(timeout=10)
    servers.clear()
    step("cancho-oci", "Package it. A dynamically linked program is refused by rule; the static one becomes an image, built twice into two directories: the same binary gives the same image. (Two builds of the source differ by 2 bytes, so a fresh build has a new digest.)",
         "mkdir -p root img0/blobs/sha256 img/blobs/sha256 img2/blobs/sha256; cp users-v1 root/users; oci-build --root root --out img0 --platform linux/amd64 --bin users:app/users; cp users-v2 root/users; oci-build --root root --out img --platform linux/amd64 --bin users:app/users; oci-build --root root --out img2 --platform linux/amd64 --bin users:app/users; diff -r img img2 && echo 'the two images are identical'")
    step("cancho-web", "What may the service do? The compiler proved it.",
         "(cd cancho-web && cancho authority examples/users/users.cho src/*.cho build/deps/*.cho --std | awk '/provably pure/{exit}{print}' | tr -s ' \\n' ' ')")
finally:
    for s in servers:
        s.terminate()
        s.wait(timeout=10)

ages = json.loads((work / "ages.json").read_text())["data"]["columns"][0]["histogram"]
steps[7]["chart"] = {"type": "histogram", "title": "Ages of the users the service holds (stats' exact histogram)", "short": "Ages of the registered users", "unit": "years", "edges": ages["edges"], "counts": ages["counts"]}
(here / "session.json").write_text(json.dumps({
    "title": "Ship an API: declare, generate a client, use it, change it, package it",
    "route": ["cancho-web", "cancho-client-gen", "cancho-table", "cancho-stats", "cancho-tools", "cancho-oci", "cancho-web"],
    "summary": "One declaration is the service, its OpenAPI document and the source of a typed client. An app uses it, the data it generates is analysed, an agent changes the contract, and the service is packaged as a reproducible image. Every step is a real run of a cancho tool; the seams that do not meet are shown as they are.",
    "source": "A recorded run of the real tools, replayed, on synthetic users (examples/ship-an-api/app.py): nothing here measures a real service. cancho-web's own users example is the service.",
    "steps": steps}, indent=2, ensure_ascii=False) + "\n")
print("wrote session.json,", len(steps), "steps")
