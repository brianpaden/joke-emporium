"""Pydantic models for joke dataset."""

from joke_emporium.models.author import Author
from joke_emporium.models.collection import Collection
from joke_emporium.models.content import JokeElement
from joke_emporium.models.enums import (
    AgeRange,
    AuthorType,
    Category,
    CognitiveType,
    ElementType,
    LinguisticMechanism,
    LogicalMechanism,
    MaturityRating,
    NarrativeStrategy,
    OppositionType,
    SourcePlatform,
    StructureType,
    TargetType,
)
from joke_emporium.models.flags import ContentFlags
from joke_emporium.models.gtvh import GTVHAnnotation, ScriptOpposition, Target
from joke_emporium.models.joke import Joke
from joke_emporium.models.metadata import Engagement, JokeMetadata, Source
from joke_emporium.models.ratings import RatingSource, Vote

__all__ = [
    # Enums
    "Category",
    "StructureType",
    "LinguisticMechanism",
    "MaturityRating",
    "ElementType",
    "CognitiveType",
    "SourcePlatform",
    "OppositionType",
    "LogicalMechanism",
    "NarrativeStrategy",
    "TargetType",
    "AuthorType",
    "AgeRange",
    # Content
    "JokeElement",
    # Ratings
    "Vote",
    "RatingSource",
    # Metadata
    "Source",
    "Engagement",
    "JokeMetadata",
    # Flags
    "ContentFlags",
    # Author
    "Author",
    # GTVH
    "ScriptOpposition",
    "Target",
    "GTVHAnnotation",
    # Main models
    "Joke",
    "Collection",
]
