"""Example importer implementation.

This file demonstrates how to create a new importer by extending BaseImporter.
Copy this file and modify it for your specific data source.

This is a working example that imports from a simple JSON file format.
"""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from uuid import uuid4

from joke_emporium.importers.base import BaseImporter
from joke_emporium.models.author import Author, AuthorType
from joke_emporium.models.content import JokeElement
from joke_emporium.models.enums import Category, ElementType, MaturityRating, SourcePlatform, StructureType
from joke_emporium.models.flags import ContentFlags
from joke_emporium.models.joke import Joke
from joke_emporium.models.metadata import JokeMetadata, Source
from joke_emporium.models.ratings import RatingSource


class ExampleImporter(BaseImporter):
    """Example importer for demonstration purposes.

    This importer reads jokes from a simple JSON file format:

    [
        {
            "id": "1",
            "text": "Why did the chicken cross the road?",
            "setup": "Why did the chicken cross the road?",
            "punchline": "To get to the other side!",
            "category": "classic",
            "rating": 4.5
        },
        ...
    ]

    To use this importer:
    1. Copy this file to a new name (e.g., taivop.py)
    2. Update source_name and source_url
    3. Implement download() to fetch your data
    4. Implement parse() to extract jokes from your format
    5. Implement transform() to convert to Joke model
    6. Optionally override validate() for custom validation
    """

    source_name = "example-jokes"
    source_url = "https://example.com/jokes"

    def download(self) -> Path:
        """Download source data to temporary location.

        For this example, we'll just create a sample file.
        In a real importer, you would:
        - Use httpx to download files
        - Clone git repositories
        - Call APIs
        - etc.

        Returns:
            Path to downloaded data file
        """
        # Create sample data
        sample_data = [
            {
                "id": "1",
                "setup": "Why did the programmer quit?",
                "punchline": "Because they didn't get arrays!",
                "category": "programmer",
                "rating": 3.5,
            },
            {
                "id": "2",
                "text": "I told my wife she was drawing her eyebrows too high. She looked surprised.",
                "category": "oneliners",
                "rating": 4.0,
            },
        ]

        # Write to temp file
        data_file = self.source_temp_dir / "example_jokes.json"
        with open(data_file, "w") as f:
            json.dump(sample_data, f, indent=2)

        return data_file

    def parse(self, data_path: Path) -> Iterator[dict[str, Any]]:
        """Parse downloaded data into raw dictionaries.

        Args:
            data_path: Path to downloaded data

        Yields:
            Dictionary for each joke in source format
        """
        with open(data_path) as f:
            data = json.load(f)

        for joke_data in data:
            yield joke_data

    def transform(self, raw_data: dict[str, Any]) -> Joke | None:
        """Transform raw data to Joke model.

        Args:
            raw_data: Dictionary in source format

        Returns:
            Joke model instance, or None if transformation fails
        """
        from datetime import datetime, timezone

        try:
            # Generate UUID
            joke_id = str(uuid4())

            # Determine structure and build content
            content = []
            structure = None

            if "setup" in raw_data and "punchline" in raw_data:
                # Two-part joke (Q&A format)
                content.append(JokeElement(type=ElementType.SETUP, text=raw_data["setup"]))
                content.append(JokeElement(type=ElementType.PUNCHLINE, text=raw_data["punchline"]))
                structure = StructureType.QA
            elif "text" in raw_data:
                # One-liner
                content.append(JokeElement(type=ElementType.TEXT, text=raw_data["text"]))
                structure = StructureType.ONE_LINER
            else:
                # No valid content
                return None

            # Map category
            categories = []
            if cat := raw_data.get("category"):
                try:
                    # Try to map to known category
                    categories.append(Category(cat.lower()))
                except ValueError:
                    # Category not in enum, will add as tag instead
                    pass

            # Map rating
            ratings = []
            if rating := raw_data.get("rating"):
                ratings.append(
                    RatingSource(
                        source="example_rating",
                        min_rating=1.0,
                        max_rating=5.0,
                        total_ratings=1,
                        avg_funniness=float(rating),
                    )
                )

            # Build metadata
            metadata = JokeMetadata(
                language="en",
                authors=[Author(id="unknown", type=AuthorType.ANONYMOUS, name="Anonymous")],
                source=Source(
                    platform=SourcePlatform.WEBSITE,
                    url=None,
                    scraped_date=None,
                    metadata={"source_id": raw_data.get("id")},
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
                maturity_rating=MaturityRating.G,  # Default to G-rated
                tags=[raw_data.get("category")] if raw_data.get("category") else [],
                flags=ContentFlags(),  # All flags default to False
                ratings=ratings,
                metadata=metadata,
            )

            return joke

        except Exception as e:
            # Log error and return None
            # The framework will count this as a failed import
            print(f"Error transforming joke {raw_data.get('id', 'unknown')}: {e}")
            return None

    def validate(self, joke: Joke) -> tuple[bool, list[str]]:
        """Validate a joke (optional override).

        The base class provides basic validation.
        Override this method to add source-specific validation rules.

        Args:
            joke: Joke to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        # Call base validation
        is_valid, errors = super().validate(joke)

        # Add custom validation rules
        if joke.structure == StructureType.QA:
            # Q&A jokes should have exactly 2 elements
            if len(joke.content) != 2:
                is_valid = False
                errors.append("Q&A joke should have exactly 2 elements (setup and punchline)")

        # Check minimum text length
        total_length = sum(len(elem.text) for elem in joke.content)
        if total_length < 10:
            is_valid = False
            errors.append(f"Joke text too short ({total_length} chars, minimum 10)")

        return (is_valid, errors)


# Example usage (for testing)
if __name__ == "__main__":
    import logging

    from joke_emporium.db.staging import get_staging_session, init_staging_db

    # Enable logging
    logging.basicConfig(level=logging.INFO)

    # Initialize staging database
    init_staging_db()

    # Create importer
    importer = ExampleImporter()

    try:
        # Run import
        with next(get_staging_session()) as session:
            metadata = importer.import_to_staging(session=session, validate=True, max_records=10)

            print("\n" + "=" * 60)
            print("Import Complete!")
            print("=" * 60)
            print(f"Import ID: {metadata.import_id}")
            print(f"Total: {metadata.total_records}")
            print(f"Successful: {metadata.successful}")
            print(f"Failed: {metadata.failed}")

    finally:
        # Cleanup temp files
        importer.cleanup()
