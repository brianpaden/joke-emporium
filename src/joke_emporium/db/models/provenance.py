"""Provenance tracking for jokes in production database."""

from datetime import datetime, timezone

from sqlmodel import Column, Field, JSON, SQLModel


class JokeProvenanceDB(SQLModel, table=True):
    """Track where production jokes came from."""

    __tablename__ = "joke_provenance"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Joke reference
    joke_uuid: str = Field(foreign_key="jokes.joke_uuid", index=True, max_length=36,
                          description="UUID of joke in production")

    # Import tracking
    import_batch_id: int | None = Field(default=None, description="Import batch ID from staging")
    staging_joke_id: int | None = Field(default=None, description="Staging joke ID")
    source_name: str = Field(max_length=100, index=True, description="Source identifier")
    imported_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc),
                                   description="When imported to production")

    # Version tracking
    version: int = Field(default=1, ge=1, description="Provenance record version")

    # Additional data
    extra_data: dict | None = Field(default=None, sa_column=Column(JSON), description="Additional metadata")
