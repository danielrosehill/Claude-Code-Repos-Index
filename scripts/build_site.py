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
    for repo in tagged:
        repo["added_date"] = added_dates.get(repo["name"], datetime.now().strftime("%Y-%m-%d"))
        repo["slug"] = slugify(repo["name"])
        # Look up created_date by GitHub repo name from URL
        gh_name = repo["url"].rstrip("/").split("/")[-1] if repo["url"] else ""
        repo["created_date"] = created_dates.get(gh_name, repo["added_date"])

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


def load_created_dates():
    """Load GitHub repo creation dates from data file."""
    if CREATED_DATES_PATH.exists():
        with open(CREATED_DATES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


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

    # Clean old pages (both flat .html and directory-based)
    for old_page in repos_dir.glob("*.html"):
        old_page.unlink()
    for old_dir in repos_dir.iterdir():
        if old_dir.is_dir():
            for f in old_dir.glob("*"):
                f.unlink()
            old_dir.rmdir()

    template = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name} - Claude Code Repos Index</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/style.css">
</head>
<body>

<nav class="topnav">
  <div class="nav-inner">
    <a href="/" class="nav-brand">Claude Code Index</a>
    <span class="nav-author">by Daniel Rosehill</span>
    <div class="nav-links">
      <a href="/">Index</a>
      <div class="nav-dropdown">
        <button class="nav-dropdown-trigger">Ideas <svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor"><path d="M2 4l3 3 3-3z"/></svg></button>
        <div class="nav-dropdown-menu nav-dropdown-ideas">
          <a class="dropdown-item" href="/ideas/claude-spaces/">Claude Spaces</a>
          <a class="dropdown-item" href="/ideas/non-code/">Non-Code Uses</a>
        </div>
      </div>
      <a href="/about/">About</a>
      <a href="https://danielrosehill.com" target="_blank">Homepage</a>
      <a href="https://github.com/danielrosehill" target="_blank">GitHub</a>
    </div>

    <button class="nav-toggle" aria-label="Toggle menu" onclick="document.querySelector('.nav-links').classList.toggle('open'); document.querySelectorAll('.nav-dropdown.open').forEach(d => d.classList.remove('open'))">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>
    </button>
  </div>
</nav>

<div class="breadcrumbs">
  <div class="breadcrumbs-inner">
    <a href="/">Index</a>
    <span class="bc-sep">/</span>
    <a href="/?category={category_slug}">{category}</a>
    <span class="bc-sep">/</span>
    <span class="bc-current">{name}</span>
  </div>
</div>

<main class="content detail-layout">
  <aside class="sidebar" id="sidebar">
    <h3 class="sidebar-heading">Categories</h3>
    <div id="category-nav"></div>
    <div class="sidebar-section">
      <h3 class="sidebar-heading">Tags</h3>
      <div id="tag-list"></div>
    </div>
    <div class="sidebar-section">
      <h3 class="sidebar-heading">Data</h3>
      <a class="sidebar-link" href="https://github.com/danielrosehill/Claude-Code-Repos-Index" target="_blank">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
        Source Repository
      </a>
      <a class="sidebar-link" href="/tagged_repos.json" target="_blank">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 1h8l3 3v11H1V1h3z"/><path d="M5 8h6M5 11h4"/></svg>
        JSON Data
      </a>
    </div>
  </aside>

  <div class="repo-detail">
    <h1>{name}</h1>
    <div class="repo-detail-meta">
      <span class="repo-detail-category">{category_group} &rsaquo; {category}</span>
      {added_html}
    </div>
    <div class="repo-detail-tags">{tags_html}</div>
    <p class="repo-detail-desc">{description}</p>
    <div class="repo-detail-actions">
      <a class="btn btn-primary" href="{url}" target="_blank" rel="noopener">
        <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
        View on GitHub
      </a>
      <a class="btn btn-outline" href="/">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M10 2L4 8l6 6"/></svg>
        Back to Index
      </a>
    </div>
  </div>
</main>

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

<script>
const CURRENT_CATEGORY_SLUG = "{category_slug}";

const CATEGORY_ICONS = {{
  'Non-Code': '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>',
  'Marketing': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>',
  'Technology & Hardware': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>',
  'Technical': '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>',
  'Research & Ideas': '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>',
  'Other': '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg>',
  'Productivity & Planning': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>',
  'Legal': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v18M3 7l9-4 9 4M3 7v4l9 4 9-4V7"/></svg>',
  'Health & Wellbeing': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/></svg>',
  'Communications & Writing': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>',
  'Financial Planning': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>',
  'Career': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2"/></svg>',
  'Business': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/></svg>',
  'Privacy & Anonymity': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
  'Systems Administration': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>',
  'Multi-Agent Tooling': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>',
  'MCP': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v6M12 18v4M4.93 4.93l4.24 4.24M14.83 14.83l4.24 4.24M2 12h6M18 12h4M4.93 19.07l4.24-4.24M14.83 9.17l4.24-4.24"/></svg>',
  'Plugins': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 3v18M3 9h18"/></svg>',
  'Slash Commands': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="7" y1="21" x2="17" y2="3"/></svg>',
  'Research': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>',
  'Argument and Perspective Exploration': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5A8.48 8.48 0 0121 11.5z"/></svg>',
  'Context and Personalization': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
  'Miscellaneous': '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/></svg>'
}};

function esc(s) {{
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}}

async function loadSidebar() {{
  try {{
    const [repoRes, catRes] = await Promise.all([
      fetch('/tagged_repos.json'),
      fetch('/categories.json')
    ]);
    const repos = await repoRes.json();
    const catHierarchy = await catRes.json();

    // Build category nav (same as index)
    const container = document.getElementById('category-nav');
    catHierarchy.groups.forEach(group => {{
      const groupEl = document.createElement('div');
      groupEl.className = 'cat-group';
      const groupLabel = document.createElement('div');
      groupLabel.className = 'cat-group-label';
      groupLabel.innerHTML = (CATEGORY_ICONS[group.name] || '') + ' ' + esc(group.name);
      groupEl.appendChild(groupLabel);

      group.categories.forEach(cat => {{
        const count = repos.filter(r => r.category_slug === cat.slug).length;
        if (count === 0) return;
        const btn = document.createElement('a');
        btn.className = 'cat-btn' + (cat.slug === CURRENT_CATEGORY_SLUG ? ' active' : '');
        btn.href = '/?category=' + cat.slug;
        btn.innerHTML = (CATEGORY_ICONS[cat.name] || '') + ' <span class="cat-name">' + esc(cat.name) + '</span><span class="tag-count">' + count + '</span>';
        groupEl.appendChild(btn);
      }});
      container.appendChild(groupEl);
    }});

    // Build tag list
    const allTags = {{}};
    repos.forEach(r => r.tags.forEach(t => {{ allTags[t] = (allTags[t] || 0) + 1; }}));
    const tagEl = document.getElementById('tag-list');
    Object.keys(allTags).sort().forEach(tag => {{
      const btn = document.createElement('a');
      btn.className = 'tag-btn';
      btn.href = '/?tag=' + encodeURIComponent(tag);
      btn.innerHTML = '<span class="tag-name">' + esc(tag) + '</span><span class="tag-count">' + allTags[tag] + '</span>';
      tagEl.appendChild(btn);
    }});
  }} catch(e) {{}}
}}
// Mobile dropdown toggle
document.querySelectorAll('.nav-dropdown-trigger').forEach(btn => {{
  btn.addEventListener('click', (e) => {{
    e.stopPropagation();
    const dropdown = btn.closest('.nav-dropdown');
    const wasOpen = dropdown.classList.contains('open');
    document.querySelectorAll('.nav-dropdown.open').forEach(d => d.classList.remove('open'));
    if (!wasOpen) dropdown.classList.toggle('open');
  }});
}});
document.addEventListener('click', () => {{
  document.querySelectorAll('.nav-dropdown.open').forEach(d => d.classList.remove('open'));
}});
loadSidebar();
</script>
</body>
</html>'''

    for repo in tagged_repos:
        slug = slugify(repo["name"])
        tags_html = "".join(
            f'<span class="tag-pill">{t}</span>' for t in repo["tags"]
        )
        added = repo.get("added_date", "")
        added_html = f'<span class="repo-detail-date">Added {added}</span>' if added else ""

        html = template.format(
            name=repo["name"],
            description=repo["description"],
            url=repo["url"],
            tags_html=tags_html,
            added_html=added_html,
            category=repo.get("category", "Miscellaneous"),
            category_slug=repo.get("category_slug", "misc"),
            category_group=repo.get("category_group", "Other"),
            slug=slug,
        )
        repo_page_dir = repos_dir / slug
        repo_page_dir.mkdir(exist_ok=True)
        (repo_page_dir / "index.html").write_text(html, encoding="utf-8")

    print(f"[4a/6] Generated {len(tagged_repos)} repo detail pages")


def copy_assets():
    """Step 4b: Copy data files to docs/."""
    DOCS_DIR.mkdir(exist_ok=True)
    if REPOS_JSON_PATH.exists():
        shutil.copy2(REPOS_JSON_PATH, DOCS_DIR / "repos.json")
    if CATEGORIES_JSON_PATH.exists():
        shutil.copy2(CATEGORIES_JSON_PATH, DOCS_DIR / "categories.json")
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
