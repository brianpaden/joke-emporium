"""Rating and voting models."""

from datetime import datetime

from pydantic import BaseModel, Field, computed_field, field_validator


class Vote(BaseModel):
    """A single vote/rating from an individual.

    Tracks individual ratings with timestamps for detailed analysis.
    """

    funniness: float = Field(
        ...,
        ge=1.0,
        le=5.0,
        description="Funniness rating (1.0-5.0 scale)"
    )
    quality: float | None = Field(
        default=None,
        ge=1.0,
        le=5.0,
        description="Quality/cleverness rating (1.0-5.0 scale, optional)"
    )
    timestamp: datetime = Field(
        ...,
        description="When this vote was cast"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "funniness": 4.5,
                    "quality": 4.0,
                    "timestamp": "2024-01-15T14:23:45Z"
                }
            ]
        }
    }


class RatingSource(BaseModel):
    """Aggregated ratings from a specific source.

    Supports different rating scales with automatic normalization to 1-5 scale.

    Common scales:
    - Reddit: min=0.0, max=1.0 (upvote ratio)
    - IMDB-style: min=1.0, max=10.0
    - Manual annotation: min=1.0, max=5.0
    - Percentage: min=0, max=100
    """

    source: str = Field(
        ...,
        description="Source identifier (URL, platform name, dataset name, etc.)"
    )
    min_rating: float = Field(
        default=1.0,
        description="Minimum possible rating in the original scale"
    )
    max_rating: float = Field(
        default=5.0,
        description="Maximum possible rating in the original scale"
    )
    total_ratings: int = Field(
        ...,
        ge=0,
        description="Total number of ratings from this source"
    )
    avg_funniness: float = Field(
        ...,
        description="Average funniness rating in the ORIGINAL scale"
    )
    avg_quality: float | None = Field(
        default=None,
        description="Average quality rating in the ORIGINAL scale (optional)"
    )
    votes: list[Vote] | None = Field(
        default=None,
        description="Optional list of individual votes (for detailed datasets)"
    )
    metadata: dict | None = Field(
        default=None,
        description="Additional source-specific metadata"
    )

    @field_validator("avg_funniness")
    @classmethod
    def validate_avg_funniness_in_range(cls, v: float, info) -> float:
        """Ensure avg_funniness is within the specified min/max range."""
        min_rating = info.data.get("min_rating", 1.0)
        max_rating = info.data.get("max_rating", 5.0)

        if not (min_rating <= v <= max_rating):
            raise ValueError(
                f"avg_funniness ({v}) must be between min_rating ({min_rating}) "
                f"and max_rating ({max_rating})"
            )
        return v

    @field_validator("avg_quality")
    @classmethod
    def validate_avg_quality_in_range(cls, v: float | None, info) -> float | None:
        """Ensure avg_quality is within the specified min/max range."""
        if v is None:
            return None

        min_rating = info.data.get("min_rating", 1.0)
        max_rating = info.data.get("max_rating", 5.0)

        if not (min_rating <= v <= max_rating):
            raise ValueError(
                f"avg_quality ({v}) must be between min_rating ({min_rating}) "
                f"and max_rating ({max_rating})"
            )
        return v

    @computed_field  # type: ignore[prop-decorator]
    @property
    def normalized_avg_funniness(self) -> float:
        """Auto-compute normalized funniness rating (1.0-5.0 scale).

        Formula: 1.0 + (raw - min) * 4.0 / (max - min)

        Examples:
            - Reddit (0-1): 0.936 → 4.74
            - IMDB (1-10): 7.8 → 4.02
            - Already 1-5: 4.67 → 4.67
        """
        if self.max_rating == self.min_rating:
            # Edge case: invalid scale, return middle value
            return 3.0

        return 1.0 + (self.avg_funniness - self.min_rating) * 4.0 / (
            self.max_rating - self.min_rating
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def normalized_avg_quality(self) -> float | None:
        """Auto-compute normalized quality rating (1.0-5.0 scale).

        Formula: 1.0 + (raw - min) * 4.0 / (max - min)
        """
        if self.avg_quality is None:
            return None

        if self.max_rating == self.min_rating:
            # Edge case: invalid scale, return middle value
            return 3.0

        return 1.0 + (self.avg_quality - self.min_rating) * 4.0 / (
            self.max_rating - self.min_rating
        )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "source": "https://reddit.com/r/Jokes/comments/abc123",
                    "min_rating": 0.0,
                    "max_rating": 1.0,
                    "total_ratings": 1335,
                    "avg_funniness": 0.936,
                    "avg_quality": None,
                    "votes": None,
                    "metadata": {"upvotes": 1250, "downvotes": 85}
                },
                {
                    "source": "manual_annotation",
                    "min_rating": 1.0,
                    "max_rating": 5.0,
                    "total_ratings": 3,
                    "avg_funniness": 4.67,
                    "avg_quality": 4.33,
                    "votes": [
                        {
                            "funniness": 5.0,
                            "quality": 4.0,
                            "timestamp": "2024-01-15T14:23:45Z"
                        },
                        {
                            "funniness": 4.0,
                            "quality": 5.0,
                            "timestamp": "2024-01-15T15:10:22Z"
                        },
                        {
                            "funniness": 5.0,
                            "quality": 4.0,
                            "timestamp": "2024-01-15T16:05:33Z"
                        }
                    ],
                    "metadata": None
                }
            ]
        }
    }
