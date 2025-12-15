"""Rating database models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from joke_emporium.db.models.joke import JokeDB
    from joke_emporium.models.ratings import RatingSource, Vote


class VoteDB(SQLModel, table=True):
    """Individual vote/rating database model."""

    __tablename__ = "votes"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Foreign key to rating source
    rating_source_id: int = Field(foreign_key="rating_sources.id", index=True)

    # Vote data
    funniness: float = Field(ge=1.0, le=5.0, description="Funniness rating (1-5)")
    quality: float | None = Field(default=None, ge=1.0, le=5.0, description="Quality rating (1-5)")
    timestamp: datetime = Field(description="When vote was cast")

    # Relationship
    rating_source: "RatingSourceDB" = Relationship(back_populates="votes")

    @classmethod
    def from_pydantic(cls, vote: "Vote", rating_source_id: int) -> "VoteDB":
        """Convert from Pydantic Vote model to database model."""
        return cls(
            rating_source_id=rating_source_id,
            funniness=vote.funniness,
            quality=vote.quality,
            timestamp=vote.timestamp,
        )

    def to_pydantic(self) -> "Vote":
        """Convert to Pydantic Vote model."""
        from joke_emporium.models.ratings import Vote

        return Vote(
            funniness=self.funniness,
            quality=self.quality,
            timestamp=self.timestamp,
        )


class RatingSourceDB(SQLModel, table=True):
    """Rating source database model with aggregated ratings."""

    __tablename__ = "rating_sources"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Foreign key to joke
    joke_id: int = Field(foreign_key="jokes.id", index=True)

    # Source information
    source: str = Field(max_length=500, description="Source identifier")
    min_rating: float = Field(default=1.0, description="Minimum rating in original scale")
    max_rating: float = Field(default=5.0, description="Maximum rating in original scale")

    # Aggregated ratings
    total_ratings: int = Field(ge=0, description="Total number of ratings")
    avg_funniness: float = Field(description="Average funniness in original scale")
    avg_quality: float | None = Field(default=None, description="Average quality in original scale")

    # Normalized ratings (computed and cached)
    normalized_avg_funniness: float = Field(description="Normalized funniness (1-5)")
    normalized_avg_quality: float | None = Field(default=None, description="Normalized quality (1-5)")

    # Metadata (stored as JSON)
    metadata_json: str | None = Field(default=None, sa_column_kwargs={"name": "metadata"})

    # Relationships
    joke: "JokeDB" = Relationship(back_populates="rating_sources")
    votes: list[VoteDB] = Relationship(
        back_populates="rating_source", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    @staticmethod
    def _compute_normalized(value: float, min_rating: float, max_rating: float) -> float:
        """Compute normalized rating (1-5 scale)."""
        if max_rating == min_rating:
            return 3.0
        return 1.0 + (value - min_rating) * 4.0 / (max_rating - min_rating)

    @classmethod
    def from_pydantic(cls, rating: "RatingSource", joke_id: int) -> "RatingSourceDB":
        """Convert from Pydantic RatingSource model to database model."""
        import json

        # Compute normalized values
        normalized_funniness = cls._compute_normalized(rating.avg_funniness, rating.min_rating, rating.max_rating)

        normalized_quality = None
        if rating.avg_quality is not None:
            normalized_quality = cls._compute_normalized(rating.avg_quality, rating.min_rating, rating.max_rating)

        return cls(
            joke_id=joke_id,
            source=rating.source,
            min_rating=rating.min_rating,
            max_rating=rating.max_rating,
            total_ratings=rating.total_ratings,
            avg_funniness=rating.avg_funniness,
            avg_quality=rating.avg_quality,
            normalized_avg_funniness=normalized_funniness,
            normalized_avg_quality=normalized_quality,
            metadata_json=json.dumps(rating.metadata) if rating.metadata else None,
        )

    def to_pydantic(self, include_votes: bool = False) -> "RatingSource":
        """Convert to Pydantic RatingSource model."""
        import json

        from joke_emporium.models.ratings import RatingSource

        votes_list = None
        if include_votes and self.votes:
            votes_list = [vote.to_pydantic() for vote in self.votes]

        return RatingSource(
            source=self.source,
            min_rating=self.min_rating,
            max_rating=self.max_rating,
            total_ratings=self.total_ratings,
            avg_funniness=self.avg_funniness,
            avg_quality=self.avg_quality,
            votes=votes_list,
            metadata=json.loads(self.metadata_json) if self.metadata_json else None,
        )

    def update_normalized_ratings(self) -> None:
        """Update cached normalized rating values."""
        self.normalized_avg_funniness = self._compute_normalized(self.avg_funniness, self.min_rating, self.max_rating)

        if self.avg_quality is not None:
            self.normalized_avg_quality = self._compute_normalized(self.avg_quality, self.min_rating, self.max_rating)
        else:
            self.normalized_avg_quality = None
