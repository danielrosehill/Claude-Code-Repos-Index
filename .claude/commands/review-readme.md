Review the README and category files for quality and organization.

## Steps

1. **Rebuild README** from category files:
   ```bash
   npm run build
   ```

2. **Check alphabetical ordering** within each category file in `categories/`. Flag any repos that are out of order and fix them.

3. **Check for duplicate repos** across all category files. Each repo should appear in exactly one category.

4. **Review descriptions** for consistency:
   - Should be 1-2 sentences
   - Should clearly state what the repo does
   - Should not start with "A tool for..." or "This repository..."
   - Should use consistent tone across similar repos

5. **Review category balance**: Flag categories that are overstuffed (>15 repos) or underpopulated (<2 repos) and suggest reorganization if needed.

6. **Verify entry format** - each entry should have:
   - `### Repo Name`
   - `[![View Repo]` badge with correct GitHub URL
   - Description
   - `---` separator

7. Report findings and fix any issues found.
