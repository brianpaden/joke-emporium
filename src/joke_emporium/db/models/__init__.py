"""SQLModel database models."""

from joke_emporium.db.models.associations import (
    JokeAuthorLink,
    JokeCategoryLink,
    JokeLinguisticMechanismLink,
)
from joke_emporium.db.models.author import AuthorDB
from joke_emporium.db.models.joke import JokeDB
from joke_emporium.db.models.rating import RatingSourceDB, VoteDB
from joke_emporium.db.models.staging import ImportBatchDB, StagingJokeDB

__all__ = [
    # Association tables
    "JokeAuthorLink",
    "JokeCategoryLink",
    "JokeLinguisticMechanismLink",
    # Models
    "AuthorDB",
    "JokeDB",
    "RatingSourceDB",
    "VoteDB",
    # Staging models
    "ImportBatchDB",
    "StagingJokeDB",
]
