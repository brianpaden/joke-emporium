# Quick Import Test Workflow

Import a small batch of jokes for testing the complete workflow from import to production.

## Purpose

Test the full import pipeline with a manageable dataset:
- Import from source
- Review staging data
- Approve jokes
- Merge to production
- Verify results

## Steps

1. Import 100 jokes from taivop dataset:
   ```
   uv run python -m joke_emporium.importers.cli import taivop --max-records 100
   ```

2. List the import batch and get the import ID

3. Inspect the staging jokes to see what was imported

4. Approve all jokes with decent scores:
   ```
   uv run python -m joke_emporium.importers.cli approve-batch <import-id> --min-score 500
   ```

5. Merge approved jokes to production:
   ```
   uv run python -m joke_emporium.importers.cli merge <import-id>
   ```

6. Show summary statistics:
   - Total jokes imported
   - Number approved
   - Number rejected/duplicates
   - Number merged to production

## Expected Outcome

A working demonstration of the import workflow with real data, suitable for testing or demonstrating the system.
