Review the frontend site to ensure new repos are properly displayed and categories are well-organized.

## Steps

1. **Rebuild the site** to ensure latest data:
   ```bash
   npm run build
   ```

2. **Check tagged_repos.json** for category distribution:
   - Read `docs/tagged_repos.json`
   - Count repos per category and per tag
   - Flag any repos with missing or generic descriptions
   - Flag any repos missing tags (only having "Documentation" as a fallback tag)

3. **Review categories.json** grouping:
   - Read `data/categories.json`
   - Verify the group/category hierarchy makes sense
   - Check that all category files have corresponding entries
   - Suggest improvements to grouping if categories have shifted

4. **Check tag_rules.json** coverage:
   - Read `data/tag_rules.json`
   - Identify repos that might benefit from additional keyword rules
   - Suggest new tag rules for untagged or poorly-tagged repos

5. **Verify repo detail pages** are generated:
   - Confirm `docs/repos/` has a directory for every repo in tagged_repos.json
   - Spot-check 3-5 recent additions for correct content

6. **Check site_state.json** for recent changes:
   - Read `data/site_state.json` history
   - Confirm recent additions are tracked
   - Report what changed since last build

7. Report findings and implement any fixes needed.
