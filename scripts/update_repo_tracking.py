#!/usr/bin/env python3
"""
Track repository count over time, generate visualization, and update repos.json.
This script is called by the pre-push git hook.
"""

import json
import re
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Paths
REPO_ROOT = Path(__file__).parent.parent
README_PATH = REPO_ROOT / "README.md"
JSON_PATH = REPO_ROOT / "repo-count-history.json"
CHART_PATH = REPO_ROOT / "repo-count-chart.png"
REPOS_JSON_PATH = REPO_ROOT / "repos.json"


def count_repos_in_readme():
    """Count the number of repository entries in README.md"""
    with open(README_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Count "View Repo" badges as proxy for repository entries
    repo_pattern = r'\[!\[View Repo\]'
    matches = re.findall(repo_pattern, content)
    return len(matches)


def parse_readme_to_json():
    """Parse README.md and extract all repositories organized by category"""
    with open(README_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    categories = []
    current_category = None
    current_category_desc = None
    current_repo = None
    repo_description_lines = []

    lines = content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        # Match top-level category (# heading, not ##)
        # Skip lines that are part of header/intro (before "Repo Index, By Section")
        if line.startswith('# ') and not line.startswith('# Repo Index'):
            # Check if this is a category (comes after the intro section)
            # Categories start with single # and are not the title or section markers
            if current_category is not None or 'Repo Index' in '\n'.join(lines[:i]):
                # Save previous category if exists
                if current_category and current_category.get('repositories'):
                    categories.append(current_category)

                category_name = line[2:].strip()
                # Get description from next non-empty line if it's not a heading or repo
                current_category_desc = ""
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    if next_line and not next_line.startswith('#') and not next_line.startswith('[!['):
                        if not next_line.startswith('---'):
                            current_category_desc = next_line
                        break
                    elif next_line.startswith('#') or next_line.startswith('[!['):
                        break
                    j += 1

                current_category = {
                    "name": category_name,
                    "description": current_category_desc,
                    "repositories": []
                }
                current_repo = None
                repo_description_lines = []

        # Match repository entry (## heading followed by View Repo badge)
        elif line.startswith('## ') and not line.startswith('### '):
            # Save previous repo description if exists
            if current_repo and repo_description_lines:
                current_repo['description'] = ' '.join(repo_description_lines).strip()

            repo_name = line[3:].strip()
            current_repo = {"name": repo_name, "url": "", "description": ""}
            repo_description_lines = []

            # Look for the View Repo badge in next few lines
            for j in range(i + 1, min(i + 5, len(lines))):
                badge_match = re.search(r'\[!\[View Repo\].*?\]\((https://github\.com/[^)]+)\)', lines[j])
                if badge_match:
                    current_repo['url'] = badge_match.group(1)
                    break

            if current_category:
                current_category['repositories'].append(current_repo)

        # Match repository entry with ### heading (alternative format)
        elif line.startswith('### '):
            # Save previous repo description if exists
            if current_repo and repo_description_lines:
                current_repo['description'] = ' '.join(repo_description_lines).strip()

            repo_name = line[4:].strip()
            current_repo = {"name": repo_name, "url": "", "description": ""}
            repo_description_lines = []

            # Look for the View Repo badge in next few lines
            for j in range(i + 1, min(i + 5, len(lines))):
                badge_match = re.search(r'\[!\[View Repo\].*?\]\((https://github\.com/[^)]+)\)', lines[j])
                if badge_match:
                    current_repo['url'] = badge_match.group(1)
                    break

            if current_category:
                current_category['repositories'].append(current_repo)

        # Collect description lines for current repo
        elif current_repo and line.strip():
            # Skip badge lines, horizontal rules, and empty lines
            if not line.startswith('[![') and not line.startswith('---') and not line.startswith('#'):
                repo_description_lines.append(line.strip())

        i += 1

    # Save last repo description
    if current_repo and repo_description_lines:
        current_repo['description'] = ' '.join(repo_description_lines).strip()

    # Save last category
    if current_category and current_category.get('repositories'):
        categories.append(current_category)

    # Build statistics
    total_repos = sum(len(cat['repositories']) for cat in categories)
    repos_by_category = {cat['name']: len(cat['repositories']) for cat in categories}

    result = {
        "metadata": {
            "title": "Claude Code Repos Index",
            "description": "Curated index of Claude Code-related resources and projects",
            "master_index_url": "https://github.com/danielrosehill/Github-Master-Index",
            "generated_date": datetime.now().strftime("%Y-%m-%d")
        },
        "categories": categories,
        "statistics": {
            "total_categories": len(categories),
            "total_repositories": total_repos,
            "repositories_by_category": repos_by_category
        }
    }

    return result


def update_repos_json():
    """Update repos.json with current README.md content"""
    print("\nParsing README.md to update repos.json...")
    data = parse_readme_to_json()

    with open(REPOS_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f"repos.json updated: {data['statistics']['total_repositories']} repositories in {data['statistics']['total_categories']} categories")


def load_tracking_data():
    """Load existing tracking data from JSON"""
    if not JSON_PATH.exists():
        return {
            "tracking_started": datetime.now().strftime("%Y-%m-%d"),
            "description": "Historical tracking of repository count in Claude Code Repos Index",
            "data_points": []
        }

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_tracking_data(data):
    """Save tracking data to JSON"""
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def update_tracking_data(count):
    """Add new data point if it's a new day"""
    data = load_tracking_data()
    today = datetime.now().strftime("%Y-%m-%d")

    # Check if we already have a data point for today
    if data["data_points"] and data["data_points"][-1]["date"] == today:
        # Update today's count
        data["data_points"][-1]["count"] = count
        print(f"Updated today's count: {count} repositories")
    else:
        # Add new data point
        data["data_points"].append({
            "date": today,
            "count": count
        })
        print(f"Added new data point: {today} - {count} repositories")

    save_tracking_data(data)
    return data


def generate_chart(data):
    """Generate visualization chart of repo count over time"""
    if not data["data_points"]:
        print("No data points to visualize yet")
        return

    # Extract dates and counts
    dates = [datetime.strptime(dp["date"], "%Y-%m-%d") for dp in data["data_points"]]
    counts = [dp["count"] for dp in data["data_points"]]

    # Create figure
    plt.figure(figsize=(12, 6))
    plt.plot(dates, counts, marker='o', linewidth=2, markersize=6, color='#2E86AB')

    # Styling
    plt.title('Claude Code Repos Index - Repository Count Over Time',
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Date', fontsize=12, fontweight='bold')
    plt.ylabel('Number of Repositories', fontsize=12, fontweight='bold')
    plt.grid(True, alpha=0.3, linestyle='--')

    # Format x-axis dates
    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45, ha='right')

    # Add value labels on points
    for date, count in zip(dates, counts):
        plt.annotate(str(count),
                    (date, count),
                    textcoords="offset points",
                    xytext=(0,10),
                    ha='center',
                    fontsize=9,
                    fontweight='bold')

    # Tight layout and save
    plt.tight_layout()
    plt.savefig(CHART_PATH, dpi=300, bbox_inches='tight')
    print(f"Chart saved to: {CHART_PATH}")
    plt.close()


def main():
    """Main execution function"""
    print("=" * 60)
    print("Claude Code Repos Index - Repository Tracking Update")
    print("=" * 60)

    # Count repositories
    count = count_repos_in_readme()
    print(f"\nCurrent repository count: {count}")

    # Update tracking data
    data = update_tracking_data(count)

    # Generate visualization
    generate_chart(data)

    print("\n" + "=" * 60)
    print("Tracking update complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
