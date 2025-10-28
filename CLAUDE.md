# Claude Code Repos Index - Repository Instructions

## Purpose

This repository serves as a curated index of Claude Code-related resources and projects shared on GitHub. It provides organized, categorized listings with descriptions to help users discover relevant tools, libraries, and configurations for Claude Code workflows.

## Repository Structure

- **`README.md`**: Main index displaying all repositories organized by category
- **`scratchpad.md`**: Staging area for new repositories to be added to the index
- **`banner.png`**: Repository banner image

## Workflow for Adding New Repositories

### 1. New Repository Collection

When Daniel adds repository URLs to `scratchpad.md`, follow this workflow:

1. **Read the scratchpad** to identify new repositories
2. **Check for duplicates**: Verify each repository isn't already in README.md
3. **Fetch repository information**: Use WebFetch to retrieve the README.md for each repository to understand its purpose
4. **Extract key information**:
   - Repository name
   - Primary purpose/functionality
   - Key features (if notable)
   - Category classification

### 2. Categorization

Organize repositories into these existing categories (or suggest new ones if needed):

- **Agent Systems & Multi-Agent Workflows**: Multi-agent systems, agent networks, orchestration
- **Configuration & Context Management**: CLAUDE.md templates, context tools, configuration managers
- **Curated Resources & Discovery**: Collections, showcases, resource lists
- **MCP & Integrations**: MCP servers, integrations, command generators
- **Security & System Administration**: Security tools, audit systems, admin utilities
- **Slash Command Libraries**: Slash command collections and libraries
- **System Management & Automation**: System tools, automation scripts, management utilities
- **Miscellaneous**: Items that don't fit other categories

### 3. Entry Format

Each repository entry should follow this format:

```markdown
### Repository Name
[![View Repo](https://img.shields.io/badge/View-Repo-blue?style=for-the-badge&logo=github)](https://github.com/danielrosehill/Repository-Name)

Brief description of the repository's purpose and key features (1-2 sentences).

---
```

### 4. Alphabetical Ordering

Within each category, maintain **strict alphabetical order by repository name**. When adding new entries:

1. Identify the correct category
2. Find the alphabetical position within that category
3. Insert the entry in the correct location
4. Verify ordering after insertion

### 5. Description Guidelines

Descriptions should be:
- **Concise**: 1-2 sentences maximum
- **Informative**: Clearly state what the repository does
- **Actionable**: Help users understand if this resource is relevant to their needs
- **Professional**: Use clear, technical language without marketing fluff

### 6. Duplicate Handling

When processing scratchpad.md:
- If a repository is already in README.md, skip it silently
- Do not remove it from scratchpad.md (Daniel manages scratchpad clearing)
- Note duplicates in your response to Daniel for awareness

## Quality Standards

### Repository Descriptions

- Begin with the primary function/purpose
- Include key differentiating features
- Avoid redundant phrases like "A tool for..." or "This repository contains..."
- Be specific about what the tool does

### Category Assignment

- Assign repositories to the most specific applicable category
- If a repository spans multiple categories, choose the primary focus
- Suggest new categories if multiple repositories don't fit existing ones

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

After updating README.md:

1. Review changes to ensure accuracy
2. Commit with descriptive message: "Add [repository names] to index"
3. Push changes to GitHub

## Common Tasks

### Adding a Single Repository

1. Read scratchpad.md
2. WebFetch the repository README
3. Determine category and alphabetical position
4. Insert entry with proper formatting
5. Commit and push

### Batch Adding Multiple Repositories

1. Read scratchpad.md
2. WebFetch all repository READMEs in parallel
3. Categorize all repositories
4. Insert all entries maintaining alphabetical order
5. Commit with list of added repositories

### Reorganizing Categories

If Daniel requests category restructuring:
1. Document the new category structure
2. Move repositories to new categories
3. Maintain alphabetical ordering within each category
4. Update this CLAUDE.md if needed
5. Commit with descriptive reorganization message

## Notes

- All repositories indexed here are public GitHub repositories
- This index focuses specifically on Claude Code-related projects
- Daniel maintains a separate master index for all GitHub projects (linked in README.md)
- The index serves both as documentation and as a discovery tool for the community