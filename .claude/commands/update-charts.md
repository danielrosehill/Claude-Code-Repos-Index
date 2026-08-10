Update the repo count tracking chart.

1. Run the tracking script to update the count history and regenerate the chart:

```bash
python3 scripts/update_repo_tracking.py
```

2. Verify the chart was updated:

```bash
ls -la charts/repo-count-chart.png
```

3. Check that the data point count in `data/repo-count-history.json` matches the actual repo count in the category files.

4. If the chart PNG looks stale or the count seems wrong, investigate and report.
