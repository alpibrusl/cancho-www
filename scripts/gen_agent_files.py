#!/usr/bin/env python3
"""Derive the agent-facing files from data/ecosystem.json, so the map, agents.md and llms.txt cannot disagree.

    python3 scripts/gen_agent_files.py          # rewrite agents.md, llms.txt, llms-full.txt and the list in index.html
    python3 scripts/gen_agent_files.py --check  # exit 1 if any of them is stale (CI)
"""
import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "data" / "ecosystem.json").read_text())
site = data["site"]
projects = data["projects"]
kinds = data["kinds"]
stages = data["stages"]
fig = {f["id"]: f for f in data["measured"]["figures"]}


def by_kind():
    for k, title in kinds.items():
        yield title, [p for p in projects if p["kind"] == k]


def agents_md():
    m = data["measured"]
    out = [
        "# cancho",
        "",
        f"> {data['tagline']}",
        "",
        f"Status: pre-1.0. As of {data['as_of']}. Alpha products are built with it; the compiler is the Rust one, and a second compiler written in cancho is being checked against it (it does not yet refuse everything the language refuses).",
        "",
        "## The idea",
        "",
        "- A value is consumed exactly once. A `res` value must be consumed on every path; there are no destructors, no garbage collector, no exceptions.",
        "- Reaching the outside world (console, file, network, foreign code) requires holding a capability for it. `split(world)` is the only source of authority, and every piece must be handed on or `release`d.",
        "- Effect rows are exact: performing an effect you did not declare, or declaring one you do not perform, is refused.",
        "- Every refusal has a stable rule tag (for example `linear-value-unconsumed`, `effect-not-declared`). Match on the tag, not the prose.",
        "- Dependencies pin to content hashes. There is no version string.",
        "",
        "## Commands",
        "",
        "```sh",
        "cancho check <file.cho>... [--std] [--output json]   # refuse, or say nothing",
        "cancho build <file.cho>... [-o <output>] [--std]     # native binary",
        "cancho run   <file.cho>... [--std]                   # build, run, exit with the program's status",
        "cancho test  <file.cho>... [--std]                   # run every `fn test_*`; exit 4 if one failed",
        "cancho authority <file.cho> [--std] [--output json]  # what the program may do, and what it never touches",
        "cancho introspect                                    # the command tree, as data",
        "cancho skill                                         # a SKILL.md, as data",
        "```",
        "",
        "Start here to write cancho: https://github.com/alpibrusl/cancho/blob/main/AGENTS.md",
        "Docs: https://alpibrusl.github.io/cancho/",
        "",
        "## Ecosystem",
        "",
        "Stages: " + "; ".join(f"`{k}` = {v}" for k, v in stages.items()),
        "",
    ]
    for title, ps in by_kind():
        out += [f"### {title}", ""]
        for p in ps:
            line = f"- [{p['name']}]({p['url']}) `{p['stage']}`: {p['summary']}"
            if p.get("authority"):
                line += f" Authority: {p['authority']}."
            if p.get("rests_on"):
                line += " Rests on: " + ", ".join(p["rests_on"]) + "."
            if p.get("note"):
                line += f" {p['note']}"
            if p.get("docs"):
                line += f" Docs: {p['docs']}"
            out.append(line)
        out.append("")
    out += [
        "More, including repositories not listed here: https://github.com/orgs/alpibrusl/repositories?q=cancho-&type=public",
        "",
        "## Measured",
        "",
        f"On {m['platform']}, {m['date']} (moves as the work does; {m['source']}):",
        "",
        f"- {fig['conformance']['passed']} / {fig['conformance']['of']} {fig['conformance']['what']}.",
        f"- {fig['refusals']['passed']} / {fig['refusals']['of']} {fig['refusals']['what']}.",
        f"- {fig['rules']['value']} {fig['rules']['what']}.",
        "",
        f"Record: {m['record']}",
        "",
        "## Machine-readable",
        "",
        f"- {site}data/ecosystem.json: every project above as JSON",
        f"- {site}llms.txt and {site}llms-full.txt",
        "",
    ]
    return "\n".join(out)


def llms_txt():
    out = [
        "# cancho",
        "",
        f"> {data['tagline']}",
        "",
        "Status: pre-1.0. Alpha products are built with it; the compiler is the Rust one, and a second compiler written in cancho is being checked against it (it does not yet refuse everything the language refuses). See the roadmap for what is open.",
        "",
        "Source: https://github.com/alpibrusl/cancho",
        "Docs: https://alpibrusl.github.io/cancho/",
        "Roadmap: https://alpibrusl.github.io/cancho/ROADMAP.html",
        "Writing cancho programs (agents): https://github.com/alpibrusl/cancho/blob/main/AGENTS.md",
        f"This site as Markdown: {site}agents.md",
        f"Everything in one file: {site}llms-full.txt",
        f"The ecosystem as JSON: {site}data/ecosystem.json",
        "",
        "## Ecosystem",
        "",
    ]
    for p in projects:
        if p["id"] == "cancho":
            continue
        out.append(f"- [{p['name']}]({p.get('docs') or p['url']}) ({p['stage']}): {p['summary']}")
    out.append("")
    return "\n".join(out)


def llms_full():
    leak = (ROOT / "demo" / "src" / "leak.cho").read_text()
    fixed = (ROOT / "demo" / "src" / "fixed.cho").read_text()
    out = [
        agents_md(),
        "## Example: a leak, refused by a named rule",
        "",
        "```",
        leak.rstrip(),
        "```",
        "",
        "```sh",
        "$ cancho check leak.cho --std",
        "leak.cho:12:9: error: `f` is still live at the end of this block; nothing consumes it",
        "$ cancho check leak.cho --std --output json | grep -E '\"(rule|message)\"'",
        '      "rule": "linear-value-unconsumed",',
        "```",
        "",
        "One added line (`file_close(f);`) fixes it:",
        "",
        "```",
        fixed.rstrip(),
        "```",
        "",
    ]
    return "\n".join(out)


def eco_list():
    lines = ['<details class="note" id="map-fallback"><summary>The same map as a list</summary>', "<ul>"]
    for p in projects:
        lines.append(
            f'<li><a href="{html.escape(p["url"])}">{html.escape(p["name"])}</a> ({p["stage"]}): {html.escape(p["summary"])}</li>'
        )
    lines += ["</ul></details>"]
    return "\n".join("  " + l for l in lines)


def index_html():
    path = ROOT / "index.html"
    text = path.read_text()
    a, b = "<!-- eco:start -->", "<!-- eco:end -->"
    i, j = text.index(a) + len(a), text.index(b)
    return path, text[:i] + "\n" + eco_list() + "\n  " + text[j:]


def main():
    targets = {
        ROOT / "agents.md": agents_md(),
        ROOT / "llms.txt": llms_txt(),
        ROOT / "llms-full.txt": llms_full(),
    }
    p, t = index_html()
    targets[p] = t
    stale = [str(k.relative_to(ROOT)) for k, v in targets.items() if not k.exists() or k.read_text() != v]
    if "--check" in sys.argv:
        if stale:
            print("stale (run scripts/gen_agent_files.py): " + ", ".join(stale))
            sys.exit(1)
        return
    for k, v in targets.items():
        k.write_text(v)
    print("wrote " + ", ".join(str(k.relative_to(ROOT)) for k in targets))


main()
