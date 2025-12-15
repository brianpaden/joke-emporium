"""Author and persona models."""

from pydantic import BaseModel, Field

from joke_emporium.models.enums import AuthorType


class Author(BaseModel):
    """Represents a joke author or persona.

    Can represent:
    - Professional comedians
    - Anonymous contributors
    - Reddit users
    - Groups/collectives
    - Unknown sources
    """

    id: str = Field(..., description="Unique identifier for this author (UUID, username, etc.)")
    type: AuthorType = Field(..., description="Type of author (individual, group, anonymous, unknown)")
    name: str | None = Field(default=None, description="Display name of the author")
    real_name: str | None = Field(default=None, description="Real name (if known and different from display name)")
    bio: str | None = Field(default=None, description="Brief biography or description")
    url: str | None = Field(default=None, description="Author's website, social media, or profile URL")
    metadata: dict | None = Field(default=None, description="Additional platform-specific or custom metadata")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "u/funny_person_123",
                    "type": "individual",
                    "name": "funny_person_123",
                    "real_name": None,
                    "bio": None,
                    "url": "https://reddit.com/u/funny_person_123",
                    "metadata": {"platform": "reddit", "karma": 15234},
                },
                {
                    "id": "mitch-hedberg",
                    "type": "individual",
                    "name": "Mitch Hedberg",
                    "real_name": "Mitchell Lee Hedberg",
                    "bio": "American stand-up comedian known for surreal humor and deadpan delivery",
                    "url": "https://en.wikipedia.org/wiki/Mitch_Hedberg",
                    "metadata": {"born": "1968-02-24", "died": "2005-03-29"},
                },
                {
                    "id": "anonymous",
                    "type": "anonymous",
                    "name": "Anonymous",
                    "real_name": None,
                    "bio": None,
                    "url": None,
                    "metadata": None,
                },
            ]
        }
    }
