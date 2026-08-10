#!/usr/bin/env python3
"""Backfill data/repo_created_dates.json with real GitHub creation dates.

The site's default "Newest" sort keys on `created_date`, which build_site.py reads
from this file. Any repo missing here falls back to `added_date`, which in turn
falls back to *today* — so an unpopulated entry silently sorts to the top and the
whole ordering becomes noise. This script keeps the file complete.

Fetches one repo per API call via `gh` (cheap: ~250 calls against a 5000/hr
authenticated budget) and keeps existing entries unless --refresh is passed.

Usage:
    python3 scripts/fetch_created_dates.py            # fill in missing only
    python3 scripts/fetch_created_dates.py --refresh  # re-fetch everything
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"
CATEGORIES_DIR = REPO_ROOT / "categories"
CREATED_DATES_PATH = DATA_DIR / "repo_created_dates.json"


def indexed_repo_names():
    """Every danielrosehill repo referenced from the category files."""
    names = set()
    for cat_file in sorted(CATEGORIES_DIR.glob("*.md")):
        text = cat_file.read_text(encoding="utf-8")
        for m in re.finditer(r"github\.com/danielrosehill/([A-Za-z0-9._-]+)", text):
            names.add(m.group(1).rstrip("/").rstrip("."))
    return sorted(names)


def fetch_created(name):
    """Return YYYY-MM-DD, or None if the repo is gone or renamed away."""
    try:
        out = subprocess.run(
            ["gh", "api", f"repos/danielrosehill/{name}", "--jq", ".createdAt // .created_at"],
            capture_output=True, text=True, check=True, timeout=30,
        ).stdout.strip()
        return out[:10] or None
    except subprocess.CalledProcessError:
        return None
    except subprocess.TimeoutExpired:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-fetch repos already recorded")
    args = ap.parse_args()

    existing = {}
    if CREATED_DATES_PATH.exists():
        existing = json.loads(CREATED_DATES_PATH.read_text(encoding="utf-8"))

    names = indexed_repo_names()
    todo = names if args.refresh else [n for n in names if n not in existing]

    print(f"{len(names)} indexed repos, {len(todo)} to fetch", file=sys.stderr)

    failed = []
    for i, name in enumerate(todo, 1):
        date = fetch_created(name)
        if date:
            existing[name] = date
        else:
            failed.append(name)
        if i % 25 == 0:
            print(f"  {i}/{len(todo)}", file=sys.stderr)

    merged = dict(sorted(existing.items()))
    CREATED_DATES_PATH.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")

    missing = [n for n in names if n not in merged]
    print(f"wrote {len(merged)} entries to {CREATED_DATES_PATH.name}", file=sys.stderr)
    if failed:
        print(f"could not resolve {len(failed)}: {', '.join(failed)}", file=sys.stderr)
    if missing:
        print(f"still missing {len(missing)}: {', '.join(missing)}", file=sys.stderr)


if __name__ == "__main__":
    main()
