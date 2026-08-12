# Dead GitHub links on the live site

**Verified: 2026-08-10**, by requesting all 239 distinct
`github.com/danielrosehill/*` URLs in the built site and re-checking the failures
through an authenticated `gh`.

Nine were unopenable by a visitor. Nothing in the build had ever noticed: a
deleted repo still renders a perfectly normal "View Repo" badge.

## Deleted vs private — they look identical

GitHub returns **404 for a private repo just as for a missing one**. An anonymous
check cannot tell them apart, and an authenticated check makes both look fine.
You need both:

| Anonymous | Authenticated | Meaning |
| --- | --- | --- |
| 404 | 404 | deleted |
| 404 | 200 | private — exists, but every visitor gets a 404 |

`scripts/check_external_links.py` does exactly this. It is deliberately **not**
wired into `npm run build` — one request per repo, and it would fail the build
offline. Run it periodically and after bulk additions.

## Deleted — entries removed

| Entry | Repo | Was in | Possible successor |
| --- | --- | --- | --- |
| Claude Code Context Toolkit | `Claude-Code-Context-Toolkit` | 05-context | `context-toolkit-plugin` (public, unindexed) |
| Claude Task Manager | `Claude-Task-Manager` | 06-multi-agent | `Claude-Task-Queuer-Plugin` — **already indexed**, so this was a dead duplicate |
| Claude Code Linux Notes | `Claude-Code-Linux-Notes` | 06-multi-agent | none found |
| Claude File Organiser Super Slash | `Claude-File-Organiser-Super-Slash` | 09-slash-commands | none found |
| Claude Code Marketplace Hub | `claude-code-marketplace` | 10-misc | `Claude-Code-Plugins` covers the marketplace |
| Claude Local AI Agent Research | `Claude-Local-AI-Agent-Research` | 10-misc | `Local-AI-Agent-Resources` (public, unindexed) |

The successor column is **inference from names and descriptions, not verified
equivalence**. Where a successor is real, re-adding it deliberately is better than
having restored the old entry.

## Private — left in place, decision needed

These exist and are linked from the index, so every visitor gets a 404:

- `Claude-Repo-Mgmt-Plugin` — in `08-plugins.md`, which is generated from the
  marketplace manifest. Fixing it means publishing the repo or removing it from
  `Claude-Code-Plugins`; editing the category file does nothing.

Publishing them is probably the intent, since they were indexed at all. Left
untouched rather than guessed at.

**Resolved 2026-08-12:** `Habits-Of-Claude` was in this list from 2026-08-10; it was
made public, so the `05-context-personalization.md` link now works. The entry there
needed no edit — the index stores no visibility field, it just links out.

## Unresolved: the model repo the site is built around

**`Claude-Agent-Workspace-Model` is deleted**, and it is referenced **11 times**
across `src/pages/` — the home page hero ("The Agent Workspace Model →"), the
About page, and most of the Claude Spaces section, including a code block telling
the reader to `Fetch https://github.com/danielrosehill/Claude-Agent-Workspace-Model`.

It is the conceptual spine of the site: pages describe it as "the reference
template that all these workspaces follow".

Not touched — this needs an editorial decision, not a link fix:

1. **Restore/republish** the repo, and every reference works again.
2. **Repoint** at `Claude-Agent-Workspace-Generator` (public, indexed under
   Multi-Agent Tooling), which generates workspaces conforming to "Agent Workspace
   Model v1.1" — so the spec may live there now. *Not verified.*
3. **Rewrite** the Claude Spaces narrative around whatever now holds the pattern.

Because these references sit in `src/pages/` rather than `categories/`,
`check_external_links.py` does not cover them; it only reads the category files.
Widening it to crawl the built site would catch this class of rot too.
