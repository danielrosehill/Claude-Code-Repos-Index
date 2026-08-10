#!/usr/bin/env python3
"""Report GitHub links in the index that a visitor cannot open.

An index is only as good as its links, and nothing here notices when a repo is
deleted or flipped to private — the entry keeps rendering a working-looking badge.
On 2026-08-10 the live site had nine such links, seven deleted and two private,
including the hero link to the model repo the whole site is organised around.

Two states matter and an anonymous request cannot tell them apart, because GitHub
returns 404 for a private repo as well as a missing one:

    deleted   404 anonymously, 404 authenticated  -> remove the entry
    private   404 anonymously, 200 authenticated  -> visitors see a dead link,
                                                      but the repo still exists

So this checks anonymously first, then re-checks the failures through `gh`.

Not wired into `npm run build`: it makes one network request per repo and would
make the build fail offline. Run it periodically, and after bulk additions.

    python3 scripts/check_external_links.py
"""

import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CATEGORIES_DIR = REPO_ROOT / "categories"
LINK_RE = re.compile(r"github\.com/danielrosehill/([A-Za-z0-9._-]+?)(?:\)|/|\s|$)")


def indexed_repos():
    """repo name -> sorted list of category files referencing it."""
    found = {}
    for cat_file in sorted(CATEGORIES_DIR.glob("*.md")):
        for name in LINK_RE.findall(cat_file.read_text(encoding="utf-8")):
            found.setdefault(name, set()).add(cat_file.name)
    return {k: sorted(v) for k, v in sorted(found.items())}


def reachable_anonymously(name):
    req = urllib.request.Request(
        f"https://github.com/danielrosehill/{name}",
        method="HEAD",
        headers={"User-Agent": "claude-code-projects-index-linkcheck"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status == 200
    except urllib.error.HTTPError:
        return False
    except Exception:
        return True  # network trouble: don't report a false positive


def exists_authenticated(name):
    result = subprocess.run(
        ["gh", "api", f"repos/danielrosehill/{name}", "--jq", ".private"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        return None  # genuinely gone
    return result.stdout.strip() == "true"  # True -> private


def main():
    repos = indexed_repos()
    print(f"checking {len(repos)} GitHub links from {CATEGORIES_DIR.name}/...\n")

    deleted, private = [], []
    for i, (name, files) in enumerate(repos.items(), 1):
        if reachable_anonymously(name):
            continue
        is_private = exists_authenticated(name)
        (private if is_private else deleted).append((name, files))
        if i % 50 == 0:
            print(f"  ...{i}/{len(repos)}", file=sys.stderr)

    if deleted:
        print(f"DELETED — remove these entries ({len(deleted)}):")
        for name, files in deleted:
            print(f"  {name}\n      in: {', '.join(files)}")
    if private:
        print(f"\nPRIVATE — exist, but every visitor sees a 404 ({len(private)}):")
        for name, files in private:
            print(f"  {name}\n      in: {', '.join(files)}")
    if not deleted and not private:
        print("all links resolve anonymously")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
