# Joke Emporium

A comprehensive, categorized dataset of jokes with rich metadata and scientific annotations.

## Features

- **Structured JSON format** with Pydantic validation
- **Multi-dimensional categorization**: topics, structure, linguistic mechanisms
- **Multi-source ratings** with automatic normalization to 1-5 scale
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
