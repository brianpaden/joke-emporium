"""Shared test fixtures and configuration."""

from datetime import UTC, datetime

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


@pytest.fixture
def staging_db_engine():
    """Create an in-memory staging database engine."""
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Create all tables
    SQLModel.metadata.create_all(engine)

    yield engine

    # Clean up
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def staging_session(staging_db_engine):
    """Create a staging database session."""
    with Session(staging_db_engine) as session:
        yield session


@pytest.fixture
def sample_import_batch(staging_session):
    """Create a sample import batch in the staging database."""
    from joke_emporium.db.models.staging import ImportBatchDB

    batch = ImportBatchDB(
        import_id="test-import-123",
        source="test-source",
        source_version="v1.0.0",
        imported_at=datetime.now(UTC),
        total_records=10,
        successful=10,
        failed=0,
    )
    staging_session.add(batch)
    staging_session.commit()
    staging_session.refresh(batch)
    return batch


@pytest.fixture
def sample_staging_joke(staging_session, sample_import_batch):
    """Create a sample staging joke in the database."""
    import json

    from joke_emporium.db.models.staging import StagingJokeDB

    joke = StagingJokeDB(
        joke_uuid="test-uuid-456",
        version=1,
        content_json=json.dumps(
            [
                {"type": "setup", "text": "Why did the chicken cross the road?"},
                {"type": "punchline", "text": "To get to the other side!"},
            ]
        ),
        structure="two_part",
        maturity_rating="G",
        tags_json=json.dumps(["animal", "classic"]),
        flags_json=json.dumps({"nsfw": False, "offensive": False}),
        language="en",
        source_platform="reddit",
        source_url="https://reddit.com/r/jokes/123",
        added_date=datetime.now(UTC),
        last_modified=datetime.now(UTC),
        verified=False,
        engagement_json=json.dumps({"upvotes": 150, "downvotes": 10, "comments": 25}),
        weighted_avg_funniness=75.5,
        weighted_avg_quality=80.0,
        total_ratings_count=100,
        text_preview="Why did the chicken cross the road? To get to the other side!",
        import_batch_id=sample_import_batch.id,
        original_data_json=json.dumps({"source_id": "reddit-123", "score": 150}),
    )
    staging_session.add(joke)
    staging_session.commit()
    staging_session.refresh(joke)
    return joke
