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
CATEGORIES_JSON_PATH = DATA_DIR / "categories.json"
TAGGED_REPOS_PATH = DOCS_DIR / "tagged_repos.json"
SITE_STATE_PATH = DATA_DIR / "site_state.json"
CREATED_DATES_PATH = DATA_DIR / "repo_created_dates.json"
ADDED_DATES_PATH = DATA_DIR / "repo_added_dates.json"
SPLIT_PAGES_PATH = DATA_DIR / "split_pages.json"
SPLIT_PAGE_BANNER = "<!-- GENERATED from categories/{source} — do not edit directly. Run `npm run build`. -->"


def load_split_config() -> dict:
    """Load data/split_pages.json mapping category file → standalone output file."""
    if not SPLIT_PAGES_PATH.exists():
        return {}
    with open(SPLIT_PAGES_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return {s["category_file"]: s for s in cfg.get("splits", [])}


def split_category_into_teaser(content: str, output_file: str, category_filename: str) -> tuple[str, str]:
    """Return (teaser_for_readme, full_page_content) for a split category.

    The teaser keeps the heading, banner image, and any intro paragraphs before
    the first repo entry, then appends a link to the dedicated page. The full
    page is the original content with a generated-file banner.
    """
    lines = content.split("\n")
    cut = next((i for i, line in enumerate(lines) if line.lstrip().startswith("### ")), len(lines))

    teaser_body = "\n".join(lines[:cut]).rstrip()
    repo_count = sum(1 for line in lines[cut:] if line.lstrip().startswith("### "))

    page_slug = output_file.rsplit(".", 1)[0]
    count_note = f" ({repo_count} entries)" if repo_count else ""
    teaser = (
        f"{teaser_body}\n\n"
        f"**[See full list in the dedicated {page_slug} page →](./{output_file})**{count_note}\n\n"
        "---\n"
    )

    banner = SPLIT_PAGE_BANNER.format(source=category_filename)
    page = f"{banner}\n\n{content.lstrip()}"
    return teaser, page


def emit_split_pages(split_config: dict) -> dict[str, str]:
    """Write standalone <output>.md files at the repo root for each split category.

    Returns a map of category filename → teaser text for use in the README.
    """
    teasers: dict[str, str] = {}
    for cat_filename, entry in split_config.items():
        cat_path = CATEGORIES_DIR / cat_filename
        if not cat_path.exists():
            print(f"  warning: split config references missing {cat_filename}")
            continue
        content = cat_path.read_text(encoding="utf-8")
        teaser, page = split_category_into_teaser(content, entry["output"], cat_filename)
        (REPO_ROOT / entry["output"]).write_text(page, encoding="utf-8")
        teasers[cat_filename] = teaser
        print(f"  emitted {entry['output']} ({cat_filename})")
    return teasers


def build_readme():
    """Step 1: Concatenate category files into README.md with teasers for split categories."""
    category_files = sorted(CATEGORIES_DIR.glob("*.md"))
    if not category_files:
        print("Error: No category files found")
        sys.exit(1)

    split_config = load_split_config()
    if split_config:
        print(f"[1a/5] Emitting {len(split_config)} split page(s)")
        teasers = emit_split_pages(split_config)
    else:
        teasers = {}

    content_parts = []
    for cat_file in category_files:
        if cat_file.name in teasers:
            content_parts.append(teasers[cat_file.name])
        else:
            content_parts.append(cat_file.read_text(encoding="utf-8"))

    full_content = "\n".join(content_parts)
    README_PATH.write_text(full_content, encoding="utf-8")
    split_note = f" ({len(teasers)} as teasers)" if teasers else ""
    print(f"[1/5] README.md built from {len(category_files)} category files{split_note}")
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

    # Load category hierarchy for slug lookup
    with open(CATEGORIES_JSON_PATH, "r", encoding="utf-8") as f:
        cat_hierarchy = json.load(f)
    cat_slug_map = {}
    cat_group_map = {}
    for group in cat_hierarchy["groups"]:
        for cat in group["categories"]:
            cat_slug_map[cat["name"]] = cat["slug"]
            cat_group_map[cat["name"]] = group["name"]

    tagged = []
    seen_names = set()

    for category in categories:
        cat_name = category["name"]
        cat_slug = cat_slug_map.get(cat_name, slugify(cat_name))
        cat_group = cat_group_map.get(cat_name, "Other")

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
                "category": cat_name,
                "category_slug": cat_slug,
                "category_group": cat_group,
            })

    # Add dates and slugs
    added_dates = derive_added_dates(tagged)
    created_dates = load_created_dates()
    banners_dir = REPO_ROOT / "public" / "banners"
    banner_exts = (".png", ".jpg", ".jpeg", ".webp", ".gif")
    for repo in tagged:
        repo["added_date"] = added_dates.get(repo["name"], datetime.now().strftime("%Y-%m-%d"))
        repo["slug"] = slugify(repo["name"])
        # Look up created_date by GitHub repo name from URL
        gh_name = repo["url"].rstrip("/").split("/")[-1] if repo["url"] else ""
        repo["created_date"] = created_dates.get(gh_name, repo["added_date"])
        # Detect optional banner: public/banners/<slug>.<ext>
        if banners_dir.exists():
            for ext in banner_exts:
                candidate = banners_dir / f"{repo['slug']}{ext}"
                if candidate.exists():
                    repo["banner"] = f"/banners/{candidate.name}"
                    break

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


def slugify(name):
    """Convert a repo name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def load_created_dates():
    """Load GitHub repo creation dates from data file."""
    if CREATED_DATES_PATH.exists():
        with open(CREATED_DATES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def derive_added_dates(tagged_repos):
    """Derive per-repo added dates, persisting them so they cannot drift.

    site_state.json history is capped at the last 50 entries, so a repo added long
    enough ago loses its "added" record and used to fall through to *today* — on
    every build. That silently restamped most of the index each time it was rebuilt
    (143 repos jumped from 2026-08-03 to 2026-08-10 in one build). Dates are now
    written to data/repo_added_dates.json and only ever assigned once.
    """
    dates = {}
    if ADDED_DATES_PATH.exists():
        with open(ADDED_DATES_PATH, "r", encoding="utf-8") as f:
            dates = json.load(f)

    # Fill any gaps from whatever history survives.
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

    # Genuinely new repos are stamped today — once.
    today = datetime.now().strftime("%Y-%m-%d")
    for repo in tagged_repos:
        if repo["name"] not in dates:
            dates[repo["name"]] = today

    with open(ADDED_DATES_PATH, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(dates.items())), f, indent=2)
        f.write("\n")

    return dates


def copy_assets():
    """Step 4: Copy data files to public/ for Astro and docs/ for legacy."""
    # Copy to Astro's public/ directory (served as static files)
    PUBLIC_DIR = REPO_ROOT / "public"
    PUBLIC_DIR.mkdir(exist_ok=True)
    if REPOS_JSON_PATH.exists():
        shutil.copy2(REPOS_JSON_PATH, PUBLIC_DIR / "repos.json")
    if CATEGORIES_JSON_PATH.exists():
        shutil.copy2(CATEGORIES_JSON_PATH, PUBLIC_DIR / "categories.json")
    # Also copy tagged_repos.json to public/ for runtime fetch
    if TAGGED_REPOS_PATH.exists():
        shutil.copy2(TAGGED_REPOS_PATH, PUBLIC_DIR / "tagged_repos.json")
    # Keep docs/ copies for backward compatibility during transition
    DOCS_DIR.mkdir(exist_ok=True)
    if REPOS_JSON_PATH.exists():
        shutil.copy2(REPOS_JSON_PATH, DOCS_DIR / "repos.json")
    if CATEGORIES_JSON_PATH.exists():
        shutil.copy2(CATEGORIES_JSON_PATH, DOCS_DIR / "categories.json")
    print("[4/5] Assets copied to public/ and docs/")


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

    # Only update last_built timestamp when there are actual content changes
    last_built = prev_state.get("last_built", datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
    if changes:
        last_built = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    state = {
        "last_built": last_built,
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


def sync_marketplace_step():
    """Step 0: Sync marketplace manifest → regenerate categories/08-plugins.md."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    try:
        from sync_marketplace import sync as run_sync
    except ImportError as e:
        print(f"[0/5] skipped marketplace sync: {e}")
        return
    print("[0/5] Syncing marketplace manifest")
    run_sync()


def main():
    print("=" * 60)
    print("Claude Code Repos Index - Site Build Pipeline")
    print("=" * 60 + "\n")

    sync_marketplace_step()
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
