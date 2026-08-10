# Essay pages name 24 repos that no longer exist

**Verified: 2026-08-10.**

The hand-written pages under `src/pages/ideas/` link repo names as
`<a class="repo-link" href="/repos/<slug>/">`. Those detail pages are generated
from `docs/tagged_repos.json`, so a link only resolves while the repo is in the
index. 24 of them pointed at pages that are never generated — 26 dead links, since
two repos are mentioned twice.

## They are gone, not merely unindexed

Checked against **all 2444 repos on the account, public and private**
(`gh repo list danielrosehill --limit 3000`), matching on a slugified name. Zero
matches. These are not private, not archived, and not renamed to anything whose
name still slugifies the same way — they were deleted.

Note that `~/repos/github/` still holds local clones of at least two of them
(`Claude-Legal-Aid-Clinic`, `Claude-OSINT-Investigator`) whose `origin` points at
a URL that now 404s. A local clone is not evidence the remote exists.

## The list

```
claude-blog-manager                                 claude-linux-server-manager
claude-budget-workspace-template                    claude-media-monitor
claude-code-lan-manager                             claude-news-fetcher-media-monitoring-system
claude-code-lawyer                                  claude-osint-investigator
claude-communications-strategist-template           claude-proxmox-manager-template
claude-decision-evaluation-framework                claude-purchasing-assistant
claude-deep-research-template-implementation-template   claude-report-parsing-space-template
claude-diary-planner-template                       claude-server-manager-template
claude-evidence-assistant                           claude-space-self-ideator
claude-health-helper                                claude-stack-research-workspace
claude-home-assistant-manager-template              claude-therapy-tracker
claude-legal-aid-clinic                             claude-writing-space-template
```

## What was done

Each dead link became `<span class="repo-mention">` — the prose still reads, but
nothing 404s. The build now passes a full internal link check (4283 links, zero
broken).

## What is still wrong

**The prose describes software that no longer exists.** Unlinking fixed the
navigation defect, not the content defect. Sentences like "Claude Evidence
Assistant focuses specifically on evidence handling and chain-of-custody
documentation" still assert a repo a reader cannot obtain. Rewriting those
paragraphs is an editorial call and was deliberately left alone.

Some look like they were superseded rather than abandoned — `Stack-Search-Plugin`
still describes itself as spawning workspaces "from the
Claude-Stack-Research-Workspace template", and `claude-purchasing-assistant`
plausibly became `Claude-Purchasing-Plugin`. If a successor exists, repointing the
mention at it is better than deleting the sentence.

## Preventing recurrence

The link check is worth keeping. Any repo dropped from the index silently breaks
every essay-page link to it, and nothing in the build warns. Running a crawl of
`docs/` for internal `href`s that do not resolve to a generated file catches it in
one pass.
