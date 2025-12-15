"""Collection model for grouping jokes."""

from datetime import datetime

from pydantic import BaseModel, Field, computed_field

from joke_emporium.models.enums import MaturityRating
from joke_emporium.models.joke import Joke


class Collection(BaseModel):
    """A collection of jokes (e.g., jokes_en_clean.json).

    Represents a single file in the dataset.
    """

    # Collection metadata
    name: str = Field(
        ...,
        description="Collection name (e.g., 'jokes_en_clean')"
    )
    version: str = Field(
        ...,
        description="Collection version (semantic versioning recommended)"
    )
    language: str = Field(
        ...,
        min_length=2,
        max_length=5,
        description="ISO 639-1 language code (e.g., 'en', 'es', 'fr')"
    )
    maturity_filter: MaturityRating | None = Field(
        default=None,
        description="Maximum maturity rating in this collection (None = all ratings)"
    )
    description: str | None = Field(
        default=None,
        description="Description of this collection"
    )
    created_date: datetime = Field(
        ...,
        description="When this collection was created"
    )
    last_modified: datetime = Field(
        ...,
        description="When this collection was last updated"
    )
    metadata: dict | None = Field(
        default=None,
        description="Additional collection-level metadata"
    )

    # The jokes
    jokes: list[Joke] = Field(
        default_factory=list,
        description="List of jokes in this collection"
    )

    # Computed statistics
    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_jokes(self) -> int:
        """Total number of jokes in this collection."""
        return len(self.jokes)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_ratings(self) -> int:
        """Total number of ratings across all jokes."""
        return sum(joke.total_ratings_count for joke in self.jokes)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def avg_funniness(self) -> float | None:
        """Average funniness across all jokes with ratings.

        Returns None if no jokes have ratings.
        """
        jokes_with_ratings = [
            joke for joke in self.jokes
            if joke.weighted_avg_funniness is not None
        ]

        if not jokes_with_ratings:
            return None

        total = sum(
            joke.weighted_avg_funniness  # type: ignore
            for joke in jokes_with_ratings
        )

        return total / len(jokes_with_ratings)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def category_distribution(self) -> dict[str, int]:
        """Count of jokes per category.

        Returns a dictionary mapping category names to counts.
        """
        distribution: dict[str, int] = {}

        for joke in self.jokes:
            for category in joke.categories:
                category_name = category.value
                distribution[category_name] = distribution.get(category_name, 0) + 1

        return distribution

    @computed_field  # type: ignore[prop-decorator]
    @property
    def maturity_distribution(self) -> dict[str, int]:
        """Count of jokes per maturity rating.

        Returns a dictionary mapping maturity ratings to counts.
        """
        distribution: dict[str, int] = {}

        for joke in self.jokes:
            rating = joke.maturity_rating.value
            distribution[rating] = distribution.get(rating, 0) + 1

        return distribution

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "jokes_en_clean",
                    "version": "1.0.0",
                    "language": "en",
                    "maturity_filter": "pg13",
                    "description": "English language jokes with maximum PG-13 rating",
                    "created_date": "2024-01-01T00:00:00Z",
                    "last_modified": "2024-01-15T10:30:00Z",
                    "metadata": {
                        "source_files": ["reddit_jokes.json", "manual_entries.json"],
                        "contributors": ["user1", "user2"]
                    },
                    "jokes": []
                }
            ]
        }
    }
