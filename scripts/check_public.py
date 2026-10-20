#!/usr/bin/env python3
"""Fail if data/ecosystem.json lists a repository that is not publicly readable, or a landing page that answers 404.

The map, agents.md and llms.txt are public, so a private repository must never reach them. Each GitHub URL in the data
file is probed with an anonymous `git ls-remote`: it succeeds for a public repository and fails for a private or missing
one (and costs no API rate limit). Each `page` URL must answer 2xx; a page that cannot be reached at all (no
network, as in some sandboxes) is reported as a warning, never as a pass or a failure. The probe runs from an empty temporary directory with no git config, so no credential
from the checkout can make a private repository look public.

    python3 scripts/check_public.py                 # data/ecosystem.json
    python3 scripts/check_public.py --file other.json
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
GITHUB = re.compile(r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?(?:#.*)?$")


def public(owner, repo, workdir):
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": workdir,
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    for k in ("HTTPS_PROXY", "https_proxy", "SSL_CERT_FILE", "GIT_SSL_CAINFO"):
        if k in os.environ:
            env[k] = os.environ[k]
    r = subprocess.run(
        ["git", "ls-remote", "--heads", "-q", f"https://github.com/{owner}/{repo}"],
        cwd=workdir, env=env, capture_output=True, timeout=60,
    )
    return r.returncode == 0


def page_status(url):
    """'ok', 'missing' (the server answered, and not with 2xx) or 'unreachable' (no answer at all)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "cancho-www-check"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return "ok" if 200 <= r.status < 300 else "missing"
    except urllib.error.HTTPError:
        return "missing"
    except Exception:
        return "unreachable"


def main():
    path = ROOT / "data" / "ecosystem.json"
    if "--file" in sys.argv:
        path = pathlib.Path(sys.argv[sys.argv.index("--file") + 1])
    data = json.loads(path.read_text())
    urls = []
    for p in data["projects"]:
        urls.append((p["id"], p["url"]))
    pages = [(p["id"], p["page"]) for p in data["projects"] if p.get("page")]
    bad, checked = [], 0
    with tempfile.TemporaryDirectory() as tmp:
        seen = set()
        for name, url in urls:
            m = GITHUB.match(url)
            if not m or (m.group(1), m.group(2)) in seen:
                continue
            seen.add((m.group(1), m.group(2)))
            checked += 1
            if not public(m.group(1), m.group(2), tmp):
                bad.append(f"{name}: {url}")
    missing, unreachable = [], []
    for name, url in pages:
        s = page_status(url)
        if s == "missing":
            missing.append(f"{name}: {url}")
        elif s == "unreachable":
            unreachable.append(f"{name}: {url}")
    if bad:
        print("not publicly readable (remove it from data/ecosystem.json, or make the repository public):")
        for b in bad:
            print("  " + b)
    if missing:
        print("landing page answers an error (publish it, or remove `page` from data/ecosystem.json):")
        for m in missing:
            print("  " + m)
    if unreachable:
        print(f"warning: could not reach {len(unreachable)} landing pages from here, so they were not checked (CI checks them)")
    if bad or missing:
        sys.exit(1)
    print(f"ok: {checked} repositories are public; {len(pages) - len(unreachable)} of {len(pages)} landing pages answer")


main()
