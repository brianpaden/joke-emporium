"""Author database model."""

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from joke_emporium.models.enums import AuthorType

if TYPE_CHECKING:
    from joke_emporium.db.models.associations import JokeAuthorLink
    from joke_emporium.models.author import Author


class AuthorDB(SQLModel, table=True):
    """Author database model.

    Stores author/persona information with relationships to jokes.
    """

    __tablename__ = "authors"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Author identification
    author_id: str = Field(
        index=True,
        unique=True,
        max_length=255,
        description="Unique author identifier (UUID, username, etc.)",
    )
    type: str = Field(max_length=50, description="Author type from AuthorType enum")

    # Author information
    name: str | None = Field(default=None, max_length=255, description="Display name")
    real_name: str | None = Field(default=None, max_length=255, description="Real name")
    bio: str | None = Field(default=None, description="Biography")
    url: str | None = Field(default=None, max_length=500, description="Profile URL")

    # Metadata (stored as JSON)
    metadata_json: str | None = Field(default=None, sa_column_kwargs={"name": "metadata"})

    # Relationships
    joke_links: list["JokeAuthorLink"] = Relationship(back_populates="author")

    @classmethod
    def from_pydantic(cls, author: "Author") -> "AuthorDB":
        """Convert from Pydantic Author model to database model."""
        import json

        return cls(
            author_id=author.id,
            type=author.type.value,
            name=author.name,
            real_name=author.real_name,
            bio=author.bio,
            url=author.url,
            metadata_json=json.dumps(author.metadata) if author.metadata else None,
        )

    def to_pydantic(self) -> "Author":
        """Convert to Pydantic Author model."""
        import json

        from joke_emporium.models.author import Author

        return Author(
            id=self.author_id,
            type=AuthorType(self.type),
            name=self.name,
            real_name=self.real_name,
            bio=self.bio,
            url=self.url,
            metadata=json.loads(self.metadata_json) if self.metadata_json else None,
        )
