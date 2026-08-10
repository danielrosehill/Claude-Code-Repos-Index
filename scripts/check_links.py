#!/usr/bin/env python3
"""Fail if any internal link in the built site points at a page that was not generated.

Repo detail pages under /repos/<slug>/ only exist while the repo is in
tagged_repos.json. The hand-written essay pages in src/pages/ideas/ link to them
by slug, so dropping a repo from the index silently 404s every mention of it —
and nothing in the Astro build warns. That is exactly how 26 dead links
accumulated before 2026-08-10 (see notes/dead-repo-mentions.md).

Run after `npm run build`:
    python3 scripts/check_links.py
"""

import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).parent.parent
BUILD_DIR = REPO_ROOT / "docs"

HREF_RE = re.compile(r'href="([^"]+)"')


def build_targets():
    """Every path the built site can actually serve."""
    targets = set()
    for root, _dirs, files in os.walk(BUILD_DIR):
        for name in files:
            rel = Path(root, name).relative_to(BUILD_DIR).as_posix()
            targets.add("/" + rel)
            if name == "index.html":
                directory = "/" + Path(rel).parent.as_posix().strip(".")
                targets.add("/" if directory in ("/", "") else directory.rstrip("/") + "/")
    return targets


def main():
    if not BUILD_DIR.exists():
        sys.exit(f"{BUILD_DIR} does not exist — run `npm run build` first.")

    targets = build_targets()
    broken = {}
    checked = 0

    for root, _dirs, files in os.walk(BUILD_DIR):
        for name in files:
            if not name.endswith(".html"):
                continue
            src = Path(root, name)
            html = src.read_text(encoding="utf-8", errors="replace")
            for href in HREF_RE.findall(html):
                if href.startswith(("http://", "https://", "mailto:", "#", "data:", "//")):
                    continue
                path = urlparse(href).path
                if not path.startswith("/"):
                    continue
                checked += 1
                candidates = (path, path.rstrip("/") + "/", "/" + path.strip("/") + "/index.html")
                if not any(c in targets for c in candidates):
                    broken.setdefault(path, set()).add(
                        src.relative_to(BUILD_DIR).as_posix()
                    )

    print(f"checked {checked} internal links across {BUILD_DIR.name}/")
    if not broken:
        print("no broken internal links")
        return 0

    print(f"\n{len(broken)} broken target(s):", file=sys.stderr)
    for path, sources in sorted(broken.items()):
        shown = ", ".join(sorted(sources)[:3])
        more = f" (+{len(sources) - 3} more)" if len(sources) > 3 else ""
        print(f"  {path}\n      linked from: {shown}{more}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
