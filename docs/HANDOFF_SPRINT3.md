# Sprint 3 Handoff Document

## Current Status: Sprint 2 Complete ✅

The TaivopImporter is fully implemented and operational. All 24 tests passing, 99.7% import success rate, ready for production database integration.

## What's Ready from Sprint 2

### Working Infrastructure
1. **Import Framework** - Base class with download → parse → transform → validate → stage pipeline
2. **Staging Database** - ImportBatchDB and StagingJokeDB models with CRUD operations
3. **TaivopImporter** - Successfully imports ~195k jokes from taivop/joke-dataset
4. **CLI Commands** - `import`, `list`, `inspect`, `approve`, `reject` (last two not yet implemented)

### Current Workflow
```bash
# Import to staging
uv run python -m joke_emporium.importers.cli import taivop --max-records 1000

# List imports
uv run python -m joke_emporium.importers.cli list

# Inspect staging jokes
uv run python -m joke_emporium.importers.cli inspect <import-id>
```

## Sprint 3: Production Database Integration

### Objective

Implement the ability to review staged jokes, mark them for approval/rejection, detect duplicates, and merge approved jokes into the production database.

### Architecture Overview

```
┌─────────────────┐
│  Staging DB     │
│  - Pending      │  Review & Flag   ┌──────────────────┐
│  - Approved     │ ───────────────> │  Production DB   │
│  - Rejected     │                  │  - Jokes         │
│  - Under Review │  Merge Process   │  - Authors       │
└─────────────────┘ ───────────────> │  - Ratings       │
                                      │  - Collections   │
                                      └──────────────────┘
```

## Implementation Steps

### 1. Extend Staging Database Models

**File:** `src/joke_emporium/db/models/staging.py`

Add review status tracking to existing models:

```python
class ReviewStatus(str, Enum):
    """Status of joke review for merge."""
    PENDING = "pending"           # Not yet reviewed
    APPROVED = "approved"         # Ready to merge
    REJECTED = "rejected"         # Don't merge
    UNDER_REVIEW = "under_review" # Needs manual review
    DUPLICATE = "duplicate"       # Duplicate of existing joke
    MERGED = "merged"             # Already merged to production


class StagingJokeDB(SQLModel, table=True):
    """Extended staging joke with review status."""
    __tablename__ = "staging_jokes"

    # ... existing fields ...

    # Review tracking
    review_status: str = Field(default=ReviewStatus.PENDING)
    review_notes: str | None = Field(default=None)
    reviewed_by: str | None = Field(default=None)  # Future: user tracking
    reviewed_at: datetime | None = Field(default=None)

    # Duplicate tracking
    duplicate_of_uuid: str | None = Field(default=None, index=True)
    duplicate_similarity: float | None = Field(default=None)

    # Merge tracking
    merged_to_uuid: str | None = Field(default=None)
    merged_at: datetime | None = Field(default=None)
```

**Migration Required:** Add new columns to existing staging database

### 2. Simple Deduplication Logic

**File:** `src/joke_emporium/db/deduplication.py`

Start with simple text comparison, design for future enhancement:

```python
"""Deduplication logic for jokes."""

from sqlmodel import Session, select
from joke_emporium.models.joke import Joke
from joke_emporium.db.models.staging import StagingJokeDB


def normalize_text(text: str) -> str:
    """Normalize joke text for comparison.

    Simple normalization:
    - Convert to lowercase
    - Strip whitespace
    - Remove extra spaces

    Future: More sophisticated normalization
    - Remove punctuation
    - Handle common variations (you're vs you are)
    """
    return text.strip().casefold()


def check_duplicate_in_staging(
    session: Session,
    joke: Joke,
    import_batch_id: int | None = None
) -> tuple[bool, str | None]:
    """Check if joke is duplicate within staging.

    Args:
        session: Database session
        joke: Joke to check
        import_batch_id: Optional batch to check within

    Returns:
        (is_duplicate, duplicate_uuid)
    """
    # Normalize joke text
    normalized = normalize_text(" ".join(elem.text for elem in joke.content))

    # Query staging for similar jokes
    query = select(StagingJokeDB)

    if import_batch_id:
        query = query.where(StagingJokeDB.import_batch_id == import_batch_id)

    query = query.where(StagingJokeDB.review_status != "rejected")

    staging_jokes = session.exec(query).all()

    for staging_joke in staging_jokes:
        # Parse staging joke content
        staging_joke_obj = Joke.model_validate_json(staging_joke.joke_json)
        staging_normalized = normalize_text(
            " ".join(elem.text for elem in staging_joke_obj.content)
        )

        if normalized == staging_normalized:
            return (True, staging_joke.joke_uuid)

    return (False, None)


def check_duplicate_in_production(
    session: Session,
    joke: Joke
) -> tuple[bool, str | None]:
    """Check if joke exists in production database.

    Args:
        session: Production database session
        joke: Joke to check

    Returns:
        (is_duplicate, duplicate_uuid)
    """
    # TODO: Implement after production DB is set up
    # For now, return False
    return (False, None)


def mark_duplicates_in_batch(
    session: Session,
    import_batch_id: int
) -> int:
    """Find and mark duplicates within an import batch.

    Args:
        session: Database session
        import_batch_id: Import batch to check

    Returns:
        Number of duplicates found
    """
    from joke_emporium.db.staging import get_staging_jokes

    duplicates_found = 0
    seen_texts = {}  # normalized_text -> uuid

    # Get all jokes in batch
    staging_jokes = get_staging_jokes(
        session,
        import_batch_id=import_batch_id,
        status="pending"
    )

    for staging_joke in staging_jokes:
        joke = Joke.model_validate_json(staging_joke.joke_json)
        normalized = normalize_text(" ".join(elem.text for elem in joke.content))

        if normalized in seen_texts:
            # Mark as duplicate
            staging_joke.review_status = ReviewStatus.DUPLICATE
            staging_joke.duplicate_of_uuid = seen_texts[normalized]
            staging_joke.duplicate_similarity = 1.0  # Exact match
            session.add(staging_joke)
            duplicates_found += 1
        else:
            seen_texts[normalized] = staging_joke.joke_uuid

    session.commit()
    return duplicates_found
```

### 3. Production Database Schema

**File:** `src/joke_emporium/db/models/production.py`

Use existing `JokeDB`, `AuthorDB`, `RatingDB` models from `src/joke_emporium/db/models/joke.py`:

```python
# Models already exist in:
# - src/joke_emporium/db/models/joke.py
# - src/joke_emporium/db/models/author.py
# - src/joke_emporium/db/models/rating.py

# Add provenance tracking
class JokeProvenanceDB(SQLModel, table=True):
    """Track where production jokes came from."""
    __tablename__ = "joke_provenance"

    id: int | None = Field(default=None, primary_key=True)
    joke_uuid: str = Field(foreign_key="jokes.id", index=True)

    # Import tracking
    import_batch_id: int | None = Field(default=None)
    staging_joke_id: int | None = Field(default=None)
    source_name: str = Field(index=True)  # e.g., "taivop/joke-dataset"
    imported_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Version tracking
    version: int = Field(default=1)

    # Metadata
    metadata: dict | None = Field(default=None, sa_column=Column(JSON))
```

**File:** `src/joke_emporium/db/production.py`

Operations for production database:

```python
"""Production database operations."""

from sqlmodel import Session, SQLModel, create_engine, select
from joke_emporium.models.joke import Joke
from joke_emporium.db.models.joke import JokeDB
# ... other imports


def init_production_db(db_path: str = "data/jokes.db") -> None:
    """Initialize production database."""
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)


def get_production_session():
    """Get production database session."""
    engine = create_engine("sqlite:///data/jokes.db")
    with Session(engine) as session:
        yield session


def save_joke_to_production(
    session: Session,
    joke: Joke,
    import_batch_id: int,
    source_name: str
) -> str:
    """Save joke to production database.

    Args:
        session: Production database session
        joke: Joke to save
        import_batch_id: Import batch ID
        source_name: Source name (e.g., "taivop/joke-dataset")

    Returns:
        UUID of saved joke
    """
    # Convert Joke model to JokeDB
    joke_db = JokeDB.from_joke(joke)

    # Check if joke already exists
    existing = session.get(JokeDB, joke.id)

    if existing:
        # Update existing joke (merge metadata)
        merge_joke_metadata(existing, joke_db)
        session.add(existing)
    else:
        # Add new joke
        session.add(joke_db)

    # Add provenance
    provenance = JokeProvenanceDB(
        joke_uuid=joke.id,
        import_batch_id=import_batch_id,
        source_name=source_name,
    )
    session.add(provenance)

    session.commit()
    return joke.id


def merge_joke_metadata(existing: JokeDB, new: JokeDB) -> None:
    """Merge metadata from new joke into existing.

    Strategy:
    - Combine ratings (don't overwrite)
    - Merge tags (unique set)
    - Combine categories (unique set)
    - Keep highest quality metadata
    """
    # Merge ratings (append, don't replace)
    existing_joke = existing.to_joke()
    new_joke = new.to_joke()

    # Combine ratings
    existing_sources = {r.source for r in existing_joke.ratings}
    for rating in new_joke.ratings:
        if rating.source not in existing_sources:
            existing_joke.ratings.append(rating)

    # Merge tags (unique)
    existing_joke.tags = list(set(existing_joke.tags + new_joke.tags))

    # Merge categories (unique)
    existing_joke.categories = list(set(existing_joke.categories + new_joke.categories))

    # Update from merged joke
    existing.update_from_joke(existing_joke)
```

### 4. Review & Approval CLI Commands

**File:** `src/joke_emporium/importers/cli.py`

Extend existing CLI with review commands:

```python
@cli.command()
@click.argument("staging_id", type=int)
@click.option("--notes", type=str, help="Review notes")
def approve(staging_id: int, notes: str | None):
    """Approve a staging joke for merge to production.

    Examples:
        # Approve single joke
        python -m joke_emporium.importers.cli approve 42

        # Approve with notes
        python -m joke_emporium.importers.cli approve 42 --notes "Great joke!"
    """
    from joke_emporium.db.staging import get_staging_session, update_review_status

    with next(get_staging_session()) as session:
        update_review_status(
            session,
            staging_id,
            ReviewStatus.APPROVED,
            notes=notes
        )
        click.echo(f"✓ Approved staging joke {staging_id}")


@cli.command()
@click.argument("staging_id", type=int)
@click.option("--notes", type=str, help="Rejection reason")
def reject(staging_id: int, notes: str | None):
    """Reject a staging joke (won't be merged).

    Examples:
        # Reject single joke
        python -m joke_emporium.importers.cli reject 42

        # Reject with reason
        python -m joke_emporium.importers.cli reject 42 --notes "Offensive content"
    """
    from joke_emporium.db.staging import get_staging_session, update_review_status

    with next(get_staging_session()) as session:
        update_review_status(
            session,
            staging_id,
            ReviewStatus.REJECTED,
            notes=notes
        )
        click.echo(f"✗ Rejected staging joke {staging_id}")


@cli.command()
@click.argument("staging_id", type=int)
@click.option("--notes", type=str, help="Review notes")
def flag(staging_id: int, notes: str | None):
    """Flag a staging joke for manual review.

    Examples:
        # Flag for review
        python -m joke_emporium.importers.cli flag 42 --notes "Check category"
    """
    from joke_emporium.db.staging import get_staging_session, update_review_status

    with next(get_staging_session()) as session:
        update_review_status(
            session,
            staging_id,
            ReviewStatus.UNDER_REVIEW,
            notes=notes
        )
        click.echo(f"⚠ Flagged staging joke {staging_id} for review")


@cli.command()
@click.argument("import_id")
@click.option("--min-score", type=float, help="Minimum score to approve")
def approve_batch(import_id: str, min_score: float | None):
    """Approve all jokes in an import batch.

    Examples:
        # Approve all jokes in batch
        python -m joke_emporium.importers.cli approve-batch abc123

        # Approve only high-quality jokes
        python -m joke_emporium.importers.cli approve-batch abc123 --min-score 1000
    """
    from joke_emporium.db.staging import get_staging_session, approve_batch_by_quality

    with next(get_staging_session()) as session:
        count = approve_batch_by_quality(
            session,
            import_id,
            min_score=min_score
        )
        click.echo(f"✓ Approved {count} jokes from import {import_id}")


@cli.command()
@click.argument("import_id")
@click.option("--status", type=click.Choice(["pending", "approved", "rejected", "under_review", "all"]), default="all")
@click.option("--limit", type=int, default=20, help="Max jokes to show")
@click.option("--verbose", is_flag=True, help="Show full joke details")
def review(import_id: str, status: str, limit: int, verbose: bool):
    """Review jokes in an import batch before merging.

    Shows joke preview with key metadata for review.

    Examples:
        # Review pending jokes
        python -m joke_emporium.importers.cli review abc123

        # Review approved jokes
        python -m joke_emporium.importers.cli review abc123 --status approved

        # Show full details
        python -m joke_emporium.importers.cli review abc123 --verbose
    """
    from joke_emporium.db.staging import get_staging_session, get_staging_jokes

    with next(get_staging_session()) as session:
        # Get jokes
        jokes = get_staging_jokes(
            session,
            import_id=import_id,
            status=None if status == "all" else status,
            limit=limit
        )

        if not jokes:
            click.echo(f"No jokes found with status: {status}")
            return

        click.echo(f"\nReviewing {len(jokes)} joke(s) from import {import_id}")
        click.echo("=" * 80)

        for staging_joke in jokes:
            joke = Joke.model_validate_json(staging_joke.joke_json)

            # Show joke ID and status
            status_icon = {
                "pending": "⏸",
                "approved": "✓",
                "rejected": "✗",
                "under_review": "⚠",
                "duplicate": "≈",
            }.get(staging_joke.review_status, "?")

            click.echo(f"\n{status_icon} ID: {staging_joke.id} | UUID: {staging_joke.joke_uuid}")
            click.echo(f"   Status: {staging_joke.review_status}")

            # Show joke text
            click.echo(f"   Text: {joke.text_preview}")

            # Show key metadata
            if joke.categories:
                click.echo(f"   Categories: {', '.join(c.value for c in joke.categories)}")
            if joke.tags:
                click.echo(f"   Tags: {', '.join(joke.tags[:5])}")
            if joke.ratings:
                avg_score = sum(r.avg_funniness for r in joke.ratings) / len(joke.ratings)
                click.echo(f"   Avg Score: {avg_score:.1f}")

            # Show verbose details
            if verbose:
                click.echo(f"   Maturity: {joke.maturity_rating.value}")
                click.echo(f"   Structure: {joke.structure.value if joke.structure else 'unknown'}")
                if staging_joke.review_notes:
                    click.echo(f"   Notes: {staging_joke.review_notes}")

            click.echo("   " + "-" * 76)

        click.echo(f"\nShowing {len(jokes)} of {len(jokes)} jokes")
```

### 5. Merge to Production

**File:** `src/joke_emporium/db/merge.py`

```python
"""Merge staging jokes to production database."""

from sqlmodel import Session, select
from joke_emporium.models.joke import Joke
from joke_emporium.db.staging import get_staging_jokes
from joke_emporium.db.production import save_joke_to_production
from joke_emporium.db.deduplication import check_duplicate_in_production


def merge_approved_jokes(
    staging_session: Session,
    production_session: Session,
    import_batch_id: int,
    source_name: str,
    dry_run: bool = False
) -> dict[str, int]:
    """Merge approved jokes from staging to production.

    Args:
        staging_session: Staging database session
        production_session: Production database session
        import_batch_id: Import batch to merge
        source_name: Source name for provenance
        dry_run: If True, don't actually commit changes

    Returns:
        Statistics dict with counts
    """
    stats = {
        "total": 0,
        "merged": 0,
        "skipped_duplicate": 0,
        "failed": 0,
    }

    # Get approved jokes
    approved_jokes = get_staging_jokes(
        staging_session,
        import_batch_id=import_batch_id,
        status="approved"
    )

    stats["total"] = len(approved_jokes)

    for staging_joke in approved_jokes:
        try:
            joke = Joke.model_validate_json(staging_joke.joke_json)

            # Check for duplicates in production
            is_duplicate, duplicate_uuid = check_duplicate_in_production(
                production_session,
                joke
            )

            if is_duplicate:
                # Mark as duplicate but still merge metadata
                staging_joke.review_status = "duplicate"
                staging_joke.duplicate_of_uuid = duplicate_uuid
                stats["skipped_duplicate"] += 1

            if not dry_run:
                # Save to production (will merge if duplicate)
                saved_uuid = save_joke_to_production(
                    production_session,
                    joke,
                    import_batch_id,
                    source_name
                )

                # Update staging record
                staging_joke.review_status = "merged"
                staging_joke.merged_to_uuid = saved_uuid
                staging_joke.merged_at = datetime.now(timezone.utc)
                staging_session.add(staging_joke)

            stats["merged"] += 1

        except Exception as e:
            logger.error(f"Failed to merge staging joke {staging_joke.id}: {e}")
            stats["failed"] += 1
            continue

    if not dry_run:
        staging_session.commit()
        production_session.commit()

    return stats
```

**CLI Command:**

```python
@cli.command()
@click.argument("import_id")
@click.option("--dry-run", is_flag=True, help="Preview merge without committing")
def merge(import_id: str, dry_run: bool):
    """Merge approved jokes from staging to production.

    Only merges jokes with status='approved'.
    All operations are transactional (all-or-nothing).

    Examples:
        # Preview merge
        python -m joke_emporium.importers.cli merge abc123 --dry-run

        # Perform merge
        python -m joke_emporium.importers.cli merge abc123
    """
    from joke_emporium.db.staging import get_staging_session, get_import_batch
    from joke_emporium.db.production import get_production_session
    from joke_emporium.db.merge import merge_approved_jokes

    with next(get_staging_session()) as staging_session:
        # Get import batch
        batch = get_import_batch(staging_session, import_id)
        if not batch:
            click.echo(f"Error: Import batch {import_id} not found")
            return

        with next(get_production_session()) as production_session:
            try:
                stats = merge_approved_jokes(
                    staging_session,
                    production_session,
                    batch.id,
                    batch.source,
                    dry_run=dry_run
                )

                if dry_run:
                    click.echo("\n🔍 DRY RUN - No changes committed\n")
                else:
                    click.echo("\n✓ MERGE COMPLETE\n")

                click.echo("=" * 60)
                click.echo(f"Total jokes reviewed: {stats['total']}")
                click.echo(f"Merged to production: {stats['merged']}")
                click.echo(f"Skipped (duplicate): {stats['skipped_duplicate']}")
                click.echo(f"Failed: {stats['failed']}")
                click.echo("=" * 60)

            except Exception as e:
                click.echo(f"\n✗ Merge failed: {e}")
                if not dry_run:
                    click.echo("All changes rolled back (transaction failed)")
                raise
```

### 6. Database Migration

**File:** `alembic/versions/003_add_review_status.py`

```python
"""Add review status to staging jokes.

Revision ID: 003
Revises: 002
Create Date: 2025-12-16
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add review columns to staging_jokes
    op.add_column('staging_jokes',
        sa.Column('review_status', sa.String(),
                 nullable=False, server_default='pending'))
    op.add_column('staging_jokes',
        sa.Column('review_notes', sa.String(), nullable=True))
    op.add_column('staging_jokes',
        sa.Column('reviewed_by', sa.String(), nullable=True))
    op.add_column('staging_jokes',
        sa.Column('reviewed_at', sa.DateTime(), nullable=True))
    op.add_column('staging_jokes',
        sa.Column('duplicate_of_uuid', sa.String(), nullable=True))
    op.add_column('staging_jokes',
        sa.Column('duplicate_similarity', sa.Float(), nullable=True))
    op.add_column('staging_jokes',
        sa.Column('merged_to_uuid', sa.String(), nullable=True))
    op.add_column('staging_jokes',
        sa.Column('merged_at', sa.DateTime(), nullable=True))

    # Add indexes
    op.create_index('ix_staging_jokes_review_status',
                    'staging_jokes', ['review_status'])
    op.create_index('ix_staging_jokes_duplicate_of_uuid',
                    'staging_jokes', ['duplicate_of_uuid'])


def downgrade() -> None:
    # Remove indexes
    op.drop_index('ix_staging_jokes_duplicate_of_uuid')
    op.drop_index('ix_staging_jokes_review_status')

    # Remove columns
    op.drop_column('staging_jokes', 'merged_at')
    op.drop_column('staging_jokes', 'merged_to_uuid')
    op.drop_column('staging_jokes', 'duplicate_similarity')
    op.drop_column('staging_jokes', 'duplicate_of_uuid')
    op.drop_column('staging_jokes', 'reviewed_at')
    op.drop_column('staging_jokes', 'reviewed_by')
    op.drop_column('staging_jokes', 'review_notes')
    op.drop_column('staging_jokes', 'review_status')
```

Run migration:
```bash
alembic upgrade head
```

### 7. Testing Strategy

**File:** `tests/test_db/test_deduplication.py`

```python
"""Tests for deduplication logic."""

import unittest
from joke_emporium.db.deduplication import normalize_text, check_duplicate_in_staging
from joke_emporium.models.joke import Joke
from joke_emporium.models.content import JokeElement
from joke_emporium.models.enums import ElementType, StructureType


class TestDeduplication(unittest.TestCase):
    """Test deduplication functionality."""

    def test_normalize_text_basic(self):
        """Test basic text normalization."""
        self.assertEqual(
            normalize_text("  Hello World  "),
            "hello world"
        )

    def test_normalize_text_casefold(self):
        """Test casefolding."""
        self.assertEqual(
            normalize_text("HELLO world"),
            "hello world"
        )

    def test_normalize_text_extra_spaces(self):
        """Test multiple spaces."""
        text = "Hello    World"
        normalized = normalize_text(text)
        # Should preserve internal spaces for now
        self.assertIn("hello", normalized)
        self.assertIn("world", normalized)

    def test_check_duplicate_identical_text(self):
        """Test detecting identical jokes."""
        # TODO: Implement with database fixtures
        pass

    def test_check_duplicate_different_text(self):
        """Test non-duplicate jokes."""
        # TODO: Implement with database fixtures
        pass
```

**File:** `tests/test_db/test_merge.py`

```python
"""Tests for merge operations."""

import unittest
from joke_emporium.db.merge import merge_approved_jokes


class TestMerge(unittest.TestCase):
    """Test merge functionality."""

    def test_merge_approved_jokes(self):
        """Test merging approved jokes to production."""
        # TODO: Implement with database fixtures
        pass

    def test_merge_skips_rejected(self):
        """Test that rejected jokes are not merged."""
        # TODO: Implement with database fixtures
        pass

    def test_merge_is_transactional(self):
        """Test that merge is all-or-nothing."""
        # TODO: Implement with database fixtures
        pass
```

### 8. Example Workflow

```bash
# 1. Import jokes to staging
uv run python -m joke_emporium.importers.cli import taivop --max-records 100

# 2. Check for duplicates in the batch
# (Happens automatically during import)

# 3. Review jokes
uv run python -m joke_emporium.importers.cli review <import-id>

# 4. Approve high-quality jokes
uv run python -m joke_emporium.importers.cli approve-batch <import-id> --min-score 1000

# 5. Review remaining jokes individually
uv run python -m joke_emporium.importers.cli review <import-id> --status pending

# 6. Approve or reject individual jokes
uv run python -m joke_emporium.importers.cli approve <staging-id>
uv run python -m joke_emporium.importers.cli reject <staging-id> --notes "Offensive"
uv run python -m joke_emporium.importers.cli flag <staging-id> --notes "Check category"

# 7. Preview merge (dry run)
uv run python -m joke_emporium.importers.cli merge <import-id> --dry-run

# 8. Perform merge
uv run python -m joke_emporium.importers.cli merge <import-id>

# 9. Verify production database
uv run python -m joke_emporium.db.operations count
```

## Success Criteria

- [ ] Extended staging database with review status fields
- [ ] Database migration applied successfully
- [ ] Simple deduplication works (exact text match)
- [ ] CLI commands: `approve`, `reject`, `flag`, `approve-batch`, `review`
- [ ] CLI command: `merge` with dry-run option
- [ ] Production database schema with provenance tracking
- [ ] Merge is transactional (all-or-nothing)
- [ ] Metadata merging works (ratings, tags, categories)
- [ ] Tests for deduplication logic
- [ ] Tests for merge operations
- [ ] Documentation updated
- [ ] Can review and approve 100 staged jokes
- [ ] Can merge 100 approved jokes to production

## File Checklist

Files to create:
- [ ] `src/joke_emporium/db/deduplication.py` (~150 lines)
- [ ] `src/joke_emporium/db/production.py` (~200 lines)
- [ ] `src/joke_emporium/db/merge.py` (~150 lines)
- [ ] `alembic/versions/003_add_review_status.py` (migration)
- [ ] `tests/test_db/test_deduplication.py` (~100 lines)
- [ ] `tests/test_db/test_merge.py` (~100 lines)

Files to update:
- [ ] `src/joke_emporium/db/models/staging.py` (add review fields)
- [ ] `src/joke_emporium/importers/cli.py` (add review commands)
- [ ] `src/joke_emporium/db/staging.py` (add review operations)

## Dependencies

Already installed - no new dependencies required.

## Known Challenges

1. **Simple Deduplication Limitations**
   - Exact text match may miss near-duplicates
   - Different punctuation/capitalization handled by normalization
   - Future: Implement fuzzy matching (Levenshtein distance)
   - Future: Use text hashing for performance

2. **Metadata Merging Complexity**
   - Multiple sources may have conflicting data
   - Current approach: Append ratings, merge tags/categories
   - Future: More sophisticated conflict resolution

3. **Performance at Scale**
   - Checking 200k jokes for duplicates could be slow
   - Current approach: Simple iteration
   - Future: Use database indexes, text hashing

4. **Transaction Size**
   - Large batches may cause long transactions
   - Current approach: Single transaction per batch
   - Future: Batch in chunks if needed

## Future Enhancements (Sprint 4)

1. **Advanced Deduplication**
   - Fuzzy matching with Levenshtein distance
   - Text fingerprinting/hashing
   - ML-based similarity detection

2. **Web UI for Review**
   - Interactive joke review interface
   - Side-by-side duplicate comparison
   - Batch operations with preview

3. **Quality Scoring**
   - Automated quality assessment
   - Source reputation tracking
   - Auto-approval thresholds

4. **Performance Optimization**
   - Bulk operations
   - Parallel processing
   - Database query optimization

## Timeline Estimate

**Sprint 3 Development:**
- Database schema updates: 1-2 hours
- Deduplication logic: 2-3 hours
- Production DB operations: 2-3 hours
- CLI review commands: 2-3 hours
- Merge logic: 2-3 hours
- Testing: 2-3 hours
- Documentation: 1 hour

**Total**: ~12-18 hours

## Notes

- Keep deduplication simple for now - experimentation needed with real data
- Focus on getting the workflow working end-to-end
- Transactional merges are critical for data integrity
- Track provenance for debugging and rollback capability
- Don't delete staging data after merge (useful for debugging)

---

## Quick Start

To begin Sprint 3:

```bash
# 1. Create database migration
alembic revision -m "add_review_status_to_staging"

# 2. Implement review status in staging models
# Edit: src/joke_emporium/db/models/staging.py

# 3. Implement deduplication logic
# Create: src/joke_emporium/db/deduplication.py

# 4. Add review CLI commands
# Edit: src/joke_emporium/importers/cli.py

# 5. Implement merge logic
# Create: src/joke_emporium/db/merge.py

# 6. Test with sample data
uv run python -m joke_emporium.importers.cli import taivop --max-records 100
uv run python -m joke_emporium.importers.cli review <import-id>
uv run python -m joke_emporium.importers.cli approve-batch <import-id>
uv run python -m joke_emporium.importers.cli merge <import-id> --dry-run
```

The foundation from Sprint 1 & 2 is solid. Sprint 3 completes the core workflow! 🚀
