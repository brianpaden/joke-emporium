"""Metadata models for jokes."""

from datetime import datetime

from pydantic import BaseModel, Field

from joke_emporium.models.author import Author
from joke_emporium.models.enums import SourcePlatform


class Source(BaseModel):
    """Information about where a joke originated."""

    platform: SourcePlatform = Field(
        ...,
        description="Platform where the joke was found"
    )
    url: str | None = Field(
        default=None,
        description="Direct URL to the original joke"
    )
    scraped_date: datetime | None = Field(
        default=None,
        description="When the joke was scraped/collected"
    )
    metadata: dict | None = Field(
        default=None,
        description="Platform-specific metadata (post ID, subreddit, etc.)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "platform": "reddit",
                    "url": "https://reddit.com/r/Jokes/comments/abc123",
                    "scraped_date": "2024-01-15T10:30:00Z",
                    "metadata": {
                        "subreddit": "r/Jokes",
                        "post_id": "abc123",
                        "author": "funny_person_123"
                    }
                }
            ]
        }
    }


class Engagement(BaseModel):
    """Engagement metrics from the original platform."""

    views: int | None = Field(
        default=None,
        ge=0,
        description="Number of views (if available)"
    )
    upvotes: int | None = Field(
        default=None,
        ge=0,
        description="Number of upvotes/likes"
    )
    downvotes: int | None = Field(
        default=None,
        ge=0,
        description="Number of downvotes/dislikes"
    )
    comments: int | None = Field(
        default=None,
        ge=0,
        description="Number of comments"
    )
    shares: int | None = Field(
        default=None,
        ge=0,
        description="Number of shares/retweets"
    )
    awards: int | None = Field(
        default=None,
        ge=0,
        description="Number of awards (Reddit gold, etc.)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "views": None,
                    "upvotes": 1250,
                    "downvotes": 85,
                    "comments": 47,
                    "shares": None,
                    "awards": 3
                }
            ]
        }
    }


class JokeMetadata(BaseModel):
    """Comprehensive metadata about a joke."""

    language: str = Field(
        default="en",
        min_length=2,
        max_length=5,
        description="ISO 639-1 language code (e.g., 'en', 'es', 'fr')"
    )
    authors: list[Author] | None = Field(
        default=None,
        description="List of authors/contributors (if known)"
    )
    source: Source | None = Field(
        default=None,
        description="Information about the joke's origin"
    )
    engagement: Engagement | None = Field(
        default=None,
        description="Engagement metrics from the source platform"
    )
    created_date: datetime | None = Field(
        default=None,
        description="When the joke was originally created/posted"
    )
    added_date: datetime = Field(
        ...,
        description="When the joke was added to this dataset"
    )
    last_modified: datetime = Field(
        ...,
        description="When the joke metadata was last updated"
    )
    verified: bool = Field(
        default=False,
        description="Whether the joke has been manually verified/reviewed"
    )
    metadata: dict | None = Field(
        default=None,
        description="Additional custom metadata"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "language": "en",
                    "authors": [
                        {
                            "id": "u/funny_person_123",
                            "type": "individual",
                            "name": "funny_person_123",
                            "url": "https://reddit.com/u/funny_person_123"
                        }
                    ],
                    "source": {
                        "platform": "reddit",
                        "url": "https://reddit.com/r/Jokes/comments/abc123",
                        "scraped_date": "2024-01-15T10:30:00Z",
                        "metadata": {"subreddit": "r/Jokes", "post_id": "abc123"}
                    },
                    "engagement": {
                        "upvotes": 1250,
                        "downvotes": 85,
                        "comments": 47,
                        "awards": 3
                    },
                    "created_date": "2024-01-10T08:15:22Z",
                    "added_date": "2024-01-15T10:30:00Z",
                    "last_modified": "2024-01-15T10:30:00Z",
                    "verified": False,
                    "metadata": None
                }
            ]
        }
    }
