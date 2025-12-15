"""
Joke Emporium - A categorized dataset of jokes with rich metadata.

Python 3.10+ | Pydantic models | SQLite support
"""

__version__ = "0.1.0"

from joke_emporium.models.author import Author
from joke_emporium.models.collection import Collection
from joke_emporium.models.joke import Joke

__all__ = ["Joke", "Author", "Collection", "__version__"]
