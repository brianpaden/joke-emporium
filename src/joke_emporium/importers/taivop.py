"""Importer for taivop/joke-dataset from GitHub.

Source: https://github.com/taivop/joke-dataset
Contains ~200k jokes from Reddit, stupidstuff.org, and wocka.com
"""

import json
import logging
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

from joke_emporium.importers.base import BaseImporter
from joke_emporium.models.author import Author, AuthorType
from joke_emporium.models.content import JokeElement
from joke_emporium.models.enums import Category, ElementType, MaturityRating, SourcePlatform, StructureType
from joke_emporium.models.flags import ContentFlags
from joke_emporium.models.joke import Joke
from joke_emporium.models.metadata import JokeMetadata, Source
from joke_emporium.models.ratings import RatingSource

logger = logging.getLogger(__name__)


class TaivopImporter(BaseImporter):
    """Import jokes from taivop/joke-dataset repository.

    Source: https://github.com/taivop/joke-dataset
    Contains ~200k jokes from Reddit, stupidstuff.org, and wocka.com

    Data format:
    - reddit_jokes.json: Jokes from Reddit r/jokes
    - stupidstuff.json: Jokes from stupidstuff.org
    - wocka.json: Jokes from wocka.com

    Each joke has format:
    {
        "id": "1",
        "type": "single" or "twoPart",
        "setup": "Why did the chicken...",  # For twoPart
        "punchline": "...",                  # For twoPart
        "body": "One liner joke",            # For single
        "score": 123,                        # Optional rating
        "category": "one-liners"             # Optional category
    }
    """

    source_name = "taivop/joke-dataset"
    source_url = "https://github.com/taivop/joke-dataset"

    # GitHub raw content base URL
    BASE_URL = "https://raw.githubusercontent.com/taivop/joke-dataset/master"

    # Files to download
    FILES = [
        "reddit_jokes.json",
        "stupidstuff.json",
        "wocka.json",
    ]

    # Category mapping from source categories to our Category enum
    CATEGORY_MAP = {
        "one-liners": Category.WORDPLAY,
        "puns": Category.WORDPLAY,
        "wordplay": Category.WORDPLAY,
        "dad": Category.WORDPLAY,
        "work": Category.WORK,
        "technology": Category.TECHNOLOGY,
        "programmer": Category.PROGRAMMER,
        "programming": Category.PROGRAMMER,
        "animals": Category.ANIMALS,
        "food": Category.FOOD,
        "politics": Category.POLITICS,
        "sports": Category.SPORTS,
        "religion": Category.RELIGION,
        "science": Category.SCIENCE,
        "math": Category.MATHEMATICS,
        "dark": Category.DARK,
        "offensive": Category.OFFENSIVE,
        "blonde": Category.BLONDE,
        "chuck norris": Category.CHUCK_NORRIS,
        "chucknorris": Category.CHUCK_NORRIS,
    }

    def download(self) -> Path:
        """Download JSON files from GitHub.

        Downloads all JSON files from the taivop/joke-dataset repository
        to the temporary directory.

        Returns:
            Path to directory containing downloaded files

        Raises:
            ImportError: If download fails
        """
        logger.info(f"Downloading files from {self.source_url}...")

        try:
            with httpx.Client(timeout=30.0) as client:
                for filename in self.FILES:
                    url = f"{self.BASE_URL}/{filename}"
                    logger.info(f"Downloading {filename} from {url}...")

                    try:
                        response = client.get(url)
                        response.raise_for_status()

                        file_path = self.source_temp_dir / filename
                        file_path.write_text(response.text, encoding="utf-8")

                        file_size = len(response.text)
                        logger.info(f"Downloaded {filename} ({file_size:,} bytes)")

                    except httpx.HTTPError as e:
                        logger.error(f"Failed to download {filename}: {e}")
                        raise ImportError(f"Failed to download {filename}: {e}") from e

            logger.info(f"Successfully downloaded all files to {self.source_temp_dir}")
            return self.source_temp_dir

        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise ImportError(f"Download failed: {e}") from e

    def parse(self, data_path: Path) -> Iterator[dict[str, Any]]:
        """Parse JSON files and yield joke dictionaries.

        Args:
            data_path: Path to directory containing JSON files

        Yields:
            Dictionary for each joke with added metadata about source file

        Raises:
            ImportError: If parsing fails
        """
        for json_file in data_path.glob("*.json"):
            logger.info(f"Parsing {json_file.name}...")

            try:
                with open(json_file, encoding="utf-8") as f:
                    jokes = json.load(f)

                if not isinstance(jokes, list):
                    logger.error(f"{json_file.name} does not contain a JSON array")
                    continue

                # Determine source platform based on filename
                if "reddit" in json_file.name.lower():
                    source_platform = SourcePlatform.REDDIT
                    source_file = "reddit_jokes"
                elif "stupidstuff" in json_file.name.lower():
                    source_platform = SourcePlatform.WEBSITE
                    source_file = "stupidstuff"
                elif "wocka" in json_file.name.lower():
                    source_platform = SourcePlatform.WEBSITE
                    source_file = "wocka"
                else:
                    source_platform = SourcePlatform.WEBSITE
                    source_file = json_file.stem

                # Add metadata to each joke
                for joke_data in jokes:
                    if isinstance(joke_data, dict):
                        joke_data["_source_file"] = source_file
                        joke_data["_source_platform"] = source_platform
                        yield joke_data
                    else:
                        logger.warning(f"Skipping non-dict entry in {json_file.name}")

                logger.info(f"Parsed {len(jokes)} jokes from {json_file.name}")

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse {json_file.name}: {e}")
                raise ImportError(f"Failed to parse {json_file.name}: {e}") from e
            except Exception as e:
                logger.error(f"Error processing {json_file.name}: {e}")
                # Don't raise, just skip this file
                continue

    def transform(self, raw_data: dict[str, Any]) -> Joke | None:
        """Transform taivop format to Joke model.

        Args:
            raw_data: Dictionary in taivop format

        Returns:
            Joke model instance, or None if transformation fails
        """
        try:
            # Generate UUID
            joke_id = str(uuid4())

            # Determine structure and build content
            content = []
            structure = None
            joke_type = raw_data.get("type", "").lower()

            if joke_type == "twopart":
                # Two-part joke (Q&A format)
                setup = raw_data.get("setup", "").strip()
                punchline = raw_data.get("delivery") or raw_data.get("punchline", "")
                punchline = punchline.strip()

                if not setup or not punchline:
                    logger.debug(f"Skipping two-part joke with missing setup/punchline: {raw_data.get('id')}")
                    return None

                content.append(JokeElement(type=ElementType.SETUP, text=setup))
                content.append(JokeElement(type=ElementType.PUNCHLINE, text=punchline))
                structure = StructureType.QA

            elif joke_type == "single":
                # One-liner
                body = raw_data.get("joke") or raw_data.get("body", "")
                body = body.strip()

                if not body:
                    logger.debug(f"Skipping single joke with missing body: {raw_data.get('id')}")
                    return None

                content.append(JokeElement(type=ElementType.TEXT, text=body))
                structure = StructureType.ONE_LINER

            else:
                # Unknown type, try to infer
                if "setup" in raw_data and ("punchline" in raw_data or "delivery" in raw_data):
                    setup = raw_data.get("setup", "").strip()
                    punchline = raw_data.get("delivery") or raw_data.get("punchline", "")
                    punchline = punchline.strip()

                    if setup and punchline:
                        content.append(JokeElement(type=ElementType.SETUP, text=setup))
                        content.append(JokeElement(type=ElementType.PUNCHLINE, text=punchline))
                        structure = StructureType.QA
                elif "joke" in raw_data or "body" in raw_data:
                    body = raw_data.get("joke") or raw_data.get("body", "")
                    body = body.strip()

                    if body:
                        content.append(JokeElement(type=ElementType.TEXT, text=body))
                        structure = StructureType.ONE_LINER

            # No valid content found
            if not content:
                logger.debug(f"No valid content found for joke: {raw_data.get('id')}")
                return None

            # Map categories
            categories = []
            tags = []
            category_raw = raw_data.get("category", "").lower().strip()

            if category_raw:
                # Try to map to known category
                if category_raw in self.CATEGORY_MAP:
                    categories.append(self.CATEGORY_MAP[category_raw])
                else:
                    # Category not in map, add as tag instead
                    tags.append(category_raw)

            # Map ratings
            ratings = []
            score = raw_data.get("score")
            if score is not None:
                try:
                    score_float = float(score)
                    # Reddit scores can be very large, use the score as both min and max
                    # to indicate this is an absolute value, not a scale
                    # Alternatively, we could use a large max_rating like 100000
                    max_score = max(score_float, 10000)  # Use at least 10000 as max
                    ratings.append(
                        RatingSource(
                            source="reddit_score" if raw_data.get("_source_platform") == SourcePlatform.REDDIT else "source_score",
                            min_rating=0.0,
                            max_rating=max_score,
                            total_ratings=1,
                            avg_funniness=score_float,
                        )
                    )
                except (ValueError, TypeError) as e:
                    logger.debug(f"Invalid score value: {score}, error: {e}")

            # Determine maturity rating
            maturity = MaturityRating.G  # Default to G-rated
            safe = raw_data.get("safe", True)
            nsfw = raw_data.get("nsfw", False)

            if not safe or nsfw:
                maturity = MaturityRating.R

            # Build content flags
            flags = ContentFlags()
            if not safe or nsfw:
                flags.offensive = True

            # Check for specific flag fields
            if raw_data.get("explicit", False):
                flags.sexual = True
                maturity = MaturityRating.X
            if raw_data.get("political", False):
                flags.political = True
            if raw_data.get("religious", False):
                flags.religious = True
            if raw_data.get("racist", False):
                flags.offensive = True
                flags.stereotypical = True
            if raw_data.get("sexist", False):
                flags.offensive = True
                flags.stereotypical = True

            # Build metadata
            source_platform = raw_data.get("_source_platform", SourcePlatform.WEBSITE)
            source_file = raw_data.get("_source_file", "unknown")

            metadata = JokeMetadata(
                language=raw_data.get("lang", "en"),
                authors=[Author(id="unknown", type=AuthorType.ANONYMOUS, name="Anonymous")],
                source=Source(
                    platform=source_platform,
                    url=None,
                    scraped_date=None,
                    metadata={
                        "source_id": str(raw_data.get("id", "")),
                        "source_file": source_file,
                    },
                ),
                added_date=datetime.now(timezone.utc),
                last_modified=datetime.now(timezone.utc),
                verified=False,
            )

            # Create joke
            joke = Joke(
                id=joke_id,
                content=content,
                categories=categories,
                structure=structure,
                maturity_rating=maturity,
                tags=tags,
                flags=flags,
                ratings=ratings,
                metadata=metadata,
            )

            return joke

        except Exception as e:
            # Log error and return None
            logger.warning(f"Error transforming joke {raw_data.get('id', 'unknown')}: {e}")
            return None

    def validate(self, joke: Joke) -> tuple[bool, list[str]]:
        """Validate taivop joke with source-specific rules.

        Args:
            joke: Joke to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        # Call base validation
        is_valid, errors = super().validate(joke)

        # Minimum text length
        total_length = sum(len(elem.text) for elem in joke.content)
        if total_length < 5:
            is_valid = False
            errors.append(f"Joke too short: {total_length} chars (minimum 5)")

        # Check for placeholder/test jokes
        combined_text = " ".join(elem.text.lower() for elem in joke.content)
        if "test" in combined_text and len(combined_text) < 20:
            is_valid = False
            errors.append("Appears to be a test joke")

        # Validate two-part jokes have exactly 2 elements
        if joke.structure == StructureType.QA:
            if len(joke.content) != 2:
                is_valid = False
                errors.append(f"Q&A joke should have exactly 2 elements, has {len(joke.content)}")

        # Validate one-liner has exactly 1 element
        if joke.structure == StructureType.ONE_LINER:
            if len(joke.content) != 1:
                is_valid = False
                errors.append(f"One-liner should have exactly 1 element, has {len(joke.content)}")

        return (is_valid, errors)
