"""Association tables for many-to-many relationships."""

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from joke_emporium.db.models.author import AuthorDB
    from joke_emporium.db.models.joke import JokeDB


class JokeAuthorLink(SQLModel, table=True):
    """Many-to-many relationship between jokes and authors."""

    __tablename__ = "joke_author_link"

    joke_id: int = Field(foreign_key="jokes.id", primary_key=True)
    author_id: int = Field(foreign_key="authors.id", primary_key=True)

    # Relationships
    joke: "JokeDB" = Relationship(back_populates="author_links")
    author: "AuthorDB" = Relationship(back_populates="joke_links")


class JokeCategoryLink(SQLModel, table=True):
    """Many-to-many relationship between jokes and categories."""

    __tablename__ = "joke_category_link"

    joke_id: int = Field(foreign_key="jokes.id", primary_key=True)
    category: str = Field(primary_key=True, max_length=50)  # Category enum value

    # Relationship
    joke: "JokeDB" = Relationship(back_populates="category_links")


class JokeLinguisticMechanismLink(SQLModel, table=True):
    """Many-to-many relationship between jokes and linguistic mechanisms."""

    __tablename__ = "joke_linguistic_mechanism_link"

    joke_id: int = Field(foreign_key="jokes.id", primary_key=True)
    mechanism: str = Field(primary_key=True, max_length=50)  # LinguisticMechanism enum value

    # Relationship
    joke: "JokeDB" = Relationship(back_populates="mechanism_links")
