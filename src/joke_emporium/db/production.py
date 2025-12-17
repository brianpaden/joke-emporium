"""Production database operations."""

from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine, select

from joke_emporium.db.models.joke import JokeDB
from joke_emporium.db.models.provenance import JokeProvenanceDB
from joke_emporium.models.joke import Joke

# Default production database path
DEFAULT_PRODUCTION_DB_PATH = Path("data/jokes.db")

# Global production engine
production_engine = None


def init_production_db(database_url: str | None = None, echo: bool = False) -> None:
    """Initialize production database engine and create all tables.

    Args:
        database_url: SQLite database URL. If None, uses default path.
        echo: If True, log all SQL statements.
    """
    global production_engine

    if database_url is None:
        # Create data directory if it doesn't exist
        DEFAULT_PRODUCTION_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        database_url = f"sqlite:///{DEFAULT_PRODUCTION_DB_PATH}"

    production_engine = create_engine(database_url, echo=echo)

    # Import all models to ensure they're registered
    from joke_emporium.db.models import (  # noqa: F401
        AuthorDB,
        JokeAuthorLink,
        JokeCategoryLink,
        JokeDB,
        JokeLinguisticMechanismLink,
        JokeProvenanceDB,
        RatingSourceDB,
        VoteDB,
    )

    # Create all tables
    SQLModel.metadata.create_all(production_engine)


def get_production_session() -> Generator[Session]:
    """Get production database session (context manager).

    Yields:
        Database session

    Example:
        with next(get_production_session()) as session:
            # Use session
            pass
    """
    if production_engine is None:
        raise RuntimeError("Production database not initialized. Call init_production_db() first.")

    with Session(production_engine) as session:
        yield session


def save_joke_to_production(
    session: Session,
    joke: Joke,
    import_batch_id: int,
    source_name: str,
    staging_joke_id: int | None = None
) -> str:
    """Save joke to production database.

    Args:
        session: Production database session
        joke: Joke to save
        import_batch_id: Import batch ID
        source_name: Source name (e.g., "taivop/joke-dataset")
        staging_joke_id: Optional staging joke ID

    Returns:
        UUID of saved joke
    """
    # Convert Joke model to JokeDB
    joke_db = JokeDB.from_pydantic(joke)

    # Check if joke already exists
    existing_query = select(JokeDB).where(JokeDB.joke_uuid == joke.id)
    existing = session.exec(existing_query).first()

    if existing:
        # Update existing joke (merge metadata)
        merge_joke_metadata(existing, joke_db)
        session.add(existing)
    else:
        # Add new joke
        session.add(joke_db)

    # Flush to ensure joke is saved before adding provenance
    session.flush()

    # Add provenance
    provenance = JokeProvenanceDB(
        joke_uuid=joke.id,
        import_batch_id=import_batch_id,
        staging_joke_id=staging_joke_id,
        source_name=source_name,
    )
    session.add(provenance)

    session.commit()
    return joke.id


def merge_joke_metadata(existing: JokeDB, new: JokeDB) -> None:
    """Merge metadata from new joke into existing.

    Strategy:
    - Keep existing content (don't overwrite)
    - Merge tags (unique set)
    - Keep highest quality metadata
    - Update last_modified timestamp
    """
    import json

    # Merge tags (unique)
    existing_tags = set(json.loads(existing.tags_json))
    new_tags = set(json.loads(new.tags_json))
    merged_tags = existing_tags | new_tags
    existing.tags_json = json.dumps(sorted(merged_tags))

    # Update last_modified
    existing.last_modified = datetime.now(timezone.utc)

    # Re-compute cached fields
    existing.update_computed_fields()


def get_joke_by_uuid(session: Session, joke_uuid: str) -> JokeDB | None:
    """Get a joke by its UUID.

    Args:
        session: Production database session
        joke_uuid: Joke UUID

    Returns:
        JokeDB instance or None if not found
    """
    query = select(JokeDB).where(JokeDB.joke_uuid == joke_uuid)
    return session.exec(query).first()


def count_production_jokes(session: Session) -> int:
    """Count jokes in production database.

    Args:
        session: Production database session

    Returns:
        Number of jokes
    """
    from sqlalchemy import func

    query = select(func.count()).select_from(JokeDB)
    return session.exec(query).one()
