# Joke Emporium

A comprehensive, categorized dataset of jokes with rich metadata and scientific annotations.

## Features

- **Structured JSON format** with Pydantic validation
- **Multi-dimensional categorization**: topics, structure, linguistic mechanisms
- **Multi-source ratings** with automatic normalization to 1-5 scale
- **Import framework** for ingesting jokes from external sources
- **Policy-based auto-approval** for automated review workflows
- **Academic annotations** supporting GTVH and Chalmers taxonomies
- **Content flags** for filtering and safety
- **Python 3.10+** with full type hints

## Installation

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

## Quick Start

```python
from datetime import datetime
from joke_emporium.models import (
    Joke, JokeElement, Author, RatingSource, JokeMetadata,
    Category, StructureType, MaturityRating, ElementType, AuthorType
)

# Create a joke
joke = Joke(
    id="550e8400-e29b-41d4-a716-446655440000",
    content=[
        JokeElement(type=ElementType.SETUP, text="Why did the chicken cross the road?"),
        JokeElement(type=ElementType.PUNCHLINE, text="To get to the other side!"),
    ],
    categories=[Category.ANIMALS],
    structure=StructureType.QA,
    maturity_rating=MaturityRating.G,
    metadata=JokeMetadata(
        language="en",
        authors=[Author(id="anonymous", type=AuthorType.ANONYMOUS, name="Anonymous")],
        added_date=datetime.now(),
        last_modified=datetime.now(),
    ),
)

# Export to JSON
print(joke.model_dump_json(indent=2))
```

## Schema Overview

### Joke Model

The main `Joke` model contains:

- **Identification**: UUID, version
- **Content**: List of `JokeElement` (setup, punchline, etc.)
- **Categorization**: Topics, structure, linguistic mechanisms, maturity rating
- **Ratings**: Multi-source ratings with normalization
- **Metadata**: Authors, source, engagement metrics
- **Advanced**: Optional GTVH annotations

### Rating Normalization

Supports ratings from different scales (Reddit 0-1, IMDB 1-10, etc.) with automatic normalization to 1-5:

```python
from joke_emporium.models import RatingSource

# Reddit upvote ratio (0-1 scale)
reddit = RatingSource(
    source="reddit",
    min_rating=0.0,
    max_rating=1.0,
    total_ratings=1335,
    avg_funniness=0.936,  # 93.6% upvote ratio
)

print(reddit.normalized_avg_funniness)  # 4.74 out of 5
```

See [NORMALIZATION_EXAMPLES.md](NORMALIZATION_EXAMPLES.md) for detailed examples.

## Categorization

### Topics (40+ categories)
- People & Relationships: relationships, marriage, dating, family, parenting
- Professions: work, doctor, lawyer, teacher, engineer, programmer
- Topics: technology, computers, science, math, animals, food, sports
- Situations: travel, school, medical, shopping, driving
- Meta: observational, absurd, wordplay

### Structure Types
- one_liner, qa, riddle, story, dialogue, knock_knock, anti_joke, etc.

### Linguistic Mechanisms (25+)
- Wordplay: pun_homophonic, pun_homographic, double_entendre
- Rhetorical: irony, sarcasm, exaggeration, hyperbole
- Logic: paraprosdokian, non_sequitur, absurdism, reversal

See [enums.py](src/joke_emporium/models/enums.py) for the complete list.

## Dataset Structure

Jokes are organized into collections (JSON files) split by language and maturity:

```
data/
  jokes_en_clean.json      # English, G-PG13
  jokes_en_nsfw.json       # English, R-X
  jokes_es_clean.json      # Spanish, G-PG13
  ...
```

Each collection file contains:
```json
{
  "name": "jokes_en_clean",
  "version": "1.0.0",
  "language": "en",
  "maturity_filter": "pg13",
  "jokes": [...]
}
```

## Research Background

This schema is informed by academic research on humor:

- **GTVH** (General Theory of Verbal Humor) - Attardo & Raskin
- **Chalmers Cognitive Taxonomy** - 4 main joke types
- **Linguistic Analysis** - Phonological, semantic, structural features
- **Real-world datasets** - Reddit, HAHA corpus, CleanComedy, Humor Genome

See [RESEARCH_CATEGORIZATION.md](RESEARCH_CATEGORIZATION.md) for details.

## Documentation

- [Import Framework Guide](README_IMPORT_FRAMEWORK.md) - Complete import workflow and policy engine
- [Policy Cookbook](docs/POLICY_COOKBOOK.md) - Policy engine examples and best practices
- [Schema Outline](SCHEMA_OUTLINE.md) - Complete schema documentation
- [Data Sources](DATA_SOURCES.md) - List of joke datasets and research
- [Research](RESEARCH_CATEGORIZATION.md) - Scientific categorization approaches
- [Normalization](NORMALIZATION_EXAMPLES.md) - Rating normalization examples

## Development

```bash
# Run tests
uv run python test_models.py

# With pytest (coming soon)
uv run pytest

# Linting
uv run ruff check .

# Type checking
uv run mypy src/
```

## Example Data

See [example_joke.json](example_joke.json) for a complete example.

## Future Plans

- SQLite database integration using SQLModel
- Web scraping tools for data collection
- Validation utilities
- I/O helpers for loading/saving collections
- Statistical analysis tools
- API for querying jokes

## License

MIT

## Contributing

Contributions welcome! This is an open dataset for research and development

## CLI

### --help
```bash
uv run joke-emporium --help                                       
Usage: joke-emporium [OPTIONS] COMMAND [ARGS]...

  Joke Emporium import management CLI.

  Manage data imports, staging database, and validation.

Options:
  --help  Show this message and exit.

Commands:
  approve        Approve a staging joke for production.
  approve-batch  Approve all jokes in an import batch.
  delete         Delete an import batch and all its staging jokes.
  flag           Flag a staging joke for manual review.
  import         Import jokes from a data source.
  inspect        Inspect staging jokes for an import batch.
  list           List all import batches.
  merge          Merge approved staging jokes to production database.
  reject         Reject a staging joke.
  reset          Reset/clear the staging database.
  review         Review jokes in an import batch before merging.
```

### approve
```bash
uv run joke-emporium approve --help
Usage: joke-emporium approve [OPTIONS] STAGING_ID

  Approve a staging joke for production.

  STAGING_ID: Database ID of the staging joke

  Example:     python -m joke_emporium.importers.cli approve 123 --notes
  "Looks good"

Options:
  --notes TEXT       Optional approval notes
  --staging-db PATH  Path to staging database
  --help             Show this message and exit.
```

### approve-batch
```bash
uv run joke-emporium approve-batch --help
Usage: joke-emporium approve-batch [OPTIONS] IMPORT_ID

  Approve all jokes in an import batch.

  IMPORT_ID: UUID of the import batch

  Examples:     # Approve all jokes in batch     python -m
  joke_emporium.importers.cli approve-batch <import_id>

      # Approve only high-quality jokes     python -m
      joke_emporium.importers.cli approve-batch <import_id> --min-score 1000

Options:
  --min-score FLOAT  Minimum score to approve
  --staging-db PATH  Path to staging database
  --help             Show this message and exit.
```

### delete
```bash
uv run joke-emporium delete --help       
Usage: joke-emporium delete [OPTIONS] IMPORT_ID

  Delete an import batch and all its staging jokes.

  IMPORT_ID: UUID of the import batch to delete

  Example:     python -m joke_emporium.importers.cli delete <import_id> --yes

Options:
  --yes              Skip confirmation
  --staging-db PATH  Path to staging database
  --help             Show this message and exit.
```

### flag
```bash
uv run joke-emporium flag --help  
Usage: joke-emporium flag [OPTIONS] STAGING_ID

  Flag a staging joke for manual review.

  STAGING_ID: Database ID of the staging joke

  Example:     python -m joke_emporium.importers.cli flag 123 --notes "Check
  category"

Options:
  --notes TEXT       Review notes
  --staging-db PATH  Path to staging database
  --help             Show this message and exit.
```

### import
```bash
uv run joke-emporium import --help
Usage: joke-emporium import [OPTIONS] {taivop}

  Import jokes from a data source.

  SOURCE: Data source to import from (currently supports: taivop)

  Examples:     # Import from taivop dataset with validation     python -m
  joke_emporium.importers.cli import taivop

      # Import without validation (faster, less safe)     python -m
      joke_emporium.importers.cli import taivop --no-validate

      # Import only 100 records for testing     python -m
      joke_emporium.importers.cli import taivop --max-records 100

Options:
  --validate / --no-validate  Validate jokes before import
  --max-records INTEGER       Maximum records to import (for testing)
  --staging-db PATH           Path to staging database (default:
                              data/staging.db)
  --help                      Show this message and exit.
```

### inspect
```bash
uv run joke-emporium inspect --help
Usage: joke-emporium inspect [OPTIONS] IMPORT_ID

  Inspect staging jokes for an import batch.

  IMPORT_ID: UUID of the import batch to inspect

  Examples:     # Inspect first 10 jokes     python -m
  joke_emporium.importers.cli inspect <import_id>

      # Inspect only pending jokes     python -m joke_emporium.importers.cli
      inspect <import_id> --status pending

      # Show more jokes     python -m joke_emporium.importers.cli inspect
      <import_id> --limit 50

Options:
  --status [pending|approved|rejected]
                                  Filter by status
  --limit INTEGER                 Number of jokes to show
  --staging-db PATH               Path to staging database
  --help                          Show this message and exit.
```

### list
```bash
uv run joke-emporium list --help   
Usage: joke-emporium list [OPTIONS]

  List all import batches.

  Examples:     # List all imports     python -m joke_emporium.importers.cli
  list

      # List only pending imports     python -m joke_emporium.importers.cli
      list --status pending

Options:
  --status [pending|approved|rejected]
                                  Filter by status
  --staging-db PATH               Path to staging database
  --help                          Show this message and exit.
```

### merge
```bash
uv run joke-emporium merge --help
Usage: joke-emporium merge [OPTIONS] IMPORT_ID

  Merge approved staging jokes to production database.

  IMPORT_ID: UUID of the import batch to merge

  Only merges jokes with status='approved'. All operations are transactional
  (all-or-nothing).

  Examples:     # Preview merge     python -m joke_emporium.importers.cli
  merge <import_id> --dry-run

      # Perform merge     python -m joke_emporium.importers.cli merge
      <import_id>

Options:
  --dry-run          Preview merge without committing
  --staging-db PATH  Path to staging database
  --prod-db PATH     Path to production database
  --help             Show this message and exit.
```

### reject
```bash
uv run joke-emporium merge --help
Usage: joke-emporium merge [OPTIONS] IMPORT_ID

  Merge approved staging jokes to production database.

  IMPORT_ID: UUID of the import batch to merge

  Only merges jokes with status='approved'. All operations are transactional
  (all-or-nothing).

  Examples:     # Preview merge     python -m joke_emporium.importers.cli
  merge <import_id> --dry-run

      # Perform merge     python -m joke_emporium.importers.cli merge
      <import_id>

Options:
  --dry-run          Preview merge without committing
  --staging-db PATH  Path to staging database
  --prod-db PATH     Path to production database
  --help             Show this message and exit.
PS C:\repos\joke-emporium> uv run joke-emporium reject --help
Usage: joke-emporium reject [OPTIONS] STAGING_ID REASON

  Reject a staging joke.

  STAGING_ID: Database ID of the staging joke REASON: Reason for rejection

  Example:     python -m joke_emporium.importers.cli reject 123 "Inappropriate
  content"

Options:
  --staging-db PATH  Path to staging database
  --help             Show this message and exit.
```

### reset
```bash
uv run joke-emporium reset --help 
Usage: joke-emporium reset [OPTIONS]

  Reset/clear the staging database.

  WARNING: This will delete ALL import batches and staging jokes!

  Example:     python -m joke_emporium.importers.cli reset --yes

Options:
  --yes              Skip confirmation
  --staging-db PATH  Path to staging database
  --help             Show this message and exit.
```

### review
```bash
uv run joke-emporium review --help
Usage: joke-emporium review [OPTIONS] IMPORT_ID

  Review jokes in an import batch before merging.

  IMPORT_ID: UUID of the import batch

  Examples:     # Review pending jokes     python -m
  joke_emporium.importers.cli review <import_id>

      # Review approved jokes     python -m joke_emporium.importers.cli review
      <import_id> --status approved

      # Show full details     python -m joke_emporium.importers.cli review
      <import_id> --verbose

Options:
  --status [pending|approved|rejected|under_review|duplicate|all]
                                  Filter by review status
  --limit INTEGER                 Max jokes to show
  --verbose                       Show full joke details
  --staging-db PATH               Path to staging database
  --help                          Show this message and exit.
```
