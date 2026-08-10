import fs from 'node:fs';
import path from 'node:path';

/**
 * /llms.txt — the site in a form an LLM or agent can read in one request.
 *
 * Generated at build time from the same tagged_repos.json the site renders, so it
 * cannot drift from the index. Follows the llms.txt convention: H1, a blockquote
 * summary, then link sections.
 */
export async function GET() {
  const dataPath = path.join(process.cwd(), 'docs', 'tagged_repos.json');
  const repos = JSON.parse(fs.readFileSync(dataPath, 'utf-8')) as Array<{
    name: string; url: string; description: string; slug: string;
    category: string; category_group: string;
  }>;

  const byCategory = new Map<string, typeof repos>();
  for (const repo of repos) {
    if (!byCategory.has(repo.category)) byCategory.set(repo.category, []);
    byCategory.get(repo.category)!.push(repo);
  }

  const sections = [...byCategory.entries()]
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([category, list]) => {
      const lines = list
        .slice()
        .sort((a, b) => a.name.localeCompare(b.name))
        .map((r) => `- [${r.name}](${r.url}): ${r.description.replace(/\s+/g, ' ').trim()}`)
        .join('\n');
      return `## ${category}\n\n${lines}`;
    })
    .join('\n\n');

  const body = `# Claude Code Projects Index

> A curated index of ${repos.length} open-source Claude Code repositories by Daniel Rosehill —
> agent workspaces, plugins, slash commands and MCP tooling, spanning software
> development and non-code domains such as sysadmin, legal, health and research.
> Site: https://claude.danielrosehill.com

Every entry below is a public GitHub repository. The index is maintained in
https://github.com/danielrosehill/Claude-Code-Projects-Index and rebuilt from
markdown category files, so this file always matches the live site.

## Machine-readable data

- [Full index as JSON](https://claude.danielrosehill.com/tagged_repos.json): every repo with name, url, description, tags, category, category_group, slug, created_date and added_date.
- [Category-grouped JSON](https://claude.danielrosehill.com/repos.json): the same repos nested under their categories.
- [Category hierarchy](https://claude.danielrosehill.com/categories.json): category groups, categories and slugs.
- [All repositories, one page](https://claude.danielrosehill.com/browse/): static HTML listing of every repo, grouped by category.
- [Sitemap](https://claude.danielrosehill.com/sitemap-index.xml): every page on the site.

## Installing the plugins

Most entries tagged "Plugin" are distributed through one Claude Code marketplace.
To install, run inside Claude Code:

    /plugin marketplace add danielrosehill/Claude-Code-Plugins
    /plugin install <plugin-name>@danielrosehill

Marketplace source: https://github.com/danielrosehill/Claude-Code-Plugins
Install guide: https://claude.danielrosehill.com/plugins/

${sections}
`;

  return new Response(body, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
}
