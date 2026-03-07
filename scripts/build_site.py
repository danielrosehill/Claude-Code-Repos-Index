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
    print(f"[1/6] README.md built from {len(category_files)} category files")
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
    print(f"[2/6] repos.json updated: {total} repos in {cats} categories")
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

    # Add dates and slugs
    added_dates = derive_added_dates(tagged)
    for repo in tagged:
        repo["added_date"] = added_dates.get(repo["name"], datetime.now().strftime("%Y-%m-%d"))
        repo["slug"] = slugify(repo["name"])

    # Sort repos alphabetically by name
    tagged.sort(key=lambda r: r["name"].lower())

    DOCS_DIR.mkdir(exist_ok=True)
    with open(TAGGED_REPOS_PATH, "w", encoding="utf-8") as f:
        json.dump(tagged, f, indent=2)

    all_tags = set()
    for r in tagged:
        all_tags.update(r["tags"])

    print(f"[3/6] tagged_repos.json generated: {len(tagged)} repos, {len(all_tags)} tags")
    return tagged


def slugify(name):
    """Convert a repo name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def derive_added_dates(tagged_repos):
    """Derive per-repo added dates from site_state.json history."""
    dates = {}
    if SITE_STATE_PATH.exists():
        with open(SITE_STATE_PATH, "r", encoding="utf-8") as f:
            state = json.load(f)
        for entry in state.get("history", []):
            date = entry.get("date", "")[:10]  # YYYY-MM-DD
            for change in entry.get("changes", []):
                if change.get("type") == "added":
                    for name in change.get("repos", []):
                        if name not in dates:
                            dates[name] = date
    # Default for repos with no history
    today = datetime.now().strftime("%Y-%m-%d")
    for repo in tagged_repos:
        if repo["name"] not in dates:
            dates[repo["name"]] = today
    return dates


def generate_repo_pages(tagged_repos):
    """Step 4a: Generate individual HTML pages for each repo."""
    repos_dir = DOCS_DIR / "repos"
    repos_dir.mkdir(parents=True, exist_ok=True)

    # Clean old pages
    for old_page in repos_dir.glob("*.html"):
        old_page.unlink()

    template = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name} - Claude Code Repos Index</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../style.css">
</head>
<body>

<nav class="topnav">
  <div class="nav-inner">
    <a href="../" class="nav-brand">Claude Code Index</a>
    <div class="nav-links">
      <a href="../">Index</a>
      <a href="../about.html">About</a>
      <a href="https://danielrosehill.com" target="_blank">Homepage</a>
      <a href="https://github.com/danielrosehill" target="_blank">GitHub</a>
      <a href="https://danielrosehill.com/contact" target="_blank">Contact</a>
    </div>
    <button class="nav-toggle" aria-label="Toggle menu" onclick="document.querySelector('.nav-links').classList.toggle('open')">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>
    </button>
  </div>
</nav>

<div class="page repo-detail">
  <a class="back-link" href="../">&larr; Back to Index</a>
  <h1>{name}</h1>
  <div class="repo-detail-tags">{tags_html}</div>
  <p>{description}</p>
  <div class="repo-detail-actions">
    <a class="btn btn-primary" href="{url}" target="_blank" rel="noopener">
      <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
      View on GitHub
    </a>
  </div>
  {added_html}
</div>

<footer class="footer">
  <div class="footer-inner">
    <span>&copy; Daniel Rosehill</span>
    <span class="footer-sep">&middot;</span>
    <a href="https://danielrosehill.com">danielrosehill.com</a>
    <span class="footer-sep">&middot;</span>
    <a href="https://github.com/danielrosehill/Claude-Code-Repos-Index">Source</a>
    <span class="footer-sep">&middot;</span>
    <a href="https://dsrholdings.cloud" target="_blank">Business Enquiries</a>
  </div>
</footer>

</body>
</html>'''

    for repo in tagged_repos:
        slug = slugify(repo["name"])
        tags_html = "".join(
            f'<span class="repo-detail-tag">{t}</span>' for t in repo["tags"]
        )
        added = repo.get("added_date", "")
        added_html = f'<p class="repo-detail-added">Added to index: {added}</p>' if added else ""

        html = template.format(
            name=repo["name"],
            description=repo["description"],
            url=repo["url"],
            tags_html=tags_html,
            added_html=added_html,
        )
        (repos_dir / f"{slug}.html").write_text(html, encoding="utf-8")

    print(f"[4a/6] Generated {len(tagged_repos)} repo detail pages")


def copy_assets():
    """Step 4b: Copy data files to docs/."""
    DOCS_DIR.mkdir(exist_ok=True)
    if REPOS_JSON_PATH.exists():
        shutil.copy2(REPOS_JSON_PATH, DOCS_DIR / "repos.json")
    print("[4b/6] Assets copied to docs/")


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

    print(f"[6/6] site_state.json updated ({', '.join(summary)})")

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
    generate_repo_pages(tagged)
    copy_assets()
    update_site_state(tagged)

    print("\n" + "=" * 60)
    print("Site build complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
