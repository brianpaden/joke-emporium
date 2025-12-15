"""Main Joke model."""

from pydantic import BaseModel, Field, computed_field

from joke_emporium.models.content import JokeElement
from joke_emporium.models.enums import (
    Category,
    CognitiveType,
    LinguisticMechanism,
    MaturityRating,
    StructureType,
)
from joke_emporium.models.flags import ContentFlags
from joke_emporium.models.gtvh import GTVHAnnotation
from joke_emporium.models.metadata import JokeMetadata
from joke_emporium.models.ratings import RatingSource


class Joke(BaseModel):
    """A complete joke with all metadata and annotations.

    This is the main model representing a single joke in the dataset.
    """

    # Identification
    id: str = Field(..., description="Unique identifier (UUID) for this joke")
    version: int = Field(default=1, ge=1, description="Schema version for this joke")

    # Content
    content: list[JokeElement] = Field(..., min_length=1, description="List of joke elements (setup, punchline, etc.)")

    # Categorization
    categories: list[Category] = Field(default_factory=list, description="Primary topic categories (can be multiple)")
    structure: StructureType | None = Field(default=None, description="Narrative structure of the joke")
    mechanisms: list[LinguisticMechanism] = Field(
        default_factory=list, description="Linguistic mechanisms used (puns, wordplay, etc.)"
    )
    maturity_rating: MaturityRating = Field(
        default=MaturityRating.G, description="Content maturity rating (G, PG, PG13, R, X)"
    )
    cognitive_type: CognitiveType | None = Field(default=None, description="Cognitive joke type (Chalmers taxonomy)")

    # Tags & Flags
    tags: list[str] = Field(default_factory=list, description="Free-form tags for additional categorization")
    flags: ContentFlags = Field(default_factory=ContentFlags, description="Content warning flags")

    # Ratings
    ratings: list[RatingSource] = Field(default_factory=list, description="Ratings from various sources")

    # Metadata
    metadata: JokeMetadata = Field(..., description="Source, authorship, and temporal metadata")

    # Advanced annotations (optional)
    gtvh: GTVHAnnotation | None = Field(default=None, description="Optional GTVH framework annotation")

    # Computed properties
    @computed_field  # type: ignore[prop-decorator]
    @property
    def weighted_avg_funniness(self) -> float | None:
        """Calculate weighted average funniness across all rating sources.

        Returns None if there are no ratings.

        Formula: sum(normalized_rating * count) / sum(count)
        """
        if not self.ratings:
            return None

        total_weight = sum(r.total_ratings for r in self.ratings)
        if total_weight == 0:
            return None

        weighted_sum = sum(r.normalized_avg_funniness * r.total_ratings for r in self.ratings)

        return weighted_sum / total_weight

    @computed_field  # type: ignore[prop-decorator]
    @property
    def weighted_avg_quality(self) -> float | None:
        """Calculate weighted average quality across all rating sources.

        Returns None if there are no quality ratings.

        Formula: sum(normalized_rating * count) / sum(count)
        """
        if not self.ratings:
            return None

        # Filter sources that have quality ratings
        quality_ratings = [r for r in self.ratings if r.normalized_avg_quality is not None]

        if not quality_ratings:
            return None

        total_weight = sum(r.total_ratings for r in quality_ratings)
        if total_weight == 0:
            return None

        weighted_sum = sum(
            r.normalized_avg_quality * r.total_ratings  # type: ignore
            for r in quality_ratings
        )

        return weighted_sum / total_weight

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_ratings_count(self) -> int:
        """Total number of ratings across all sources."""
        return sum(r.total_ratings for r in self.ratings)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def text_preview(self) -> str:
        """Generate a text preview of the joke (first 100 chars).

        Useful for displaying in lists or search results.
        """
        full_text = " ".join(element.text for element in self.content)
        if len(full_text) <= 100:
            return full_text
        return full_text[:97] + "..."

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "version": 1,
                    "content": [
                        {"type": "setup", "text": "Why did the scarecrow win an award?"},
                        {"type": "punchline", "text": "Because he was outstanding in his field!"},
                    ],
                    "categories": ["work", "wordplay"],
                    "structure": "qa",
                    "mechanisms": ["pun_homographic"],
                    "maturity_rating": "g",
                    "cognitive_type": "interpretational_sds",
                    "tags": ["classic", "pun", "wholesome"],
                    "flags": {
                        "profanity": False,
                        "dark_humor": False,
                        "offensive": False,
                        "political": False,
                        "sexual": False,
                        "violent": False,
                        "stereotypical": False,
                        "religious": False,
                        "requires_context": False,
                    },
                    "ratings": [
                        {
                            "source": "manual_annotation",
                            "min_rating": 1.0,
                            "max_rating": 5.0,
                            "total_ratings": 3,
                            "avg_funniness": 4.67,
                            "avg_quality": 4.33,
                            "votes": None,
                            "metadata": None,
                        }
                    ],
                    "metadata": {
                        "language": "en",
                        "authors": [{"id": "anonymous", "type": "anonymous", "name": "Anonymous"}],
                        "source": None,
                        "engagement": None,
                        "created_date": None,
                        "added_date": "2024-01-15T10:30:00Z",
                        "last_modified": "2024-01-15T10:30:00Z",
                        "verified": True,
                        "metadata": None,
                    },
                    "gtvh": None,
                }
            ]
        }
    }
