#!/usr/bin/env python3
"""
Build README.md by concatenating category files.

This script reads all markdown files from the categories/ directory
in sorted order and concatenates them into README.md.

Usage:
    python scripts/build_readme.py

The category files should be named with numeric prefixes to control order:
    00-header.md
    01-systems-administration.md
    02-non-code.md
    02a-non-code-legal.md
    03-research.md
    etc.
"""

from pathlib import Path
import sys


def build_readme():
    """Concatenate category files into README.md."""
    repo_root = Path(__file__).parent.parent
    categories_dir = repo_root / "categories"
    readme_path = repo_root / "README.md"

    if not categories_dir.exists():
        print(f"Error: Categories directory not found: {categories_dir}")
        sys.exit(1)

    # Get all markdown files sorted by name
    category_files = sorted(categories_dir.glob("*.md"))

    if not category_files:
        print("Error: No markdown files found in categories directory")
        sys.exit(1)

    print(f"Building README.md from {len(category_files)} category files...")

    # Concatenate all files
    content_parts = []
    for cat_file in category_files:
        print(f"  - {cat_file.name}")
        content = cat_file.read_text(encoding='utf-8')
        content_parts.append(content)

    # Join with newlines between sections
    full_content = "\n".join(content_parts)

    # Write to README.md
    readme_path.write_text(full_content, encoding='utf-8')

    print(f"\nREADME.md built successfully ({len(full_content)} characters)")
    print(f"Source files: {[f.name for f in category_files]}")


if __name__ == "__main__":
    build_readme()
