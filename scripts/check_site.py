#!/usr/bin/env python3
"""Check a built site tree (the directory build_site.sh assembles as _site/).

    python3 scripts/check_site.py _site

It checks the tree, not the source, so it fails when the build put something wrong in place:

  * the root (/) is the cancho-ui build: a title, exactly one h1, the canonical link, and the page's content in the
    HTML itself (every project of data/ecosystem.json appears with JavaScript off);
  * /classic/ is the previous page and /next/ is a redirect to /; both name / as canonical; robots.txt keeps
    crawlers out of /classic/;
  * the files other things depend on are there (agents.md, llms.txt, llms-full.txt, data/ecosystem.json,
    data/demos.json, og.png, logo.png, logo-mark.png, demo/, CNAME, robots.txt), the data is data/ecosystem.json
    byte for byte, and any file that /classic/ and / both serve is the same bytes in both;
  * on each page, no URL is root-relative (it would break the page under a path such as /classic/ or
    alpibrusl.github.io/cancho-www/), no resource (script, stylesheet, image, media, frame, icon) is
    requested from another origin, and every internal link and resource resolves to a file in the tree.

Standard library only. Exits 1 on the first failure it can report, naming every problem it found.
"""
import html
import html.parser
import json
import pathlib
import re
import sys
import urllib.parse

REPO = pathlib.Path(__file__).resolve().parent.parent
problems = []


def bad(msg):
    problems.append(msg)


RESOURCE_REL = {"stylesheet", "icon", "apple-touch-icon", "preload", "prefetch", "modulepreload", "manifest", "shortcut"}
# attributes that make the browser fetch something, by tag
RESOURCE_ATTRS = {"script": ["src"], "img": ["src", "srcset"], "source": ["src", "srcset"], "video": ["src", "poster"],
                  "audio": ["src"], "iframe": ["src"], "embed": ["src"], "object": ["data"], "track": ["src"],
                  "input": ["src"]}


class Page(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.in_title = False
        self.h1 = []
        self.in_h1 = 0
        self.canonical = None
        self.urls = []        # (kind, tag, url): kind is "resource" or "link"
        self.css = []         # text of <style> blocks and style attributes
        self.scripts = []     # text of inline <script>
        self.text = []
        self.skip = 0
        self.frames = []      # srcdoc documents
        self.skiptag = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag == "h1":
            self.in_h1 += 1
            self.h1.append("")
        if tag in ("script", "style"):
            self.skiptag = tag
        if tag == "link":
            rels = set((a.get("rel") or "").lower().split())
            if "canonical" in rels:
                self.canonical = a.get("href")
            if rels & RESOURCE_REL and a.get("href"):
                self.urls.append(("resource", tag, a["href"]))
            elif a.get("href") and "alternate" in rels:
                self.urls.append(("link", tag, a["href"]))
        elif tag == "a" and a.get("href"):
            self.urls.append(("link", tag, a["href"]))
        for attr in RESOURCE_ATTRS.get(tag, []):
            v = a.get(attr)
            if not v:
                continue
            if attr == "srcset":
                for part in v.split(","):
                    if part.strip():
                        self.urls.append(("resource", tag, part.strip().split()[0]))
            else:
                self.urls.append(("resource", tag, v))
        if a.get("style"):
            self.css.append(a["style"])
        if tag == "iframe" and a.get("srcdoc"):
            self.frames.append(a["srcdoc"])
        if tag == "meta" and (a.get("http-equiv") or "").lower() == "refresh":
            m = re.search(r"url=(.+)$", a.get("content") or "", re.I)
            if m:
                self.urls.append(("link", tag, m.group(1).strip()))

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag == "h1" and self.in_h1:
            self.in_h1 -= 1
        if tag == self.skiptag:
            self.skiptag = None

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.in_h1:
            self.h1[-1] += data
        if self.skiptag == "style":
            self.css.append(data)
        elif self.skiptag == "script":
            self.scripts.append(data)
        else:
            self.text.append(data)


def parse(text):
    p = Page()
    p.feed(text)
    p.close()
    return p


def norm_text(s):
    return re.sub(r"\s+", " ", s).strip()


def check_page(tree, rel, expect_site):
    """rel: path of an html file under tree, like 'index.html' or 'classic/index.html'."""
    f = tree / rel
    if not f.is_file():
        bad(f"{rel}: missing")
        return None
    pages = [("", parse(f.read_text(encoding="utf-8")))]
    queue = list(pages[0][1].frames)
    while queue:  # sealed frames: their documents are checked like the page, except for links to files
        d = parse(queue.pop())
        pages.append(("(srcdoc) ", d))
        queue.extend(d.frames)
    here = f.parent
    for label, p in pages:
        for kind, tag, url in p.urls:
            u = urllib.parse.urlsplit(url)
            where = f"{rel}: {label}<{tag}> {url!r}"
            if u.scheme in ("http", "https") or url.startswith("//"):
                if kind == "resource":
                    bad(f"{where}: a resource from another origin (the page must request nothing outside its own)")
                continue
            if u.scheme in ("mailto", "tel", "data", "javascript", "blob", "about"):
                if kind == "resource" and u.scheme in ("javascript",):
                    bad(f"{where}: javascript: URL")
                continue
            if url.startswith("/"):
                bad(f"{where}: root-relative; it would break under /classic/ or a project path")
                continue
            if label:
                continue  # a sealed frame's relative URLs would resolve against about:srcdoc; none is expected
            path = urllib.parse.unquote(u.path)
            if not path:
                continue  # '#fragment' or '?query' on this page
            target = (here / path).resolve()
            try:
                target.relative_to(tree.resolve())
            except ValueError:
                bad(f"{where}: leaves the site")
                continue
            if target.is_dir():
                target = target / "index.html"
            if not target.is_file():
                bad(f"{where}: does not resolve to a file in the tree")
        css = "\n".join(p.css)
        if re.search(r"url\(\s*['\"]?/(?!/)", css):
            bad(f"{rel}: {label}CSS with a root-relative url()")
        if re.search(r"url\(\s*['\"]?(https?:)?//", css) or re.search(r"@import\s+(url\()?\s*['\"]?(https?:)?//", css):
            bad(f"{rel}: {label}CSS requests another origin")
        for s in p.scripts:
            if re.search(r"""(fetch|import|importScripts)\(\s*['"`]/(?!/)""", s):
                bad(f"{rel}: {label}inline script fetches a root-relative URL")
    return pages[0][1]


def check_assets(tree, subdir):
    """Scripts and styles that are files: no root-relative fetch or url()."""
    base = tree / subdir if subdir else tree
    for f in sorted(base.rglob("*")):
        if not f.is_file() or f.suffix not in (".js", ".css"):
            continue
        if not subdir and "classic" in f.relative_to(tree).parts[:1]:
            continue
        t = f.read_text(encoding="utf-8", errors="replace")
        rel = f.relative_to(tree)
        if re.search(r"""(fetch|import|importScripts)\(\s*['"`]/(?!/)""", t):
            bad(f"{rel}: fetches a root-relative URL")
        if re.search(r"url\(\s*['\"]?/(?!/)", t):
            bad(f"{rel}: root-relative url()")


def main():
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    tree = pathlib.Path(sys.argv[1]).resolve()
    data_file = REPO / "data" / "ecosystem.json"
    data = json.loads(data_file.read_text())
    site = data["site"]  # https://cancho.dev/

    # files other things depend on, at the same URLs the site has always served them from
    for rel in ["CNAME", "robots.txt", "agents.md", "llms.txt", "llms-full.txt", "data/ecosystem.json",
                "data/demos.json", "og.png", "logo.png", "logo-mark.png", "demo/demo.mp4", "demo/demo.webm",
                "demo/poster.png", "demo/demo.cast", "assets/fonts/OFL-Caveat.txt", "assets/fonts/OFL-JetBrainsMono.txt",
                "assets/fonts/OFL-PlusJakartaSans.txt"]:
        f = tree / rel
        if not f.is_file() or f.stat().st_size == 0:
            bad(f"/{rel}: missing or empty")
    if (tree / "CNAME").is_file() and (tree / "CNAME").read_text().strip() != "cancho.dev":
        bad("/CNAME: not cancho.dev")
    for rel, src in [("data/ecosystem.json", data_file), ("data/demos.json", REPO / "data" / "demos.json"),
                     ("agents.md", REPO / "agents.md"), ("llms.txt", REPO / "llms.txt"),
                     ("llms-full.txt", REPO / "llms-full.txt"), ("og.png", REPO / "og.png"),
                     ("logo.png", REPO / "logo.png"), ("logo-mark.png", REPO / "logo-mark.png")]:
        for prefix in ("", "classic/"):
            f = tree / prefix / rel
            if f.is_file() and f.read_bytes() != src.read_bytes():
                bad(f"/{prefix}{rel}: not byte for byte the repository's {src.name}: the live page would be stale")
    for rel in ["data/ecosystem.json", "data/demos.json"]:
        try:
            json.loads((tree / rel).read_text())
        except Exception as e:  # noqa: BLE001
            bad(f"/{rel}: not JSON ({e})")
    # whatever both trees serve at one path is the same bytes
    classic = tree / "classic"
    if classic.is_dir():
        for f in sorted(classic.rglob("*")):
            rel = f.relative_to(classic)
            g = tree / rel
            if f.is_file() and rel.name != "index.html" and g.is_file() and f.read_bytes() != g.read_bytes():
                bad(f"/{rel} differs between / and /classic/")

    robots = (tree / "robots.txt").read_text() if (tree / "robots.txt").is_file() else ""
    if not re.search(r"^Disallow:\s*/classic/\s*$", robots, re.M):
        bad("robots.txt: /classic/ is not disallowed")
    if re.search(r"^Disallow:\s*/\s*$", robots, re.M):
        bad("robots.txt: disallows the whole site")

    # the root: the cancho-ui build
    root = check_page(tree, "index.html", site)
    if root:
        if not norm_text(root.title):
            bad("/: no <title>")
        h1 = [norm_text(h) for h in root.h1]
        if len(h1) != 1 or not h1[0]:
            bad(f"/: expected exactly one non-empty h1, found {h1!r}")
        if root.canonical != site:
            bad(f"/: canonical is {root.canonical!r}, expected {site!r}")
        # JavaScript off: the content is in the HTML, not drawn by a script
        body = norm_text(" ".join(root.text))
        missing = [p["name"] for p in data["projects"] if p["name"] not in body]
        if missing:
            bad(f"/: with JavaScript off these projects of data/ecosystem.json are not in the page: {missing}")
        for c in data["verifies"]["compiler"][:3]:
            first = norm_text(c["claim"].replace("`", ""))[:40]
            if first and first not in body and html.unescape(first) not in body:
                bad(f"/: a claim of data/ecosystem.json is not in the HTML: {first!r}")
        if "<script" not in (tree / "index.html").read_text():
            bad("/: no script at all; the cancho-ui build is expected to carry app.js")
    check_assets(tree, "")

    # /classic/
    c = check_page(tree, "classic/index.html", site)
    if c:
        if not norm_text(c.title):
            bad("/classic/: no <title>")
        if c.canonical != site:
            bad(f"/classic/: canonical is {c.canonical!r}, expected {site!r}")
    check_assets(tree, "classic")

    # /next/
    n = check_page(tree, "next/index.html", site)
    if n and n.canonical != site:
        bad(f"/next/: canonical is {n.canonical!r}, expected {site!r}")
    if (tree / "next" / "index.html").is_file():
        t = (tree / "next" / "index.html").read_text()
        if 'url=../' not in t:
            bad("/next/: not a redirect to /")
        if len(list((tree / "next").rglob("*"))) != 1:
            bad("/next/: more than the redirect page")

    if problems:
        print(f"check_site: {len(problems)} problem(s) in {tree}:", file=sys.stderr)
        for p in problems:
            print("  - " + p, file=sys.stderr)
        return 1
    print(f"check_site: {tree} ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
