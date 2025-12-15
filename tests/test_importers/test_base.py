"""Unit tests for base importer class."""

import unittest
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from joke_emporium.importers.base import BaseImporter
from joke_emporium.models.author import Author, AuthorType
from joke_emporium.models.content import JokeElement
from joke_emporium.models.enums import ElementType
from joke_emporium.models.joke import Joke
from joke_emporium.models.metadata import JokeMetadata


class MockImporter(BaseImporter):
    """Mock importer for testing BaseImporter."""

    source_name = "mock-source"
    source_url = "https://example.com/mock"

    def __init__(self, temp_dir: Path | None = None):
        """Initialize mock importer."""
        super().__init__(temp_dir)
        self.downloaded = False
        self.mock_data = []

    def download(self) -> Path:
        """Mock download method."""
        self.downloaded = True
        mock_file = self.source_temp_dir / "mock_data.txt"
        mock_file.write_text("mock data")
        return mock_file

    def parse(self, data_path: Path) -> Iterator[dict[str, Any]]:
        """Mock parse method."""
        for item in self.mock_data:
            yield item

    def transform(self, raw_data: dict[str, Any]) -> Joke | None:
        """Mock transform method."""
        from datetime import datetime, timezone

        if "fail" in raw_data:
            return None

        return Joke(
            id=f"test-{raw_data.get('id', 'unknown')}",
            content=[
                JokeElement(type=ElementType.TEXT, text=raw_data.get("text", "Test joke"))
            ],
            metadata=JokeMetadata(
                language="en",
                authors=[Author(id="test", type=AuthorType.ANONYMOUS, name="Test")],
                added_date=datetime.now(timezone.utc),
                last_modified=datetime.now(timezone.utc),
                verified=False,
            ),
        )


class TestBaseImporter(unittest.TestCase):
    """Tests for BaseImporter class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path("temp/test_imports")
        self.importer = MockImporter(temp_dir=self.temp_dir)

    def tearDown(self):
        """Clean up test files."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test importer initialization."""
        self.assertEqual(self.importer.source_name, "mock-source")
        self.assertEqual(self.importer.source_url, "https://example.com/mock")
        self.assertTrue(self.importer.temp_dir.exists())
        self.assertTrue(self.importer.source_temp_dir.exists())

    def test_initialization_without_source_name(self):
        """Test that initialization fails without source_name."""

        class InvalidImporter(BaseImporter):
            source_name = ""

            def download(self) -> Path:
                pass

            def parse(self, data_path: Path) -> Iterator[dict[str, Any]]:
                pass

            def transform(self, raw_data: dict[str, Any]) -> Joke | None:
                pass

        with self.assertRaises(ValueError):
            InvalidImporter()

    def test_validate_valid_joke(self):
        """Test validation of valid joke."""
        from datetime import datetime, timezone

        joke = Joke(
            id="test-123",
            content=[JokeElement(type=ElementType.TEXT, text="This is a test joke")],
            metadata=JokeMetadata(
                language="en",
                authors=[Author(id="test", type=AuthorType.ANONYMOUS, name="Test")],
                added_date=datetime.now(timezone.utc),
                last_modified=datetime.now(timezone.utc),
                verified=False,
            ),
        )

        is_valid, errors = self.importer.validate(joke)

        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_validate_joke_with_no_content(self):
        """Test validation catches empty content in validate method."""
        from datetime import datetime, timezone

        # Create a joke with content, then manually set it to empty for testing
        # (Pydantic won't allow empty content in __init__)
        joke = Joke(
            id="test-456",
            content=[JokeElement(type=ElementType.TEXT, text="temp")],
            metadata=JokeMetadata(
                language="en",
                authors=[Author(id="test", type=AuthorType.ANONYMOUS, name="Test")],
                added_date=datetime.now(timezone.utc),
                last_modified=datetime.now(timezone.utc),
                verified=False,
            ),
        )

        # Manually set content to empty to test validation
        joke.content = []

        is_valid, errors = self.importer.validate(joke)

        self.assertFalse(is_valid)
        self.assertIn("Joke has no content", errors)

    def test_validate_joke_with_empty_text(self):
        """Test validation fails for joke with empty text."""
        from datetime import datetime, timezone

        joke = Joke(
            id="test-789",
            content=[JokeElement(type=ElementType.TEXT, text="   ")],  # Whitespace only
            metadata=JokeMetadata(
                language="en",
                authors=[Author(id="test", type=AuthorType.ANONYMOUS, name="Test")],
                added_date=datetime.now(timezone.utc),
                last_modified=datetime.now(timezone.utc),
                verified=False,
            ),
        )

        is_valid, errors = self.importer.validate(joke)

        self.assertFalse(is_valid)
        self.assertTrue(any("Empty text" in error for error in errors))

    def test_cleanup(self):
        """Test cleanup removes temporary directory."""
        # Ensure directory exists
        self.assertTrue(self.importer.source_temp_dir.exists())

        # Cleanup
        self.importer.cleanup()

        # Directory should be removed
        self.assertFalse(self.importer.source_temp_dir.exists())

    def test_download_creates_file(self):
        """Test download method creates file."""
        result_path = self.importer.download()

        self.assertTrue(result_path.exists())
        self.assertTrue(self.importer.downloaded)
        self.assertEqual(result_path.read_text(), "mock data")

    def test_parse_yields_data(self):
        """Test parse method yields data."""
        self.importer.mock_data = [{"id": "1", "text": "Joke 1"}, {"id": "2", "text": "Joke 2"}]

        data_path = Path("dummy")  # Not used in mock
        results = list(self.importer.parse(data_path))

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["id"], "1")
        self.assertEqual(results[1]["id"], "2")

    def test_transform_creates_joke(self):
        """Test transform method creates Joke."""
        raw_data = {"id": "123", "text": "Test joke"}

        joke = self.importer.transform(raw_data)

        self.assertIsNotNone(joke)
        self.assertEqual(joke.id, "test-123")
        self.assertEqual(joke.content[0].text, "Test joke")

    def test_transform_returns_none_on_failure(self):
        """Test transform returns None on failure."""
        raw_data = {"fail": True}

        joke = self.importer.transform(raw_data)

        self.assertIsNone(joke)


class TestBaseImporterEdgeCases(unittest.TestCase):
    """Edge case tests for BaseImporter."""

    def test_temp_dir_creation_with_slash_in_name(self):
        """Test that source names with slashes create valid directories."""
        temp_dir = Path("temp/test_edge")

        class SlashImporter(MockImporter):
            source_name = "github/repo-name"

        importer = SlashImporter(temp_dir=temp_dir)

        # Should replace / with _
        self.assertTrue(importer.source_temp_dir.exists())
        self.assertIn("github_repo-name", str(importer.source_temp_dir))

        # Cleanup
        import shutil

        if temp_dir.exists():
            shutil.rmtree(temp_dir)
