"""Staging database models for import validation."""

from datetime import datetime
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel

from joke_emporium.db.models.joke import JokeDB


class ReviewStatus(str, Enum):
    """Status of joke review for merge."""
    PENDING = "pending"           # Not yet reviewed
    APPROVED = "approved"         # Ready to merge
    REJECTED = "rejected"         # Don't merge
    UNDER_REVIEW = "under_review" # Needs manual review
    DUPLICATE = "duplicate"       # Duplicate of existing joke
    MERGED = "merged"             # Already merged to production


class ImportBatchDB(SQLModel, table=True):
    """Track import batches in staging database.

    Each import operation creates one import batch that contains
    multiple staging jokes.
    """

    __tablename__ = "import_batches"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Import metadata
    import_id: str = Field(index=True, unique=True, max_length=36, description="UUID for this import batch")
    source: str = Field(max_length=100, description="Source identifier")
    source_version: str | None = Field(default=None, max_length=100, description="Git commit hash or version")
    imported_at: datetime = Field(description="When the import was performed")

    # Statistics
    total_records: int = Field(default=0, ge=0, description="Total records processed")
    successful: int = Field(default=0, ge=0, description="Successfully imported records")
    failed: int = Field(default=0, ge=0, description="Failed records")

    # Validation
    validation_status: str = Field(
        default="pending", max_length=20, description="Validation status: pending/approved/rejected"
    )
    notes: str | None = Field(default=None, description="Additional notes or error messages")

    # Relationships
    staging_jokes: list["StagingJokeDB"] = Relationship(
        back_populates="import_batch", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class StagingJokeDB(SQLModel, table=True):
    """Staging joke model for import validation.

    Contains all joke fields plus import tracking and validation metadata.
    """

    __tablename__ = "staging_jokes"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Identification (from JokeDB)
    joke_uuid: str = Field(index=True, max_length=36, description="UUID identifier")
    version: int = Field(default=1, ge=1, description="Schema version")

    # Content (from JokeDB)
    content_json: str = Field(sa_column_kwargs={"name": "content"}, description="JSON array of joke elements")

    # Categorization (from JokeDB)
    structure: str | None = Field(default=None, max_length=50, description="Structure type")
    maturity_rating: str = Field(max_length=10, default="g", description="Maturity rating")
    cognitive_type: str | None = Field(default=None, max_length=50, description="Cognitive type")

    # Tags (from JokeDB)
    tags_json: str = Field(default="[]", sa_column_kwargs={"name": "tags"}, description="JSON array of tags")

    # Content flags (from JokeDB)
    flags_json: str = Field(sa_column_kwargs={"name": "flags"}, description="JSON object of content flags")

    # Metadata fields (from JokeDB)
    language: str = Field(default="en", max_length=5, description="Language code")
    source_platform: str | None = Field(default=None, max_length=50, description="Source platform")
    source_url: str | None = Field(default=None, max_length=500, description="Source URL")
    scraped_date: datetime | None = Field(default=None, description="When scraped")
    created_date: datetime | None = Field(default=None, description="When originally created")
    added_date: datetime = Field(description="When added to dataset")
    last_modified: datetime = Field(description="When last modified")
    verified: bool = Field(default=False, description="Manually verified")

    # Engagement metrics (from JokeDB)
    engagement_json: str | None = Field(
        default=None, sa_column_kwargs={"name": "engagement"}, description="JSON object of engagement metrics"
    )

    # GTVH annotation (from JokeDB)
    gtvh_json: str | None = Field(default=None, sa_column_kwargs={"name": "gtvh"}, description="JSON GTVH annotation")

    # Additional metadata (from JokeDB)
    metadata_json: str | None = Field(default=None, sa_column_kwargs={"name": "metadata"})

    # Cached computed fields (from JokeDB)
    weighted_avg_funniness: float | None = Field(default=None, description="Cached weighted avg funniness (1-5)")
    weighted_avg_quality: float | None = Field(default=None, description="Cached weighted avg quality (1-5)")
    total_ratings_count: int = Field(default=0, description="Cached total ratings count")
    text_preview: str = Field(default="", max_length=150, description="Cached text preview")

    # Import tracking (staging-specific)
    import_batch_id: int | None = Field(default=None, foreign_key="import_batches.id", index=True)

    # Validation metadata (staging-specific)
    validation_status: str = Field(
        default="pending", max_length=20, description="Validation status: pending/approved/rejected"
    )
    validation_notes: str | None = Field(default=None, description="Validation errors or notes")
    duplicate_of: str | None = Field(
        default=None, max_length=36, description="UUID of duplicate joke if detected"
    )

    # Review tracking (staging-specific)
    review_status: str = Field(default=ReviewStatus.PENDING, max_length=20, index=True,
                               description="Review status for merge")
    review_notes: str | None = Field(default=None, description="Review notes or reason")
    reviewed_by: str | None = Field(default=None, max_length=100, description="User who reviewed")
    reviewed_at: datetime | None = Field(default=None, description="When reviewed")

    # Duplicate tracking (staging-specific)
    duplicate_of_uuid: str | None = Field(default=None, max_length=36, index=True,
                                          description="UUID of duplicate joke if found")
    duplicate_similarity: float | None = Field(default=None, description="Similarity score (0-1)")

    # Merge tracking (staging-specific)
    merged_to_uuid: str | None = Field(default=None, max_length=36, description="UUID in production")
    merged_at: datetime | None = Field(default=None, description="When merged to production")

    # Raw data preservation (staging-specific)
    original_data_json: str = Field(description="Original source data as JSON")

    # Relationships
    import_batch: ImportBatchDB | None = Relationship(back_populates="staging_jokes")

    @classmethod
    def from_joke_and_raw(
        cls, joke: "Joke", raw_data: dict, import_batch_id: int  # noqa: F821
    ) -> "StagingJokeDB":
        """Create staging joke from Joke model and raw data.

        Args:
            joke: Pydantic Joke model
            raw_data: Original raw data dictionary
            import_batch_id: ID of import batch

        Returns:
            StagingJokeDB instance
        """
        import json

        from joke_emporium.models.joke import Joke

        # Convert joke to JokeDB format
        joke_db = JokeDB.from_pydantic(joke)

        # Create staging joke with fields from JokeDB plus staging-specific fields
        staging_joke = cls(
            joke_uuid=joke_db.joke_uuid,
            version=joke_db.version,
            content_json=joke_db.content_json,
            structure=joke_db.structure,
            maturity_rating=joke_db.maturity_rating,
            cognitive_type=joke_db.cognitive_type,
            tags_json=joke_db.tags_json,
            flags_json=joke_db.flags_json,
            language=joke_db.language,
            source_platform=joke_db.source_platform,
            source_url=joke_db.source_url,
            scraped_date=joke_db.scraped_date,
            created_date=joke_db.created_date,
            added_date=joke_db.added_date,
            last_modified=joke_db.last_modified,
            verified=joke_db.verified,
            engagement_json=joke_db.engagement_json,
            gtvh_json=joke_db.gtvh_json,
            metadata_json=joke_db.metadata_json,
            weighted_avg_funniness=joke_db.weighted_avg_funniness,
            weighted_avg_quality=joke_db.weighted_avg_quality,
            total_ratings_count=joke_db.total_ratings_count,
            text_preview=joke_db.text_preview,
            import_batch_id=import_batch_id,
            validation_status="pending",
            original_data_json=json.dumps(raw_data),
        )

        return staging_joke
