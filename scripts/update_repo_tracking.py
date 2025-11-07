#!/usr/bin/env python3
"""
Track repository count over time and generate visualization.
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


def count_repos_in_readme():
    """Count the number of repository entries in README.md"""
    with open(README_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Count "View Repo" badges as proxy for repository entries
    repo_pattern = r'\[!\[View Repo\]'
    matches = re.findall(repo_pattern, content)
    return len(matches)


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
