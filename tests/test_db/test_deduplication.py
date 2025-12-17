"""Tests for deduplication logic."""

import unittest

from joke_emporium.db.deduplication import normalize_text


class TestNormalization(unittest.TestCase):
    """Test text normalization functionality."""

    def test_normalize_text_basic(self):
        """Test basic text normalization."""
        self.assertEqual(
            normalize_text("  Hello World  "),
            "hello world"
        )

    def test_normalize_text_casefold(self):
        """Test casefolding."""
        self.assertEqual(
            normalize_text("HELLO world"),
            "hello world"
        )

    def test_normalize_text_extra_spaces(self):
        """Test multiple spaces normalization."""
        text = "Hello    World"
        normalized = normalize_text(text)
        self.assertEqual(normalized, "hello world")

    def test_normalize_text_unicode(self):
        """Test unicode normalization."""
        # Test that unicode is normalized properly
        text1 = "café"  # é as single character
        text2 = "café"  # é as e + combining accent
        self.assertEqual(normalize_text(text1), normalize_text(text2))

    def test_normalize_text_ellipsis(self):
        """Test ellipsis preservation."""
        text = "Wait for it..."
        normalized = normalize_text(text)
        self.assertIn("...", normalized)

    def test_normalize_text_punctuation(self):
        """Test punctuation removal."""
        text = "Hello, World!"
        normalized = normalize_text(text)
        self.assertEqual(normalized, "hello world")

    def test_normalize_text_apostrophes(self):
        """Test apostrophe preservation in contractions."""
        text = "Don't you think it's great?"
        normalized = normalize_text(text)
        self.assertIn("don't", normalized)
        self.assertIn("it's", normalized)

    def test_normalize_text_line_breaks(self):
        """Test line break normalization."""
        text = "Line 1\r\nLine 2\rLine 3\nLine 4"
        normalized = normalize_text(text)
        # Should normalize all line breaks to spaces
        self.assertIn("line 1", normalized)
        self.assertIn("line 2", normalized)

    def test_normalize_identical_jokes(self):
        """Test that identical jokes normalize to same text."""
        joke1 = "Why did the chicken cross the road?"
        joke2 = "WHY DID THE CHICKEN CROSS THE ROAD?"
        self.assertEqual(normalize_text(joke1), normalize_text(joke2))

    def test_normalize_similar_jokes(self):
        """Test that similar jokes with different punctuation normalize similarly."""
        joke1 = "Hello, world!"
        joke2 = "Hello world"
        self.assertEqual(normalize_text(joke1), normalize_text(joke2))


if __name__ == "__main__":
    unittest.main()
