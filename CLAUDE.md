# Claude Code Repos Index - Repository Instructions

## Purpose

This repository serves as a curated index of agent workspace blueprints and Claude Code-related resources shared on GitHub. It provides organized, categorized listings with descriptions to help users discover relevant tools, templates, and configurations for agentic AI workflows.

Many of the repositories in this index are **agent workspaces** — pre-configured repository environments designed for structured, domain-specific agentic AI workflows. This pattern, which I originally called "Claude Spaces," uses repository structure, context files, and Claude Code's built-in features to create effective AI work environments that go far beyond traditional codebases.

## Repository Structure

- **`README.md`**: Main index displaying all repositories (auto-generated from category files)
- **`categories/`**: Individual category files that are concatenated to build README.md
- **`scratchpad.md`**: Staging area for new repositories to be added to the index
- **`scripts/build_readme.py`**: Script to regenerate README.md from category files
- **`scripts/build_site.py`**: Unified build pipeline (README + repos.json + tagged_repos.json + site state tracking)
- **`scripts/update_repo_tracking.py`**: Script to update repo counts and repos.json
- **`data/repos.json`**: Programmatic representation of the index (category-based)
- **`data/tag_rules.json`**: Auto-tagging rules mapping categories and keywords to tags
- **`data/site_state.json`**: Tracks what has been deployed to the site (repo manifest, change history)
- **`docs/`**: Astro build output (deployed via GitHub Pages)
- **`images/`**: Category banner images

## Astro Site Architecture

The deployed site is built with **Astro** (static site generator). Source files live in `src/`:

- **`src/layouts/BaseLayout.astro`**: Shared HTML shell (head, fonts, CSS import)
- **`src/components/Nav.astro`**: Shared top navigation (single source of truth)
- **`src/components/Footer.astro`**: Shared footer
- **`src/styles/global.css`**: All site styles
- **`src/data/categoryIcons.ts`**: Shared category icon SVGs
- **`src/pages/`**: All page templates (Astro generates `docs/` from these)
  - `index.astro` — Main index with search/filter/pagination
  - `about/index.astro` — About page
  - `plugins/index.astro` — Plugins Marketplace page
  - `ideas/claude-spaces/` — Claude Spaces landing + subpages
  - `ideas/non-code/` — Non-Code Uses landing + subpages
  - `repos/[...slug].astro` — Dynamic route generating all repo detail pages from `tagged_repos.json`
- **`public/`**: Static assets copied to build output (images, JSON data files)
- **`astro.config.mjs`**: Astro config (outputs to `docs/`)

**To add/edit nav links, footer, or layout**: Edit the component in `src/components/` — changes apply to all 135+ pages automatically.

**To add a new static page**: Create a `.astro` file in `src/pages/` using `BaseLayout`.

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
  08-plugins.md             # GENERATED — see below, do not hand-edit
  09-slash-commands.md
  10-misc.md
```

### `08-plugins.md` is generated, not authored

`scripts/sync_marketplace.py` fetches `.claude-plugin/marketplace.json` from
`danielrosehill/Claude-Code-Plugins` and regenerates `categories/08-plugins.md`
wholesale. Hand-written entries there are silently destroyed on the next sync or
build.

To get a plugin into the index, register it in the **marketplace repo** — it then
flows here automatically. A plugin repo that is not in the marketplace has no
route into the Plugins category; file it under its topical category instead, or
add it to the marketplace first.

### Building the Site

After editing category files, run the full build pipeline:

```bash
npm run build
```

This runs two steps:
1. **`npm run build:data`** (`python3 scripts/build_site.py`): Builds README.md, repos.json, tagged_repos.json, copies data to `public/`
2. **`npm run build:site`** (`astro build`): Generates all HTML pages from Astro templates into `docs/`

For development with hot reload: `npm run dev`

To run just the data pipeline (no site rebuild): `python3 scripts/build_site.py`

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

When adding new repositories, consider whether they fit an existing category or whether a new category/subcategory should be created. The goal is to group repositories that explore Claude Code or the agent workspace model for similar purposes.

### 3. Editing the Correct Category File

**Always edit the specific category file**, not README.md directly:

1. Identify the correct category file in `categories/`
2. Add the repository entry in alphabetical order within that file
3. Run `npm run build` to rebuild README, site data, and Astro site

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

1. Run `npm run build` to regenerate README.md and rebuild the Astro site
2. Review changes to ensure accuracy
3. Commit with descriptive message: "Add [repository names] to index"
4. Push changes to GitHub (pre-push hooks will update tracking data)

## Common Tasks

### Adding a Single Repository

1. Read scratchpad.md
2. WebFetch the repository README
3. Identify the correct category file
4. Insert entry in alphabetical order within that file
5. Run `npm run build`
6. Commit and push

### Batch Adding Multiple Repositories

1. Read scratchpad.md
2. WebFetch all repository READMEs in parallel
3. Categorize all repositories
4. Edit appropriate category files, maintaining alphabetical order
5. Run `npm run build`
6. Commit with list of added repositories

### Reorganizing Categories

If Daniel requests category restructuring:
1. Document the new category structure
2. Create new category files or rename existing ones (maintain numeric prefixes)
3. Move repositories between category files as needed
4. Maintain alphabetical ordering within each category
5. Run `npm run build`
6. Update this CLAUDE.md if the structure changes significantly
7. Commit with descriptive reorganization message

### Creating a New Category

1. Create a new file in `categories/` with appropriate numeric prefix
2. Add category header with title and optional image reference
3. Add repository entries in alphabetical order
4. Run `npm run build`

## JSON Data Files

- `data/repos.json` - Category-based index (generated by `build_site.py`)
- `docs/tagged_repos.json` - Tag-based index for the site (generated by `build_site.py`)
- `data/site_state.json` - Deployment state tracking with change history
- `data/tag_rules.json` - Configurable rules for auto-tagging repos

To regenerate all data and rebuild the site: `npm run build`

## Badge System

Repositories can have multiple badges to indicate their type and purpose:

| Badge | Color | Purpose |
|-------|-------|---------|
| `Agent Workspace` | Purple | Pre-configured agent workspaces for domain-specific workflows |
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
![Agent Workspace](https://img.shields.io/badge/Agent-Workspace-purple?style=flat-square)
```

## Repository Discovery

In addition to the scratchpad workflow, run the discovery script to find public
repos that are not yet in the index:

```bash
python3 scripts/discover_new_repos.py          # names matching /claude/
python3 scripts/discover_new_repos.py --all    # every public repo
```

Results are written to `data/unindexed_repos.json`.

Two traps this script has already fallen into, both fixed — do not reintroduce
either:

- **`gh repo list --limit` must exceed the account's total public repo count**
  (>1050 as of Aug 2026). `gh` truncates silently, so a limit of 500 returned a
  plausible-looking list while hiding every older candidate.
- **The default pattern only matches `claude` in the repo *name*.** Genuinely
  Claude Code-related repos named otherwise — `Document-As-You-Go`,
  `Aliexpress-Shopper`, `Android-Media-Importer`, `Israel-Phonebook-Manager` —
  are invisible to it. Periodically re-run with `--all`, or grep descriptions for
  `claude|agentic|slash command|subagent|agent workspace`, and triage by hand.

Compare results against the category files before adding anything; the script
does not know which repos were deliberately excluded.

## The deployed site

Live at **https://claude.danielrosehill.com**, deployed by **Vercel** on push to
`main` (`vercel.json` sets `outputDirectory: docs`). `docs/` is the committed
Astro build output — so **run `npm run build` and commit the result**; this repo
is not one where the build can be left to CI.

`npm run build` is three steps: `build:data` (the Python pipeline that regenerates
`README.md`, the split markdown pages and `data/*.json`), `build:site` (Astro), and
`check:links`, which fails the build on a broken internal link.

**Repo detail pages come from Astro, not Python.** `src/pages/repos/[...slug].astro`
owns `/repos/<slug>/`. `build_site.py` used to render those pages too — 237 of them,
from a duplicate HTML template — and `astro build` then overwrote every one. The
Python copies still carried the pre-rename slug and none of the SEO metadata, and
editing that template had no visible effect whatsoever. Removed 2026-08-10. If you
need to change how a repo page looks, the `.astro` file is the only place.

### SEO and machine-readable surfaces

`astro.config.mjs` sets `site:` — this is load-bearing. Without it canonical URLs,
Open Graph URLs and `@astrojs/sitemap` all silently produce nothing.

`BaseLayout.astro` takes `description`, `image`, `isHome` and `schema` props and
emits the canonical link, Open Graph and Twitter tags, and JSON-LD. **Pass a
`description` on every new page** — the fallback is the site-wide one, which is
fine for a stray page but poor if it ends up on many.

| Surface | Source | Notes |
| --- | --- | --- |
| `/sitemap-index.xml` | `@astrojs/sitemap` | every page, generated |
| `/robots.txt` | `public/robots.txt` | static; points at the sitemap |
| `/llms.txt` | `src/pages/llms.txt.ts` | generated from `tagged_repos.json`, cannot drift |
| `/browse/` | `src/pages/browse/index.astro` | static listing of every repo |
| `/og-image.png` | `public/` | 1200×630 |

**Why `/browse/` exists:** the home page renders its repo list client-side from
`tagged_repos.json`, so a crawler that does not run JS sees only "Loading
repositories…" and finds no repo links at all. `/browse/` is the static
counterpart that puts all 236 in the initial HTML. Keep it working; do not fold it
into the client-rendered index.

### Dates: both are persisted, deliberately

`created_date` (real GitHub creation date, `data/repo_created_dates.json`, filled
by `scripts/fetch_created_dates.py`) drives the site's default "Newest" sort.
`added_date` (`data/repo_added_dates.json`) is when the repo entered this index.

Both files exist because both values used to be recomputed as *today* on every
build whenever a lookup missed — `site_state.json` history is capped at 50 entries,
so older repos fell off and got restamped. On 2026-08-10 that had left 125 of 236
repos claiming they were created that day, which made the default sort meaningless.
Never reintroduce a `datetime.now()` fallback that is not written back to disk.

After adding repos, run `python3 scripts/fetch_created_dates.py` before building,
or the new entries sort to the top with a fabricated date.

## This repo's own name

Canonical slug: **`danielrosehill/Claude-Code-Projects-Index`**. It has been
renamed twice, and both former slugs still resolve via GitHub's rename redirect:

| Former slug | Status |
| --- | --- |
| `Claude-Code-Repos-Index` | redirects |
| `Claude-Agent-Blueprints` | redirects |

The redirects make staleness invisible — a clone whose `origin` points at an old
slug fetches and pushes perfectly well, and `gh api repos/<old-slug>` returns
`200`. Resolve `.full_name` before trusting any slug. Consequences already hit:
the local checkout sat 130 commits behind on a stale remote URL, and `10-misc.md`
carried an entry for "Claude Agent Blueprints" — this repo listing *itself* under
a dead name, with a description that had drifted. All three former names are in
`SKIP_REPOS` in `scripts/discover_new_repos.py`.

The local working copy's directory name may also lag the repo name; it is not
authoritative.

## Notes

- All repositories indexed here are public GitHub repositories
- This index focuses specifically on Claude Code-related projects
- Daniel maintains a separate master index for all GitHub projects (linked in README.md)
- The index serves both as documentation and as a discovery tool for the community
- **Always edit category files, never README.md directly** (it is auto-generated)
