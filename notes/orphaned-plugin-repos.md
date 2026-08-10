# Orphaned plugin repos

**Verified: 2026-08-10.**

24 public repos named `*-plugin` are in **neither** the marketplace manifest
(`danielrosehill/Claude-Code-Plugins`) **nor** this index. They are invisible to
both discovery routes, so nothing will surface them again on its own.

## Why they fall through

`categories/08-plugins.md` is regenerated wholesale from the marketplace manifest
by `scripts/sync_marketplace.py`. The Plugins category therefore mirrors the
marketplace exactly — a plugin repo that was never registered there has no route
into the index, and hand-adding it to `08-plugins.md` is destroyed on the next
build.

`scripts/discover_new_repos.py` compares GitHub against the *category files*, so
once the marketplace is in sync these repos do show up as unindexed — but they
read as ordinary unindexed repos, with nothing marking them as ex-plugins.

## The list

Sorted newest first. Dates are last push, which is the best available staleness
signal.

| Repo | Last push | Note |
| --- | --- | --- |
| `Flood-Data-Analyst-plugin` | 2026-04-23 | no description |
| `audio-voice-id-plugin` | 2026-04-19 | speaker diarization, voice enrollment |
| `linux-desktop-plugin` | 2026-04-19 | KDE/Plasma desktop management |
| `mqtt-observability-plugin` | 2026-04-18 | no description |
| `lan-manager-plugin` | 2026-04-18 | LAN scanning / device discovery |
| `github-research-plugin` | 2026-04-16 | no description |
| `context-toolkit-plugin` | 2026-04-16 | CONTEXT.md workflow system |
| `brainstorm-solutions-plugin` | 2026-04-10 | no description |
| `Stack-Search-Plugin` | 2026-04-10 | spawns stack-search workspaces |
| `docker-manager-plugin` | 2026-04-09 | containers, Compose, volumes |
| `conda-manager-plugin` | 2026-04-09 | supersedes `conda-management-plugin`? |
| `synology-manager-plugin` | 2026-04-09 | Synology NAS over SSH |
| `user-manual-plugin` | 2025-12-31 | doc-generation prompt |
| `writing-editing-plugin` | 2025-12-16 | |
| `tech-research-plugin` | 2025-12-16 | |
| `learning-plugin` | 2025-12-16 | |
| `filesystem-org-plugin` | 2025-12-16 | |
| `linux-server-plugin` | 2025-12-16 | |
| `git-github-plugin` | 2025-12-16 | |
| `ai-tools-plugin` | 2025-12-16 | |
| `diary-planner-plugin` | 2025-12-16 | |
| `general-dev-plugin` | 2025-11-15 | |
| `server-management-plugin` | 2025-11-15 | |
| `conda-management-plugin` | 2025-11-15 | superseded by `conda-manager-plugin`? |

## What is unresolved

Whether these are **retired** or merely **unregistered** has not been
established, and it is a curation call rather than something to infer:

- The lowercase-hyphenated naming (`docker-manager-plugin`) predates the current
  `Claude-*-Plugin` convention used across the marketplace, which suggests an
  older generation.
- Several look superseded by marketplace cluster plugins — `linux-desktop-plugin`
  against `Claude-Desktop-Manager-Plugin`, `server-management-plugin` against
  `Claude-Sysadmin-Homelab-Plugin`, `conda-management-plugin` against
  `conda-manager-plugin`.
- But that mapping was **not** verified against the plugins' actual contents.
  Treat the "superseded by" guesses above as hypotheses to check, not findings.

Three outcomes per repo, whichever fits: register it in the marketplace (it then
flows into the index automatically), archive it, or add it to `SKIP_REPOS` in
`scripts/discover_new_repos.py` so it stops resurfacing as a false candidate.
