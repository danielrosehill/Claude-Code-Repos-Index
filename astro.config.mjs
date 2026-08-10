import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// `site` is required for canonical URLs, Open Graph tags and the sitemap —
// without it Astro emits relative URLs only and @astrojs/sitemap is a no-op.
export default defineConfig({
  site: 'https://claude.danielrosehill.com',
  outDir: './docs',
  build: {
    format: 'directory',
  },
  integrations: [sitemap()],
});
