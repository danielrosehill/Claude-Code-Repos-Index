Sync the index by discovering and adding new repositories. This is the automated index sync workflow.

## Step 1: Discover new repos

Run the discovery script to find Claude-related repos not yet in the index:

```bash
python3 scripts/discover_new_repos.py
```

If the user specified `--all`, pass that flag to scan all public repos.

## Step 2: Review the list

Show the user the list of unindexed repos and ask if they want to:
- Add **all** of them
- Select specific ones to add
- Skip any that shouldn't be in this index (e.g., forks, experiments, deprecated)

Add any repos they want to permanently skip to the `SKIP_REPOS` set in `scripts/discover_new_repos.py`.

## Step 3: Fetch and categorize

For each repo to add, in parallel:
1. **WebFetch** the repo's GitHub page to read the README
2. Determine the **single best category** by matching against existing category file headings:
   - Systems Administration (`01-systems-administration.md`)
   - Productivity & Planning (`02-productivity.md`)
   - Legal (`02a-legal.md`)
   - Health & Wellbeing (`02b-health.md`)
   - Communications & Writing (`02c-communications.md`)
   - Financial Planning (`02d-financial.md`)
   - Career (`02e-career.md`)
   - Business (`02f-business.md`)
   - Privacy & Anonymity (`02g-privacy.md`)
   - Technology & Hardware (`02h-technology.md`)
   - Marketing (`02i-marketing.md`)
   - Research (`03-research.md`)
   - Argument and Perspective Exploration (`04-argument-perspective.md`)
   - Context and Personalization (`05-context-personalization.md`)
   - Multi-Agent Tooling (`06-multi-agent-tooling.md`)
   - MCP (`07-mcp.md`)
   - Plugins (`08-plugins.md`)
   - Slash Commands (`09-slash-commands.md`)
   - Miscellaneous (`10-misc.md`)
3. Write a **concise 1-2 sentence description** based on the README
4. If no existing category fits, suggest creating a new one

## Step 4: Present categorization for approval

Show the user a table of:
| Repo | Category | Description |

Ask them to confirm or adjust before proceeding.

## Step 5: Insert entries

For each approved repo, edit the appropriate category file:
- Insert in **alphabetical order** within the file
- Use this exact format:

```markdown
### Repository Name
[![View Repo](https://img.shields.io/badge/View%20Repo-blue?style=flat-square&logo=github)](https://github.com/danielrosehill/Repository-Name)

Brief description here.

---
```

## Step 6: Fetch creation dates for the new repos

The site's default "Newest" sort keys on `created_date`. A repo missing from
`data/repo_created_dates.json` falls back to today's date and sorts to the top
with a fabricated value, so do this *before* building:

```bash
python3 scripts/fetch_created_dates.py
```

## Step 7: Build and deploy

```bash
npm run build
```

This runs the data pipeline, then Astro, then `scripts/check_links.py` — which
fails the build if any internal link points at a page that was not generated.

## Step 8: Commit and push

Commit all changes with a descriptive message listing the added repos, then push:

```bash
git add -A
git commit -m "Add [N] new repositories to index: [list names]

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
git push
```

## Notes

- Each repo belongs to ONE category only
- Maintain strict alphabetical ordering within each category file
- Descriptions should be concise, informative, and professional
- Skip repos that are clearly experiments, empty, or deprecated
- If a repo spans multiple categories, choose the primary focus
