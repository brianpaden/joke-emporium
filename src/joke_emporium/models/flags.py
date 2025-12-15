"""Content flag models for joke categorization."""

from pydantic import BaseModel, Field


class ContentFlags(BaseModel):
    """Boolean flags for content warnings and categorization.

    These flags help with filtering and content warnings.
    They complement the maturity rating system.
    """

    profanity: bool = Field(default=False, description="Contains profanity or strong language")
    dark_humor: bool = Field(default=False, description="Contains dark, morbid, or gallows humor")
    offensive: bool = Field(default=False, description="May be offensive to some audiences")
    political: bool = Field(default=False, description="Contains political content or satire")
    sexual: bool = Field(default=False, description="Contains sexual content or innuendo")
    violent: bool = Field(default=False, description="Contains violent or graphic content")
    stereotypical: bool = Field(
        default=False, description="Uses stereotypes or potentially insensitive characterizations"
    )
    religious: bool = Field(default=False, description="Contains religious content or themes")
    requires_context: bool = Field(default=False, description="Requires specific cultural or contextual knowledge")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
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
                {
                    "profanity": True,
                    "dark_humor": True,
                    "offensive": False,
                    "political": False,
                    "sexual": False,
                    "violent": False,
                    "stereotypical": False,
                    "religious": False,
                    "requires_context": False,
                },
            ]
        }
    }
