#!/usr/bin/env python3
"""
Discover public Claude-related GitHub repositories not yet in the index.

Compares repos from danielrosehill's GitHub account against what's already
tracked in the category files, and outputs a JSON list of unindexed repos.

Usage:
    python scripts/discover_new_repos.py              # Claude-related repos only
    python scripts/discover_new_repos.py --all        # All public repos (broad)
    python scripts/discover_new_repos.py --pattern X  # Custom regex filter

Output: JSON array to stdout with {name, url, description} for each new repo.
Also writes to data/unindexed_repos.json for consumption by the sync command.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CATEGORIES_DIR = REPO_ROOT / "categories"
DATA_DIR = REPO_ROOT / "data"
OUTPUT_PATH = DATA_DIR / "unindexed_repos.json"

# Default pattern: repos with claude, agent-workspace, or claude-code in the name
DEFAULT_PATTERN = r"claude|agent-workspace|claude-code"

# Repos to always skip (meta repos, forks, non-relevant)
SKIP_REPOS = {
    "Claude-Code-Projects-Index",  # This repo itself
    "Claude-Code-Repos-Index",     # Former name of this repo (rename redirect)
    "Claude-Agent-Blueprints",     # Former name of this repo (rename redirect)
    "claude-code",                 # Anthropic's Claude Code (fork)
    "awesome-claude-code",         # Curated list, not a project repo
}


def get_indexed_repo_names():
    """Extract all repo names currently in the index from category files."""
    indexed = set()
    for cat_file in CATEGORIES_DIR.glob("*.md"):
        content = cat_file.read_text(encoding="utf-8")
        # Match GitHub URLs in View Repo badges
        for match in re.finditer(
            r"github\.com/danielrosehill/([^)\s]+)", content
        ):
            indexed.add(match.group(1).rstrip("/"))
    return indexed


def get_github_repos(pattern=None):
    """Fetch public repos from GitHub using gh CLI."""
    # Limit must stay above the account's total public repo count (>1050 as of
    # Aug 2026) — gh truncates silently, which used to hide older candidates.
    cmd = [
        "gh", "repo", "list", "danielrosehill",
        "--limit", "2000",
        "--visibility", "public",
        "--no-archived",
        "--source",  # exclude forks
        "--json", "name,description,url",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    repos = json.loads(result.stdout)

    if pattern:
        regex = re.compile(pattern, re.IGNORECASE)
        repos = [r for r in repos if regex.search(r["name"])]

    return repos


def discover(pattern=None):
    """Find repos on GitHub that aren't in the index yet."""
    indexed = get_indexed_repo_names()
    github_repos = get_github_repos(pattern)

    new_repos = []
    for repo in github_repos:
        name = repo["name"]
        if name in indexed or name in SKIP_REPOS:
            continue
        new_repos.append({
            "name": name,
            "url": repo.get("url", f"https://github.com/danielrosehill/{name}"),
            "description": repo.get("description", "") or "",
        })

    new_repos.sort(key=lambda r: r["name"].lower())
    return new_repos


def main():
    parser = argparse.ArgumentParser(description="Discover unindexed repos")
    parser.add_argument(
        "--all", action="store_true",
        help="Check ALL public repos (not just Claude-related)"
    )
    parser.add_argument(
        "--pattern", type=str, default=None,
        help="Custom regex pattern to filter repo names"
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Only output JSON, no status messages"
    )
    args = parser.parse_args()

    pattern = None if args.all else (args.pattern or DEFAULT_PATTERN)

    if not args.quiet:
        scope = "all public" if args.all else f"matching /{pattern}/"
        print(f"Scanning {scope} repos...", file=sys.stderr)

    new_repos = discover(pattern)

    # Write to file
    DATA_DIR.mkdir(exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(new_repos, f, indent=2)

    if not args.quiet:
        print(f"Found {len(new_repos)} unindexed repos", file=sys.stderr)
        if new_repos:
            print(f"Written to {OUTPUT_PATH}", file=sys.stderr)
            print("", file=sys.stderr)
            for r in new_repos:
                desc = f" — {r['description']}" if r["description"] else ""
                print(f"  • {r['name']}{desc}", file=sys.stderr)

    # Also output JSON to stdout for piping
    json.dump(new_repos, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
