# Database Layer Documentation

The Joke Emporium uses SQLModel (Pydantic + SQLAlchemy) for database operations with SQLite as the primary storage engine.

## Architecture

### Database Models

All database models are located in [src/joke_emporium/db/models/](../src/joke_emporium/db/models/):

- **[joke.py](../src/joke_emporium/db/models/joke.py)** - Main `JokeDB` table with cached computed fields
- **[author.py](../src/joke_emporium/db/models/author.py)** - `AuthorDB` table for joke authors
- **[rating.py](../src/joke_emporium/db/models/rating.py)** - `RatingSourceDB` and `VoteDB` tables
- **[associations.py](../src/joke_emporium/db/models/associations.py)** - Many-to-many link tables

### Database Schema

```
jokes (main table)
├── id (PK, auto-increment)
├── joke_uuid (unique index)
├── content_json (JSON array of JokeElements)
├── structure, maturity_rating, cognitive_type
├── tags_json, flags_json, gtvh_json
├── language, source info, dates
├── cached: weighted_avg_funniness, weighted_avg_quality, total_ratings_count, text_preview
└── relationships:
    ├── rating_sources (1:many)
    ├── author_links (many:many via joke_author_link)
    ├── category_links (many:many via joke_category_link)
    └── mechanism_links (many:many via joke_linguistic_mechanism_link)

authors
├── id (PK, auto-increment)
├── author_id (unique index - UUID/username)
├── type, name, real_name, bio, url
└── metadata_json

rating_sources
├── id (PK, auto-increment)
├── joke_id (FK to jokes)
├── source, min_rating, max_rating
├── total_ratings, avg_funniness, avg_quality
├── normalized_avg_funniness, normalized_avg_quality (cached)
├── metadata_json
└── votes (1:many)

votes
├── id (PK, auto-increment)
├── rating_source_id (FK to rating_sources)
├── funniness, quality
└── timestamp

Association Tables (many-to-many):
├── joke_author_link (joke_id, author_id)
├── joke_category_link (joke_id, category)
└── joke_linguistic_mechanism_link (joke_id, mechanism)
```

## Key Features

### 1. Cached Computed Fields

The `JokeDB` model caches expensive calculations:

```python
# Cached fields (updated automatically)
weighted_avg_funniness: float | None  # Weighted average across all rating sources
weighted_avg_quality: float | None     # Weighted average quality
total_ratings_count: int               # Total ratings across all sources
text_preview: str                      # First 100 chars of joke text
```

These are automatically updated via `update_computed_fields()` when ratings change.

### 2. Rating Normalization

All ratings are automatically normalized to a 1-5 scale:

```python
# RatingSource stores both original and normalized values
avg_funniness: float  # Original scale (e.g., 0.936 for Reddit)
normalized_avg_funniness: float  # Normalized to 1-5 (e.g., 4.74)
```

Formula: `1.0 + (raw - min) * 4.0 / (max - min)`

### 3. Pydantic Compatibility

All database models can convert to/from Pydantic models:

```python
# Convert Pydantic → Database
joke_db = JokeDB.from_pydantic(joke)

# Convert Database → Pydantic
joke = joke_db.to_pydantic()
```

This maintains full JSON compatibility with the Pydantic models.

### 4. Many-to-Many Relationships

Categories, mechanisms, and authors use normalized many-to-many tables instead of JSON arrays:

```python
# Query jokes by category
jokes = get_jokes_by_category(session, "wordplay")

# Query jokes by author
jokes = get_jokes_by_author(session, "anonymous")
```

## Usage

### Initialization

```python
from joke_emporium.db import init_db, get_session

# Initialize database (creates tables if needed)
init_db("sqlite:///data/jokes.db")

# Or use default path
init_db()  # Uses data/jokes.db
```

### Basic Operations

```python
from joke_emporium.db.operations import save_joke, get_joke_by_uuid, delete_joke
from joke_emporium.db.session import get_session

# Save a joke
with next(get_session()) as session:
    joke_db = save_joke(session, joke)
    print(f"Saved with ID: {joke_db.id}")

# Retrieve by UUID
with next(get_session()) as session:
    joke = get_joke_by_uuid(session, "550e8400-...")
    print(joke.text_preview)

# Delete a joke
with next(get_session()) as session:
    deleted = delete_joke(session, "550e8400-...")
```

### Query Operations

```python
from joke_emporium.db.operations import (
    get_all_jokes,
    get_jokes_by_category,
    get_jokes_by_author,
)

# Get all jokes (with pagination)
with next(get_session()) as session:
    jokes = get_all_jokes(session, limit=100, offset=0)

# Filter by category
with next(get_session()) as session:
    wordplay_jokes = get_jokes_by_category(session, "wordplay")

# Filter by author
with next(get_session()) as session:
    author_jokes = get_jokes_by_author(session, "comedian_123")
```

## Migrations

The project uses Alembic for database migrations:

```bash
# Generate a new migration
uv run alembic revision --autogenerate -m "Description"

# Apply migrations
uv run alembic upgrade head

# Downgrade
uv run alembic downgrade -1

# View migration history
uv run alembic history
```

### Initial Migration

The initial schema migration is at [alembic/versions/d8396f9e3c57_initial_schema.py](../alembic/versions/).

## Testing

Run the database tests:

```bash
uv run python test_db.py
```

The test suite covers:
1. Creating and saving jokes
2. Retrieving jokes by UUID
3. Querying all jokes
4. Filtering by category
5. Filtering by author
6. Updating jokes
7. Deleting jokes
8. Pydantic compatibility

## Performance Considerations

### Cached Fields

The cached computed fields (`weighted_avg_funniness`, etc.) are stored in the database to avoid expensive recalculation on every query. They are updated:

- Automatically when jokes are saved via `save_joke()`
- Manually via `joke_db.update_computed_fields()`

### Indexes

- `joke_uuid`: Unique index for fast UUID lookups
- `author_id`: Index on authors table
- `joke_id`: Indexes on rating_sources for fast joins
- `rating_source_id`: Index on votes for fast joins

### JSON Storage

Some fields are stored as JSON for flexibility:
- `content_json`: Joke elements
- `tags_json`: Free-form tags
- `flags_json`: Content flags
- `gtvh_json`: GTVH annotations
- `engagement_json`: Engagement metrics
- `metadata_json`: Additional metadata

This trades some query flexibility for schema flexibility and alignment with Pydantic models.

## Future Enhancements

Potential improvements:
- Full-text search on joke content
- Materialized views for common queries
- Read replicas for scaling
- Partial indexes for common filters
- Query result caching
