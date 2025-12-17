"""Shared test fixtures and configuration."""

from datetime import UTC

import pytest
from sqlmodel import Session, SQLModel, create_engine

from joke_emporium.models.author import Author, AuthorType
from joke_emporium.models.content import JokeElement
from joke_emporium.models.enums import ElementType, MaturityRating
from joke_emporium.models.joke import Joke
from joke_emporium.models.metadata import JokeMetadata


@pytest.fixture
def test_db_engine():
    """Create an in-memory test database engine."""
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Create all tables
    SQLModel.metadata.create_all(engine)

    yield engine

    # Clean up
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def test_db_session(test_db_engine):
    """Create a test database session."""
    with Session(test_db_engine) as session:
        yield session


@pytest.fixture
def sample_joke():
    """Create a sample joke for testing."""
    from datetime import datetime

    return Joke(
        id="test-uuid-123",
        content=[
            JokeElement(type=ElementType.SETUP, text="Why did the chicken cross the road?"),
            JokeElement(type=ElementType.PUNCHLINE, text="To get to the other side!"),
        ],
        maturity_rating=MaturityRating.G,
        metadata=JokeMetadata(
            language="en",
            authors=[Author(id="test-author", type=AuthorType.ANONYMOUS, name="Anonymous")],
            added_date=datetime.now(UTC),
            last_modified=datetime.now(UTC),
            verified=False,
        ),
    )


@pytest.fixture
def sample_raw_data():
    """Create sample raw data dictionary for testing."""
    return {
        "id": "source-123",
        "type": "twoPart",
        "setup": "Why did the chicken cross the road?",
        "punchline": "To get to the other side!",
        "score": 42,
    }
