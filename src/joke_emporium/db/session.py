"""Database session management and initialization."""

from collections.abc import Generator
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

# Default database path
DEFAULT_DB_PATH = Path("data/jokes.db")

# Global engine (set via init_db)
engine = None


def init_db(database_url: str | None = None, echo: bool = False) -> None:
    """Initialize the database engine and create all tables.

    Args:
        database_url: SQLite database URL. If None, uses default path.
        echo: If True, log all SQL statements.
    """
    global engine

    if database_url is None:
        # Create data directory if it doesn't exist
        DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        database_url = f"sqlite:///{DEFAULT_DB_PATH}"

    engine = create_engine(database_url, echo=echo)

    # Import all models to ensure they're registered
    from joke_emporium.db.models import (  # noqa: F401
        AuthorDB,
        JokeAuthorLink,
        JokeCategoryLink,
        JokeDB,
        JokeLinguisticMechanismLink,
        RatingSourceDB,
        VoteDB,
    )

    # Create all tables
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session]:
    """Get a database session (context manager).

    Yields:
        Database session

    Example:
        with next(get_session()) as session:
            # Use session
            pass
    """
    if engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    with Session(engine) as session:
        yield session


def get_engine():
    """Get the global database engine.

    Returns:
        SQLAlchemy engine instance

    Raises:
        RuntimeError: If database hasn't been initialized
    """
    if engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return engine
