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

## Policy-Based Auto-Approval

The Policy Engine enables automated review of staging jokes, dramatically reducing manual review time.

### Quick Start

After importing jokes, apply policies to auto-approve/reject them:

```bash
# Apply default policies with preview
uv run python -m joke_emporium.importers.cli apply-policies <import-id> --dry-run

# Apply default policies
uv run python -m joke_emporium.importers.cli apply-policies <import-id>

# Use custom policy configuration
uv run python -m joke_emporium.importers.cli apply-policies <import-id> --config config/policies/strict.yaml
```

### Benefits

For a typical import of 195k jokes from taivop dataset:
- Manual review: ~270 hours (5 seconds per joke)
- With policies: ~10 hours (reviewing only flagged jokes)
- Time savings: 96% reduction in review time

### How It Works

Policies are defined in YAML files with three types of rules:

1. **Auto-Approve**: Automatically approve jokes matching quality/safety criteria
2. **Auto-Reject**: Automatically reject low-quality, spam, or deleted content
3. **Flag for Review**: Mark borderline content for manual inspection

Policies use first-match-wins precedence, evaluating in order: approve → reject → flag.

### Configuration Structure

```yaml
policies:
  auto_approve:
    - name: "high_quality_safe"
      conditions:
        - weighted_avg_funniness: ">= 80"
        - total_ratings_count: ">= 10"
        - flags.nsfw: "false"
      action: approve
      reason: "High quality with sufficient ratings"
      priority: 1

  auto_reject:
    - name: "deleted_content"
      conditions:
        - flags.deleted: "true"
      action: reject
      reason: "Content was deleted from source"

  flag_for_review:
    - name: "borderline_quality"
      conditions:
        - weighted_avg_funniness: ">= 50"
        - weighted_avg_funniness: "< 80"
      action: flag
      reason: "Moderate quality - needs review"
```

### Supported Operators

| Operator | Description | Example | Use Case |
|----------|-------------|---------|----------|
| `==` | Equality | `maturity_rating: "G"` | Exact match |
| `!=` | Inequality | `flags.nsfw: "!= true"` | Exclude values |
| `>` | Greater than | `weighted_avg_funniness: "> 80"` | Minimum quality |
| `>=` | Greater or equal | `total_ratings_count: ">= 10"` | Sufficient ratings |
| `<` | Less than | `weighted_avg_funniness: "< 20"` | Low quality |
| `<=` | Less or equal | `total_ratings_count: "<= 3"` | Insufficient data |
| `in` | List membership | `maturity_rating: "in ['G', 'PG']"` | Multiple values |
| `not_in` | Not in list | `maturity_rating: "not_in ['R', 'NC-17']"` | Exclude values |
| `is_null` | Is null/None | `maturity_rating: "is_null"` | Missing data |
| `is_not_null` | Is not null | `weighted_avg_funniness: "is_not_null"` | Has value |

### Field Access Patterns

**Direct Fields** (from StagingJokeDB):
- `weighted_avg_funniness` - Quality score (0-100 scale)
- `total_ratings_count` - Number of ratings
- `text_preview` - First 200 chars of joke text
- `maturity_rating` - G, PG, PG-13, R, NC-17
- `verified` - Boolean verification status

**JSON Fields** (nested access):
- `flags.nsfw` - NSFW flag
- `flags.deleted` - Deleted from source
- `flags.removed` - Removed by moderators
- `flags.spam` - Spam detection
- `flags.profanity` - Contains profanity
- `engagement.upvotes` - Community upvotes
- `engagement.downvotes` - Community downvotes
- `metadata.source_platform` - Origin platform

### Built-in Policy Templates

**Default** (`config/import_policies.yaml`):
- Balanced approach for general platforms
- Auto-approves high quality (4.0+ out of 5) with 10+ ratings
- Auto-rejects low quality (< 2.0) and empty content
- Flags mature content and borderline quality

**Strict** (`config/policies/strict.yaml`):
- Family-friendly platforms only
- Requires premium quality (85+ on 0-100 scale)
- Rejects all NSFW and adult-rated content
- Flags PG-13 and profanity for review

**Permissive** (`config/policies/permissive.yaml`):
- General entertainment platforms
- Accepts most content based on quality alone
- Only rejects spam, deleted, and very low quality
- Minimal flagging (moderate quality and no ratings)

**NSFW Only** (`config/policies/nsfw_only.yaml`):
- Adult content platforms
- Auto-approves high-quality NSFW content
- Rejects family-friendly content
- Flags borderline maturity ratings

### Example: High-Quality Family Content

```yaml
auto_approve:
  - name: "premium_family_content"
    conditions:
      - weighted_avg_funniness: ">= 85"
      - total_ratings_count: ">= 15"
      - flags.nsfw: "false"
      - flags.deleted: "false"
      - maturity_rating: "in ['G', 'PG']"
    action: approve
    reason: "Premium quality family-safe content"
```

This policy automatically approves jokes that are:
- Excellent quality (85+ on 0-100 scale)
- Well-validated (15+ ratings)
- Safe for all audiences
- Not deleted or removed

### Best Practices

1. **Always Check Flags**: Include `flags.deleted: "false"` and `flags.removed: "false"` in auto-approve policies
2. **Use Dry-Run First**: Test policies with `--dry-run` before applying
3. **Combine Quality and Quantity**: Require both good scores and sufficient ratings
4. **Order by Priority**: Use `priority` field to control evaluation order
5. **Flag Borderline Content**: Don't auto-approve/reject edge cases - flag for review
6. **Document Reasons**: Always include clear `reason` fields for audit trail

### Performance

The policy engine is highly optimized:
- Processes ~1000 jokes/second on standard hardware
- Uses batch commits for database efficiency
- Minimal memory footprint with streaming processing
- JSON field caching for repeated access

For detailed examples and advanced techniques, see [POLICY_COOKBOOK.md](docs/POLICY_COOKBOOK.md).

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
│   ├── policies.py          # Policy engine for auto-approval
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
│   ├── test_base.py         # 11 tests
│   ├── test_policies.py     # 77 unit tests
│   └── test_policies_integration.py  # 16 integration tests
└── conftest.py              # Shared fixtures
```

## Testing

```bash
# Run all tests
task test

# Run importer tests only
uv run pytest tests/test_importers/ -v

# Run policy engine tests
uv run pytest tests/test_importers/test_policies.py -v

# Run with coverage
task test:coverage
```

**Current status:** 115 tests passing (77 policy unit + 16 policy integration + 22 importer) ✅

## Documentation

- [IMPORT_PLAN.md](docs/IMPORT_PLAN.md) - Complete import plan (all 4 sprints)
- [POLICY_COOKBOOK.md](docs/POLICY_COOKBOOK.md) - Policy engine guide and examples
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
