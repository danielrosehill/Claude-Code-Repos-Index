Verify data files are in sync with category files and rebuild the frontend.

## Steps

1. **Run the full build pipeline**:
   ```bash
   npm run build
   ```

2. **Cross-check repo counts**:
   - Count repos in category files (count `### ` headings, excluding the category `# ` headings)
   - Compare against `data/repos.json` total
   - Compare against `docs/tagged_repos.json` total
   - Compare against `data/site_state.json` total_repos
   - All four counts must match. If they don't, investigate and fix.

3. **Verify tagged_repos.json completeness**:
   - Every repo in category files should appear in `docs/tagged_repos.json`
   - Every repo should have at least one tag
   - Every repo should have a valid `category` and `category_slug`

4. **Verify repo detail pages**:
   - Count directories in `docs/repos/` — should match total repo count
   - Spot-check a few pages exist and have correct content

5. **Check categories.json** in `data/categories.json`:
   - All categories from category files should be represented
   - Slugs should be consistent

6. Report any discrepancies found and fix them.
