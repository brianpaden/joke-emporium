"""Joke database model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from joke_emporium.models.enums import CognitiveType, MaturityRating, StructureType

if TYPE_CHECKING:
    from joke_emporium.db.models.associations import JokeAuthorLink, JokeCategoryLink, JokeLinguisticMechanismLink
    from joke_emporium.db.models.rating import RatingSourceDB
    from joke_emporium.models.joke import Joke


class JokeDB(SQLModel, table=True):
    """Joke database model.

    Main table storing jokes with cached computed fields.
    """

    __tablename__ = "jokes"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Identification
    joke_uuid: str = Field(index=True, unique=True, max_length=36, description="UUID identifier")
    version: int = Field(default=1, ge=1, description="Schema version")

    # Content (stored as JSON array of JokeElement)
    content_json: str = Field(sa_column_kwargs={"name": "content"}, description="JSON array of joke elements")

    # Categorization
    structure: str | None = Field(default=None, max_length=50, description="Structure type")
    maturity_rating: str = Field(max_length=10, default="g", description="Maturity rating")
    cognitive_type: str | None = Field(default=None, max_length=50, description="Cognitive type")

    # Tags (stored as JSON array)
    tags_json: str = Field(default="[]", sa_column_kwargs={"name": "tags"}, description="JSON array of tags")

    # Content flags (stored as JSON object)
    flags_json: str = Field(sa_column_kwargs={"name": "flags"}, description="JSON object of content flags")

    # Metadata fields
    language: str = Field(default="en", max_length=5, description="Language code")
    source_platform: str | None = Field(default=None, max_length=50, description="Source platform")
    source_url: str | None = Field(default=None, max_length=500, description="Source URL")
    scraped_date: datetime | None = Field(default=None, description="When scraped")
    created_date: datetime | None = Field(default=None, description="When originally created")
    added_date: datetime = Field(description="When added to dataset")
    last_modified: datetime = Field(description="When last modified")
    verified: bool = Field(default=False, description="Manually verified")

    # Engagement metrics (stored as JSON object)
    engagement_json: str | None = Field(
        default=None, sa_column_kwargs={"name": "engagement"}, description="JSON object of engagement metrics"
    )

    # GTVH annotation (stored as JSON object)
    gtvh_json: str | None = Field(default=None, sa_column_kwargs={"name": "gtvh"}, description="JSON GTVH annotation")

    # Additional metadata (stored as JSON)
    metadata_json: str | None = Field(default=None, sa_column_kwargs={"name": "metadata"})

    # Cached computed fields
    weighted_avg_funniness: float | None = Field(default=None, description="Cached weighted avg funniness (1-5)")
    weighted_avg_quality: float | None = Field(default=None, description="Cached weighted avg quality (1-5)")
    total_ratings_count: int = Field(default=0, description="Cached total ratings count")
    text_preview: str = Field(default="", max_length=150, description="Cached text preview")

    # Relationships
    rating_sources: list["RatingSourceDB"] = Relationship(
        back_populates="joke", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    author_links: list["JokeAuthorLink"] = Relationship(
        back_populates="joke", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    category_links: list["JokeCategoryLink"] = Relationship(
        back_populates="joke", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    mechanism_links: list["JokeLinguisticMechanismLink"] = Relationship(
        back_populates="joke", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    def update_computed_fields(self) -> None:
        """Update all cached computed fields based on current data."""
        # Update weighted averages from rating sources
        if self.rating_sources:
            total_weight = sum(r.total_ratings for r in self.rating_sources)

            if total_weight > 0:
                # Weighted avg funniness
                weighted_sum_funniness = sum(r.normalized_avg_funniness * r.total_ratings for r in self.rating_sources)
                self.weighted_avg_funniness = weighted_sum_funniness / total_weight

                # Weighted avg quality
                quality_sources = [r for r in self.rating_sources if r.normalized_avg_quality is not None]
                if quality_sources:
                    quality_weight = sum(r.total_ratings for r in quality_sources)
                    if quality_weight > 0:
                        weighted_sum_quality = sum(
                            r.normalized_avg_quality * r.total_ratings  # type: ignore
                            for r in quality_sources
                        )
                        self.weighted_avg_quality = weighted_sum_quality / quality_weight
                else:
                    self.weighted_avg_quality = None
            else:
                self.weighted_avg_funniness = None
                self.weighted_avg_quality = None

            # Total ratings count
            self.total_ratings_count = total_weight
        else:
            self.weighted_avg_funniness = None
            self.weighted_avg_quality = None
            self.total_ratings_count = 0

        # Update text preview from content
        import json

        try:
            content_list = json.loads(self.content_json)
            full_text = " ".join(elem.get("text", "") for elem in content_list)
            if len(full_text) <= 100:
                self.text_preview = full_text
            else:
                self.text_preview = full_text[:97] + "..."
        except (json.JSONDecodeError, AttributeError):
            self.text_preview = ""

    @classmethod
    def from_pydantic(cls, joke: "Joke") -> "JokeDB":
        """Convert from Pydantic Joke model to database model."""
        import json

        # Serialize content
        content_json = json.dumps([elem.model_dump() for elem in joke.content])

        # Serialize tags
        tags_json = json.dumps(joke.tags)

        # Serialize flags
        flags_json = json.dumps(joke.flags.model_dump())

        # Serialize GTVH
        gtvh_json = None
        if joke.gtvh:
            gtvh_json = json.dumps(joke.gtvh.model_dump())

        # Serialize engagement
        engagement_json = None
        if joke.metadata.engagement:
            engagement_json = json.dumps(joke.metadata.engagement.model_dump())

        # Extract source info
        source_platform = None
        source_url = None
        scraped_date = None
        if joke.metadata.source:
            source_platform = joke.metadata.source.platform.value
            source_url = joke.metadata.source.url
            scraped_date = joke.metadata.source.scraped_date

        # Create joke DB instance
        joke_db = cls(
            joke_uuid=joke.id,
            version=joke.version,
            content_json=content_json,
            structure=joke.structure.value if joke.structure else None,
            maturity_rating=joke.maturity_rating.value,
            cognitive_type=joke.cognitive_type.value if joke.cognitive_type else None,
            tags_json=tags_json,
            flags_json=flags_json,
            language=joke.metadata.language,
            source_platform=source_platform,
            source_url=source_url,
            scraped_date=scraped_date,
            created_date=joke.metadata.created_date,
            added_date=joke.metadata.added_date,
            last_modified=joke.metadata.last_modified,
            verified=joke.metadata.verified,
            engagement_json=engagement_json,
            gtvh_json=gtvh_json,
            metadata_json=json.dumps(joke.metadata.metadata) if joke.metadata.metadata else None,
        )

        # Compute cached fields
        joke_db.update_computed_fields()

        return joke_db

    def to_pydantic(
        self,
        include_authors: bool = True,
        include_categories: bool = True,
        include_mechanisms: bool = True,
        include_ratings: bool = True,
    ) -> "Joke":
        """Convert to Pydantic Joke model."""
        import json

        from joke_emporium.models.content import JokeElement
        from joke_emporium.models.enums import Category, LinguisticMechanism, SourcePlatform
        from joke_emporium.models.flags import ContentFlags
        from joke_emporium.models.gtvh import GTVHAnnotation
        from joke_emporium.models.joke import Joke
        from joke_emporium.models.metadata import Engagement, JokeMetadata, Source

        # Deserialize content
        content_data = json.loads(self.content_json)
        content = [JokeElement(**elem) for elem in content_data]

        # Deserialize categories
        categories = []
        if include_categories:
            categories = [Category(link.category) for link in self.category_links]

        # Deserialize mechanisms
        mechanisms = []
        if include_mechanisms:
            mechanisms = [LinguisticMechanism(link.mechanism) for link in self.mechanism_links]

        # Deserialize tags
        tags = json.loads(self.tags_json)

        # Deserialize flags
        flags_data = json.loads(self.flags_json)
        flags = ContentFlags(**flags_data)

        # Deserialize ratings
        ratings = []
        if include_ratings:
            ratings = [rs.to_pydantic(include_votes=True) for rs in self.rating_sources]

        # Deserialize authors
        authors = None
        if include_authors and self.author_links:
            authors = [link.author.to_pydantic() for link in self.author_links]

        # Deserialize source
        source = None
        if self.source_platform:
            source = Source(
                platform=SourcePlatform(self.source_platform),
                url=self.source_url,
                scraped_date=self.scraped_date,
                metadata=None,  # Could parse from source metadata if needed
            )

        # Deserialize engagement
        engagement = None
        if self.engagement_json:
            engagement_data = json.loads(self.engagement_json)
            engagement = Engagement(**engagement_data)

        # Deserialize GTVH
        gtvh = None
        if self.gtvh_json:
            gtvh_data = json.loads(self.gtvh_json)
            gtvh = GTVHAnnotation(**gtvh_data)

        # Create metadata
        metadata = JokeMetadata(
            language=self.language,
            authors=authors,
            source=source,
            engagement=engagement,
            created_date=self.created_date,
            added_date=self.added_date,
            last_modified=self.last_modified,
            verified=self.verified,
            metadata=json.loads(self.metadata_json) if self.metadata_json else None,
        )

        # Create and return Joke
        return Joke(
            id=self.joke_uuid,
            version=self.version,
            content=content,
            categories=categories,
            structure=StructureType(self.structure) if self.structure else None,
            mechanisms=mechanisms,
            maturity_rating=MaturityRating(self.maturity_rating),
            cognitive_type=CognitiveType(self.cognitive_type) if self.cognitive_type else None,
            tags=tags,
            flags=flags,
            ratings=ratings,
            metadata=metadata,
            gtvh=gtvh,
        )
