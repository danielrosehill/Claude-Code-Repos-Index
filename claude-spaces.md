# Claude Spaces

## What Are Claude Spaces?

**Claude Spaces** (also called **Claude Workspaces**) are pre-configured repository structures designed to use Claude Code as a **Conversational UI Agent (CUA)** for managing structured workflows beyond traditional software development.

Rather than treating Claude Code purely as a coding assistant, Claude Spaces leverage the agentic IDE paradigm for:

- **System Administration**: Managing servers, networks, containers, and infrastructure
- **Research & Analysis**: Conducting deep research, report parsing, and data synthesis
- **Personal Productivity**: Health tracking, budgeting, job searching, therapy notes
- **Content Creation**: Writing, blog management, documentation workflows
- **Domain-Specific Work**: Legal research, OSINT investigations, hardware planning

## Core Characteristics

A Claude Space typically includes:

| Component | Purpose |
|-----------|---------|
| **CLAUDE.md** | Context and domain-specific instructions for the workspace |
| **Slash Commands** | Pre-built commands for common tasks in that domain |
| **Sub-Agents** | Specialized agents for complex multi-step workflows |
| **Directory Structure** | Organized folders for inputs, outputs, context, and memory |
| **Workflow Documentation** | Guidance on using the space effectively |

## Why This Matters

Claude Spaces demonstrate that agentic IDEs are **general-purpose structured workflow engines**. If your work involves:

- Iterative tasks with persistent context
- Structured inputs and outputs
- Complex multi-step workflows
- Version-controlled documentation

...then the Claude Space pattern may be applicable, regardless of whether the work involves code.

## Template vs Space vs Plugin

The distinction can be fuzzy, but generally:

| Type | Primary Purpose | Typical Use |
|------|-----------------|-------------|
| **Template** | Forkable starting point | Clone and customize for your needs |
| **Space** | Persistent operational workspace | System admin, research, personal productivity |
| **Plugin** | Reusable capability extension | Add features across multiple projects |

Many repositories serve multiple purposes - a Template can become a Space once forked and populated with your data, and Spaces often include Plugin-like slash commands.

## Getting Started

1. Browse the [index](./README.md) for spaces marked with ![Claude Space](https://img.shields.io/badge/Claude-Space-purple?style=flat-square)
2. Fork a template that matches your use case
3. Customize the CLAUDE.md with your specific context
4. Add your own slash commands and agents as needed

## Related Resources

- [Claude Spaces Model](https://github.com/danielrosehill/Claude-Spaces-Model) - Conceptual documentation for the pattern
- [Claude Workspace Setup Helper](https://github.com/danielrosehill/Claude-Workspace-Setup-Helper) - Interactive tool for discovering and setting up workspaces
- [Notes on Templates and Workspaces](./notes.md) - Additional context on the approach
