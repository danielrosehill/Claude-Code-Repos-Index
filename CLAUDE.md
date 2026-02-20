# Claude Code Repos Index - Repository Instructions

## Purpose

This repository serves as a curated index of Claude Code-related resources and projects shared on GitHub. It provides organized, categorized listings with descriptions to help users discover relevant tools, libraries, and configurations for Claude Code workflows.

Many of the repositories in this index are **Claude Spaces**—pre-configured workspaces that use Claude as a Conversational UI Agent for structured, non-development workflows. These represent a pattern where repositories serve as mini AI agent workspaces rather than traditional codebases.

## Repository Structure

- **`README.md`**: Main index displaying all repositories (auto-generated from category files)
- **`categories/`**: Individual category files that are concatenated to build README.md
- **`scratchpad.md`**: Staging area for new repositories to be added to the index
- **`scripts/build_readme.py`**: Script to regenerate README.md from category files
- **`scripts/update_repo_tracking.py`**: Script to update repo counts and repos.json
- **`data/repos.json`**: Programmatic representation of the index
- **`images/`**: Category banner images

## Modular Category System

The index is built from individual category files stored in the `categories/` directory. This modular approach allows for:
- Easier maintenance of individual sections
- Clear ownership of category content
- Simpler diffs when reviewing changes
- Parallel editing of different categories

### Category Files

Files are named with numeric prefixes to control concatenation order:

```
categories/
  00-header.md              # Banner, intro, understanding section
  01-systems-administration.md
  02-productivity.md        # Productivity & Planning
  02a-legal.md              # Legal
  02b-health.md             # Health & Wellbeing
  02c-communications.md     # Communications & Writing
  02d-financial.md          # Financial Planning
  02e-career.md             # Career
  02f-business.md           # Business
  02g-privacy.md            # Privacy & Anonymity
  03-research.md
  04-argument-perspective.md
  05-context-personalization.md
  06-multi-agent-tooling.md
  07-mcp.md
  08-plugins.md
  09-slash-commands.md
  10-misc.md
```

### Building README.md

After editing category files, regenerate README.md:

```bash
python3 scripts/build_readme.py
```

This concatenates all category files in sorted order to produce the final README.md.

## Workflow for Adding New Repositories

### 1. New Repository Collection

When Daniel adds repository URLs to `scratchpad.md`, follow this workflow:

1. **Read the scratchpad** to identify new repositories
2. **Check for duplicates**: Verify each repository isn't already in the index
3. **Fetch repository information**: Use WebFetch to retrieve the README.md for each repository
4. **Extract key information**:
   - Repository name
   - Primary purpose/functionality
   - Key features (if notable)
   - Category classification

### 2. Categorization

**Important**: Each repository should belong to **one primary category only**. While some repositories may touch multiple domains, choose the most appropriate single category to avoid duplication and maintenance complexity.

When adding new repositories, consider whether they fit an existing category or whether a new category/subcategory should be created. The goal is to group repositories that explore Claude Code or the "Claude Workspace" model for similar purposes.

### 3. Editing the Correct Category File

**Always edit the specific category file**, not README.md directly:

1. Identify the correct category file in `categories/`
2. Add the repository entry in alphabetical order within that file
3. Run `python3 scripts/build_readme.py` to regenerate README.md
4. Run the pre-commit hooks or `python3 scripts/update_repo_tracking.py` to update repos.json

### 4. Entry Format

Each repository entry should follow this format:

```markdown
### Repository Name
[![View Repo](https://img.shields.io/badge/View%20Repo-blue?style=flat-square&logo=github)](https://github.com/danielrosehill/Repository-Name)

Brief description of the repository's purpose and key features (1-2 sentences).

---
```

### 5. Alphabetical Ordering

Within each category file, maintain **strict alphabetical order by repository name**. When adding new entries:

1. Find the alphabetical position within the category file
2. Insert the entry in the correct location
3. Verify ordering after insertion

### 6. Description Guidelines

Descriptions should be:
- **Concise**: 1-2 sentences maximum
- **Informative**: Clearly state what the repository does
- **Actionable**: Help users understand if this resource is relevant to their needs
- **Professional**: Use clear, technical language without marketing fluff

### 7. Duplicate Handling

When processing scratchpad.md:
- If a repository is already in any category file, skip it silently
- Do not remove it from scratchpad.md (Daniel manages scratchpad clearing)
- Note duplicates in your response to Daniel for awareness

## Quality Standards

### Repository Descriptions

- Begin with the primary function/purpose
- Include key differentiating features
- Avoid redundant phrases like "A tool for..." or "This repository contains..."
- Be specific about what the tool does

### Category Assignment

- Assign repositories to the **single most appropriate category**
- If a repository spans multiple categories, choose the primary focus
- Suggest new categories/subcategories if multiple repositories don't fit existing ones

### Consistency

- Use consistent terminology across similar repositories
- Match the tone and style of existing descriptions
- Maintain parallel structure in descriptions within the same category

## WebFetch Usage

When gathering information about new repositories:

```
WebFetch URL: https://github.com/danielrosehill/[repo-name]
Prompt: "Summarize the purpose and key features of this repository in 1-2 concise sentences suitable for an index listing."
```

## Git Operations

After updating category files:

1. Run `python3 scripts/build_readme.py` to regenerate README.md
2. Review changes to ensure accuracy
3. Commit with descriptive message: "Add [repository names] to index"
4. Push changes to GitHub (pre-push hooks will update tracking data)

## Common Tasks

### Adding a Single Repository

1. Read scratchpad.md
2. WebFetch the repository README
3. Identify the correct category file
4. Insert entry in alphabetical order within that file
5. Run `python3 scripts/build_readme.py`
6. Commit and push

### Batch Adding Multiple Repositories

1. Read scratchpad.md
2. WebFetch all repository READMEs in parallel
3. Categorize all repositories
4. Edit appropriate category files, maintaining alphabetical order
5. Run `python3 scripts/build_readme.py`
6. Commit with list of added repositories

### Reorganizing Categories

If Daniel requests category restructuring:
1. Document the new category structure
2. Create new category files or rename existing ones (maintain numeric prefixes)
3. Move repositories between category files as needed
4. Maintain alphabetical ordering within each category
5. Run `python3 scripts/build_readme.py`
6. Update this CLAUDE.md if the structure changes significantly
7. Commit with descriptive reorganization message

### Creating a New Category

1. Create a new file in `categories/` with appropriate numeric prefix
2. Add category header with title and optional image reference
3. Add repository entries in alphabetical order
4. Run `python3 scripts/build_readme.py`

## JSON Data File

The `data/repos.json` file maintains a programmatic representation of the index. To regenerate:

- Run `/build-json` or `python3 scripts/update_repo_tracking.py`

## Badge System

Repositories can have multiple badges to indicate their type and purpose:

| Badge | Color | Purpose |
|-------|-------|---------|
| `Claude Space` | Purple | Workspaces where Claude manages files/processes |
| `Agent Config` | Orange | Multi-agent configurations and orchestration |
| `Slash Commands` | Cyan | Slash command collections |
| `Non-Code` | Teal | Non-development use cases |
| `Light Touch` | Light gray | Minimal configuration/simple utilities |
| `Template` | Green | Forkable templates |
| `LAN Manager` | Blue | Network/LAN management |
| `Diary` | Pink | Diary/planning workspaces |
| `Health` | Red | Health-related workspaces |
| `Job Search` | Gold | Career/job search tools |
| `Rig` | Gray | Hardware planning |
| `Therapy` | Lavender | Therapy tracking |
| `Budget` | Gold | Budget/financial workspaces |
| `Legal` | Navy | Legal research and case management |
| `Forensics` | Dark red | Digital forensics and evidence handling |

Badge format example:
```markdown
![Claude Space](https://img.shields.io/badge/Claude-Space-purple?style=flat-square)
```

## Repository Discovery

In addition to the scratchpad workflow, you can proactively discover missing repositories by querying Daniel's GitHub account:

```bash
gh repo list danielrosehill --limit 500 --visibility public --json name,description --jq '.[] | select(.name | test("claude|Claude"; "i"))'
```

This helps identify public Claude-related repositories that may not yet be in the index. Compare results against the category files to find candidates for addition.

## Notes

- All repositories indexed here are public GitHub repositories
- This index focuses specifically on Claude Code-related projects
- Daniel maintains a separate master index for all GitHub projects (linked in README.md)
- The index serves both as documentation and as a discovery tool for the community
- **Always edit category files, never README.md directly** (it is auto-generated)
