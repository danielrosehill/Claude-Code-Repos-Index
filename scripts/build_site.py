#!/usr/bin/env python3
"""
Build the deployed index site from the current repo data.

This is the unified build pipeline that:
1. Builds README.md from category files
2. Updates repos.json from README.md
3. Generates tagged_repos.json for the site using tag rules
4. Copies assets to docs/
5. Updates site_state.json tracking file

Usage:
    python scripts/build_site.py
"""

import hashlib
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CATEGORIES_DIR = REPO_ROOT / "categories"
DATA_DIR = REPO_ROOT / "data"
DOCS_DIR = REPO_ROOT / "docs"
README_PATH = REPO_ROOT / "README.md"
REPOS_JSON_PATH = DATA_DIR / "repos.json"
TAG_RULES_PATH = DATA_DIR / "tag_rules.json"
TAGGED_REPOS_PATH = DOCS_DIR / "tagged_repos.json"
SITE_STATE_PATH = DATA_DIR / "site_state.json"


def build_readme():
    """Step 1: Concatenate category files into README.md."""
    category_files = sorted(CATEGORIES_DIR.glob("*.md"))
    if not category_files:
        print("Error: No category files found")
        sys.exit(1)

    content_parts = []
    for cat_file in category_files:
        content_parts.append(cat_file.read_text(encoding="utf-8"))

    full_content = "\n".join(content_parts)
    README_PATH.write_text(full_content, encoding="utf-8")
    print(f"[1/5] README.md built from {len(category_files)} category files")
    return full_content


def parse_readme_to_repos_json():
    """Step 2: Parse README.md into repos.json (reuses existing logic)."""
    # Import and run the existing parser
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from update_repo_tracking import parse_readme_to_json

    data = parse_readme_to_json()
    DATA_DIR.mkdir(exist_ok=True)
    with open(REPOS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    total = data["statistics"]["total_repositories"]
    cats = data["statistics"]["total_categories"]
    print(f"[2/5] repos.json updated: {total} repos in {cats} categories")
    return data


def parse_categories_direct():
    """Parse category files directly to get accurate category-to-repo mapping."""
    category_files = sorted(CATEGORIES_DIR.glob("*.md"))
    categories = []

    for cat_file in category_files:
        content = cat_file.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Find the category heading (# Title)
        cat_name = None
        for line in lines:
            line = line.strip()
            if line.startswith("# ") and not line.startswith("## "):
                cat_name = line[2:].strip()
                break

        if not cat_name:
            continue

        # Skip the header file
        if cat_name in ("Claude Code Repos Index", ""):
            continue

        # Parse repos from this category file
        repos = []
        current_repo = None
        desc_lines = []

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("### "):
                # Save previous repo
                if current_repo and desc_lines:
                    current_repo["description"] = " ".join(desc_lines).strip()
                if current_repo:
                    repos.append(current_repo)

                current_repo = {"name": stripped[4:].strip(), "url": "", "description": ""}
                desc_lines = []

            elif current_repo:
                badge_match = re.search(
                    r"\[!\[View Repo\].*?\]\((https://github\.com/[^)]+)\)", stripped
                )
                if badge_match:
                    current_repo["url"] = badge_match.group(1)
                elif (
                    stripped
                    and not stripped.startswith("[![")
                    and not stripped.startswith("![")
                    and not stripped.startswith("---")
                    and not stripped.startswith("#")
                ):
                    desc_lines.append(stripped)

        # Save last repo
        if current_repo and desc_lines:
            current_repo["description"] = " ".join(desc_lines).strip()
        if current_repo:
            repos.append(current_repo)

        if repos:
            categories.append({"name": cat_name, "repos": repos})

    return categories


def generate_tagged_repos(_repos_data):
    """Step 3: Generate tagged_repos.json from category files + tag rules."""
    with open(TAG_RULES_PATH, "r", encoding="utf-8") as f:
        rules = json.load(f)

    category_tags = rules.get("category_tags", {})
    keyword_tags = rules.get("keyword_tags", {})
    overrides = rules.get("tag_overrides", {})

    # Parse categories directly from files for accurate mapping
    categories = parse_categories_direct()

    tagged = []
    seen_names = set()

    for category in categories:
        cat_name = category["name"]
        # Find matching category tags
        base_tags = []
        for rule_cat, rule_tags in category_tags.items():
            if rule_cat.lower() in cat_name.lower() or cat_name.lower() in rule_cat.lower():
                base_tags.extend(rule_tags)

        for repo in category["repos"]:
            name = repo["name"]
            if name in seen_names:
                continue
            seen_names.add(name)

            desc = repo.get("description", "")
            url = repo.get("url", "")

            # Check for manual override first
            if name in overrides:
                repo_tags = overrides[name]
            else:
                repo_tags = list(base_tags)

                # Apply keyword-based tags
                for tag, patterns in keyword_tags.items():
                    if tag in repo_tags:
                        continue
                    matched = False
                    for pat in patterns.get("name_patterns", []):
                        if pat.lower() in name.lower():
                            matched = True
                            break
                    if not matched:
                        for pat in patterns.get("desc_patterns", []):
                            if pat.lower() in desc.lower():
                                matched = True
                                break
                    if matched:
                        repo_tags.append(tag)

            # Ensure at least one tag
            if not repo_tags:
                repo_tags = ["Documentation"]

            # Sort tags alphabetically, deduplicate
            repo_tags = sorted(set(repo_tags))

            tagged.append({
                "name": name,
                "url": url,
                "description": desc,
                "tags": repo_tags,
            })

    # Sort repos alphabetically by name
    tagged.sort(key=lambda r: r["name"].lower())

    DOCS_DIR.mkdir(exist_ok=True)
    with open(TAGGED_REPOS_PATH, "w", encoding="utf-8") as f:
        json.dump(tagged, f, indent=2)

    all_tags = set()
    for r in tagged:
        all_tags.update(r["tags"])

    print(f"[3/5] tagged_repos.json generated: {len(tagged)} repos, {len(all_tags)} tags")
    return tagged


def copy_assets():
    """Step 4: Copy data files to docs/."""
    DOCS_DIR.mkdir(exist_ok=True)
    if REPOS_JSON_PATH.exists():
        shutil.copy2(REPOS_JSON_PATH, DOCS_DIR / "repos.json")
    print("[4/5] Assets copied to docs/")


def update_site_state(tagged_repos):
    """Step 5: Update site_state.json with deployment tracking info."""
    # Build a manifest of what's in the site
    repo_manifest = {}
    for repo in tagged_repos:
        content = json.dumps(repo, sort_keys=True)
        repo_manifest[repo["name"]] = hashlib.md5(content.encode()).hexdigest()

    # Load previous state
    prev_state = {}
    if SITE_STATE_PATH.exists():
        with open(SITE_STATE_PATH, "r", encoding="utf-8") as f:
            prev_state = json.load(f)

    prev_manifest = prev_state.get("repo_manifest", {})
    prev_names = set(prev_manifest.keys())
    curr_names = set(repo_manifest.keys())

    added = sorted(curr_names - prev_names)
    removed = sorted(prev_names - curr_names)
    modified = sorted(
        name
        for name in curr_names & prev_names
        if repo_manifest[name] != prev_manifest.get(name)
    )

    # Build changelog entry
    changes = []
    if added:
        changes.append({"type": "added", "repos": added})
    if removed:
        changes.append({"type": "removed", "repos": removed})
    if modified:
        changes.append({"type": "modified", "repos": modified})

    # Append to history (keep last 50 entries)
    history = prev_state.get("history", [])
    if changes:
        history.append({
            "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "changes": changes,
            "total_repos": len(tagged_repos),
        })
    history = history[-50:]

    state = {
        "last_built": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "total_repos": len(tagged_repos),
        "total_tags": len({t for r in tagged_repos for t in r["tags"]}),
        "repo_manifest": repo_manifest,
        "history": history,
    }

    with open(SITE_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    summary = []
    if added:
        summary.append(f"{len(added)} added")
    if removed:
        summary.append(f"{len(removed)} removed")
    if modified:
        summary.append(f"{len(modified)} modified")
    if not summary:
        summary.append("no changes")

    print(f"[5/5] site_state.json updated ({', '.join(summary)})")

    if added:
        for name in added:
            print(f"       + {name}")
    if removed:
        for name in removed:
            print(f"       - {name}")


def main():
    print("=" * 60)
    print("Claude Code Repos Index - Site Build Pipeline")
    print("=" * 60 + "\n")

    readme_content = build_readme()
    repos_data = parse_readme_to_repos_json()
    tagged = generate_tagged_repos(repos_data)
    copy_assets()
    update_site_state(tagged)

    print("\n" + "=" * 60)
    print("Site build complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
