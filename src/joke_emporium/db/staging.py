"""Staging database operations for import validation."""

from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine, select

from joke_emporium.db.models.staging import ImportBatchDB, ReviewStatus, StagingJokeDB
from joke_emporium.importers.models import ImportMetadata
from joke_emporium.models.joke import Joke

# Default staging database path
DEFAULT_STAGING_DB_PATH = Path("data/staging.db")

# Global staging engine
staging_engine = None


def init_staging_db(database_url: str | None = None, echo: bool = False) -> None:
    """Initialize the staging database engine and create all tables.

    Args:
        database_url: SQLite database URL. If None, uses default path.
        echo: If True, log all SQL statements.
    """
    global staging_engine

    if database_url is None:
        # Create data directory if it doesn't exist
        DEFAULT_STAGING_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        database_url = f"sqlite:///{DEFAULT_STAGING_DB_PATH}"

    staging_engine = create_engine(database_url, echo=echo)

    # Import all models to ensure they're registered
    from joke_emporium.db.models import (  # noqa: F401
        AuthorDB,
        ImportBatchDB,
        JokeAuthorLink,
        JokeCategoryLink,
        JokeDB,
        JokeLinguisticMechanismLink,
        RatingSourceDB,
        StagingJokeDB,
        VoteDB,
    )

    # Create all tables
    SQLModel.metadata.create_all(staging_engine)


def get_staging_session() -> Generator[Session]:
    """Get a staging database session (context manager).

    Yields:
        Database session

    Example:
        with next(get_staging_session()) as session:
            # Use session
            pass
    """
    if staging_engine is None:
        raise RuntimeError("Staging database not initialized. Call init_staging_db() first.")

    with Session(staging_engine) as session:
        yield session


def create_import_batch(session: Session, metadata: ImportMetadata) -> ImportBatchDB:
    """Create a new import batch record.

    Args:
        session: Staging database session
        metadata: Import metadata

    Returns:
        Created ImportBatchDB instance
    """
    import_batch = ImportBatchDB(
        import_id=metadata.import_id,
        source=metadata.source,
        source_version=metadata.source_version,
        imported_at=metadata.imported_at,
        total_records=metadata.total_records,
        successful=metadata.successful,
        failed=metadata.failed,
        validation_status=metadata.validation_status.value,
        notes=metadata.notes,
    )

    session.add(import_batch)
    session.commit()
    session.refresh(import_batch)

    return import_batch


def update_import_batch(session: Session, import_batch: ImportBatchDB) -> None:
    """Update an import batch record.

    Args:
        session: Staging database session
        import_batch: ImportBatchDB instance with updated values
    """
    session.add(import_batch)
    session.commit()
    session.refresh(import_batch)


def get_import_batch(session: Session, import_id: str) -> ImportBatchDB | None:
    """Get an import batch by its import_id.

    Args:
        session: Staging database session
        import_id: Import batch UUID

    Returns:
        ImportBatchDB instance or None if not found
    """
    statement = select(ImportBatchDB).where(ImportBatchDB.import_id == import_id)
    return session.exec(statement).first()


def get_all_import_batches(session: Session, validation_status: str | None = None) -> list[ImportBatchDB]:
    """Get all import batches, optionally filtered by status.

    Args:
        session: Staging database session
        validation_status: Optional filter by validation status

    Returns:
        List of ImportBatchDB instances
    """
    statement = select(ImportBatchDB)

    if validation_status:
        statement = statement.where(ImportBatchDB.validation_status == validation_status)

    return list(session.exec(statement).all())


def save_staging_joke(session: Session, joke: Joke, raw_data: dict, import_batch_id: int) -> StagingJokeDB:
    """Save a joke to staging database.

    Args:
        session: Staging database session
        joke: Pydantic Joke model
        raw_data: Original raw data dictionary
        import_batch_id: ID of import batch

    Returns:
        Created StagingJokeDB instance
    """
    staging_joke = StagingJokeDB.from_joke_and_raw(joke, raw_data, import_batch_id)

    session.add(staging_joke)
    session.commit()
    session.refresh(staging_joke)

    return staging_joke


def get_staging_jokes(
    session: Session,
    import_id: str | None = None,
    validation_status: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[StagingJokeDB]:
    """Query staging jokes with optional filters.

    Args:
        session: Staging database session
        import_id: Optional filter by import batch ID
        validation_status: Optional filter by validation status
        limit: Maximum number of jokes to return
        offset: Number of jokes to skip

    Returns:
        List of StagingJokeDB instances
    """
    statement = select(StagingJokeDB)

    if import_id:
        # Join with import batch to filter by import_id
        statement = statement.join(ImportBatchDB).where(ImportBatchDB.import_id == import_id)

    if validation_status:
        statement = statement.where(StagingJokeDB.validation_status == validation_status)

    statement = statement.offset(offset)

    if limit:
        statement = statement.limit(limit)

    return list(session.exec(statement).all())


def approve_staging_joke(session: Session, staging_id: int, notes: str | None = None) -> bool:
    """Approve a staging joke for production.

    Args:
        session: Staging database session
        staging_id: ID of staging joke
        notes: Optional approval notes

    Returns:
        True if approved, False if not found
    """
    statement = select(StagingJokeDB).where(StagingJokeDB.id == staging_id)
    staging_joke = session.exec(statement).first()

    if not staging_joke:
        return False

    staging_joke.review_status = ReviewStatus.APPROVED
    staging_joke.reviewed_at = datetime.now(UTC)
    if notes:
        staging_joke.review_notes = notes

    session.add(staging_joke)
    session.commit()

    return True


def reject_staging_joke(session: Session, staging_id: int, reason: str) -> bool:
    """Reject a staging joke.

    Args:
        session: Staging database session
        staging_id: ID of staging joke
        reason: Reason for rejection

    Returns:
        True if rejected, False if not found
    """
    statement = select(StagingJokeDB).where(StagingJokeDB.id == staging_id)
    staging_joke = session.exec(statement).first()

    if not staging_joke:
        return False

    staging_joke.review_status = ReviewStatus.REJECTED
    staging_joke.reviewed_at = datetime.now(UTC)
    staging_joke.review_notes = reason

    session.add(staging_joke)
    session.commit()

    return True


def mark_duplicate(session: Session, staging_id: int, duplicate_of_uuid: str) -> bool:
    """Mark a staging joke as duplicate of another joke.

    Args:
        session: Staging database session
        staging_id: ID of staging joke
        duplicate_of_uuid: UUID of the duplicate joke

    Returns:
        True if marked, False if not found
    """
    statement = select(StagingJokeDB).where(StagingJokeDB.id == staging_id)
    staging_joke = session.exec(statement).first()

    if not staging_joke:
        return False

    staging_joke.duplicate_of_uuid = duplicate_of_uuid
    staging_joke.review_status = ReviewStatus.DUPLICATE
    staging_joke.reviewed_at = datetime.now(UTC)
    staging_joke.review_notes = f"Duplicate of joke {duplicate_of_uuid}"

    session.add(staging_joke)
    session.commit()

    return True


def count_staging_jokes(session: Session, import_id: str | None = None) -> int:
    """Count staging jokes, optionally filtered by import batch.

    Args:
        session: Staging database session
        import_id: Optional filter by import batch ID

    Returns:
        Number of staging jokes
    """
    statement = select(StagingJokeDB)

    if import_id:
        statement = statement.join(ImportBatchDB).where(ImportBatchDB.import_id == import_id)

    return session.exec(statement).count()


def delete_import_batch(session: Session, import_id: str) -> bool:
    """Delete an import batch and all its staging jokes.

    Args:
        session: Staging database session
        import_id: Import batch UUID

    Returns:
        True if deleted, False if not found
    """
    statement = select(ImportBatchDB).where(ImportBatchDB.import_id == import_id)
    import_batch = session.exec(statement).first()

    if not import_batch:
        return False

    # Cascade will delete all staging jokes
    session.delete(import_batch)
    session.commit()

    return True


def update_review_status(
    session: Session, staging_id: int, status: ReviewStatus, notes: str | None = None, reviewed_by: str | None = None
) -> bool:
    """Update review status of a staging joke.

    Args:
        session: Staging database session
        staging_id: ID of staging joke
        status: New review status
        notes: Optional review notes
        reviewed_by: Optional user identifier

    Returns:
        True if updated, False if not found
    """
    statement = select(StagingJokeDB).where(StagingJokeDB.id == staging_id)
    staging_joke = session.exec(statement).first()

    if not staging_joke:
        return False

    staging_joke.review_status = status
    if notes:
        staging_joke.review_notes = notes
    if reviewed_by:
        staging_joke.reviewed_by = reviewed_by
    staging_joke.reviewed_at = datetime.now(UTC)

    session.add(staging_joke)
    session.commit()

    return True


def approve_batch_by_quality(session: Session, import_id: str, min_score: float | None = None) -> int:
    """Approve jokes in a batch based on quality score.

    Args:
        session: Staging database session
        import_id: Import batch ID
        min_score: Minimum weighted avg funniness score

    Returns:
        Number of jokes approved
    """
    # Get import batch
    import_batch = get_import_batch(session, import_id)
    if not import_batch:
        return 0

    # Query pending jokes in batch
    query = select(StagingJokeDB).where(
        StagingJokeDB.import_batch_id == import_batch.id, StagingJokeDB.review_status == ReviewStatus.PENDING
    )

    if min_score is not None:
        query = query.where(StagingJokeDB.weighted_avg_funniness >= min_score)

    staging_jokes = session.exec(query).all()

    # Approve each joke
    count = 0
    for staging_joke in staging_jokes:
        staging_joke.review_status = ReviewStatus.APPROVED
        staging_joke.reviewed_at = datetime.now(UTC)
        session.add(staging_joke)
        count += 1

    session.commit()
    return count


def get_staging_jokes_by_status(
    session: Session, import_batch_id: int | None = None, status: str | None = None, limit: int | None = None
) -> list[StagingJokeDB]:
    """Get staging jokes filtered by review status.

    Args:
        session: Staging database session
        import_batch_id: Optional import batch ID filter
        status: Optional review status filter
        limit: Maximum number to return

    Returns:
        List of StagingJokeDB instances
    """
    query = select(StagingJokeDB)

    if import_batch_id is not None:
        query = query.where(StagingJokeDB.import_batch_id == import_batch_id)

    if status:
        query = query.where(StagingJokeDB.review_status == status)

    if limit:
        query = query.limit(limit)

    return list(session.exec(query).all())
