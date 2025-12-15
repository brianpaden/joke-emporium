# Joke Emporium Import Framework

## Quick Start

The import framework is ready to use! Here's how to get started:

### 1. Run the Example Importer

```bash
# Run the example importer (imports 2 sample jokes)
uv run python src/joke_emporium/importers/example_importer.py
```

### 2. View Imported Data

```bash
# List all import batches
task import:list

# Inspect a specific import (use the import_id from list command)
uv run python -m joke_emporium.importers.cli inspect <import-id>
```

### 3. CLI Commands

```bash
# List all available import commands
task --list | grep import

# Import from taivop (Sprint 2 - not yet implemented)
task import:taivop

# List import batches
task import:list

# Inspect import
uv run python -m joke_emporium.importers.cli inspect <import-id>

# Approve a joke
uv run python -m joke_emporium.importers.cli approve <staging-id>

# Reject a joke
uv run python -m joke_emporium.importers.cli reject <staging-id> "reason"

# Delete an import batch
uv run python -m joke_emporium.importers.cli delete <import-id> --yes
```

## Creating a New Importer

To add a new data source:

1. **Copy the example:**
   ```bash
   cp src/joke_emporium/importers/example_importer.py src/joke_emporium/importers/your_source.py
   ```

2. **Update the class:**
   ```python
   class YourSourceImporter(BaseImporter):
       source_name = "your-source-name"
       source_url = "https://source.com"
   ```

3. **Implement three methods:**
   - `download()` - Download the data
   - `parse()` - Parse into dictionaries
   - `transform()` - Convert to Joke models

4. **Test it:**
   ```bash
   uv run python src/joke_emporium/importers/your_source.py
   ```

5. **Add CLI support** (in `cli.py`):
   ```python
   elif source == "your-source":
       from joke_emporium.importers.your_source import YourSourceImporter
       # ...
   ```

See [example_importer.py](src/joke_emporium/importers/example_importer.py) for a complete working example.

## Architecture

### Two-Database System

**Staging Database** (`data/staging.db`)
- Receives all imports
- Allows validation and review
- Tracks import provenance
- Preserves original data

**Production Database** (`data/jokes.db`)
- Clean, validated jokes only
- No changes to existing schema
- Ready for application use

### Import Pipeline

```
Source → Download → Parse → Transform → Validate → Staging → Review → Production
```

### Database Schema

**ImportBatchDB**
- Tracks each import operation
- Statistics (total, successful, failed)
- Validation status

**StagingJokeDB**
- Extended joke model
- Import tracking fields
- Validation metadata
- Original source data (JSON)

## Files and Structure

```
src/joke_emporium/
├── importers/
│   ├── __init__.py
│   ├── base.py              # Base importer class
│   ├── models.py            # Import models
│   ├── cli.py               # CLI interface
│   └── example_importer.py  # Working example
├── db/
│   ├── staging.py           # Staging database operations
│   └── models/
│       └── staging.py       # Staging database models
└── validation/              # (Future: validation rules)

tests/
├── test_importers/
│   ├── test_models.py       # 11 tests
│   └── test_base.py         # 11 tests
└── conftest.py              # Shared fixtures
```

## Testing

```bash
# Run all tests
task test

# Run importer tests only
uv run pytest tests/test_importers/ -v

# Run with coverage
task test:coverage
```

**Current status:** 22/22 tests passing ✅

## Documentation

- [IMPORT_PLAN.md](docs/IMPORT_PLAN.md) - Complete import plan (all 4 sprints)
- [IMPORT_SPRINT1_SUMMARY.md](docs/IMPORT_SPRINT1_SUMMARY.md) - Sprint 1 completion summary
- [TESTING_STANDARDS.md](docs/TESTING_STANDARDS.md) - Testing guidelines
- [DATA_SOURCES.md](docs/DATA_SOURCES.md) - Available data sources

## What's Implemented (Sprint 1) ✅

- [x] Base importer framework
- [x] Import models (metadata, progress, validation)
- [x] Staging database schema
- [x] Staging database operations
- [x] CLI interface (7 commands)
- [x] Task commands integration
- [x] Example importer (working)
- [x] Comprehensive tests (22 tests)
- [x] Full documentation

## What's Next (Sprint 2)

Sprint 2 will implement the **taivop/joke-dataset** importer:

- Download 200k jokes from GitHub
- Parse JSON files
- Map to Joke models
- Handle multiple formats
- Source-specific validation

This will provide real-world data for the joke emporium!

## Example Output

```
$ uv run python src/joke_emporium/importers/example_importer.py
INFO:joke_emporium.importers.base:Starting import from example-jokes (import_id=...)
INFO:joke_emporium.importers.base:Downloading source data...
INFO:joke_emporium.importers.base:Downloaded to temp\imports\example-jokes\example_jokes.json
INFO:joke_emporium.importers.base:Parsing and transforming data...
INFO:joke_emporium.importers.base:Import complete: 2 successful, 0 failed out of 2 total

============================================================
Import Complete!
============================================================
Import ID: c63889fa-cf48-4ca7-b476-52362a418f95
Total: 2
Successful: 2
Failed: 0

$ task import:list
Found 1 import batch(es):

Import ID                              Source          Date            Total  Success  Failed  Status
----------------------------------------------------------------------------------------------------------------------------------
c63889fa-cf48-4ca7-b476-52362a418f95   example-jokes   2025-12-15...   2      2        0       pending
```

## Support

For issues or questions:
- Check the [documentation](docs/)
- Review the [example importer](src/joke_emporium/importers/example_importer.py)
- Run the test suite: `task test`
- Inspect the code in [base.py](src/joke_emporium/importers/base.py)

## License

MIT - See main project LICENSE file
