"""Unit tests for importer models."""

import unittest
from datetime import UTC, datetime

from joke_emporium.importers.models import (
    ImportMetadata,
    ImportProgress,
    ValidationResult,
    ValidationStatus,
)


class TestValidationStatus(unittest.TestCase):
    """Tests for ValidationStatus enum."""

    def test_validation_status_values(self):
        """Test that ValidationStatus has expected values."""
        self.assertEqual(ValidationStatus.PENDING.value, "pending")
        self.assertEqual(ValidationStatus.APPROVED.value, "approved")
        self.assertEqual(ValidationStatus.REJECTED.value, "rejected")


class TestImportMetadata(unittest.TestCase):
    """Tests for ImportMetadata model."""

    def test_create_valid_metadata(self):
        """Test creating valid ImportMetadata."""
        now = datetime.now(UTC)

        metadata = ImportMetadata(
            import_id="test-import-123",
            source="test-source",
            imported_at=now,
            total_records=100,
            successful=90,
            failed=10,
        )

        self.assertEqual(metadata.import_id, "test-import-123")
        self.assertEqual(metadata.source, "test-source")
        self.assertEqual(metadata.total_records, 100)
        self.assertEqual(metadata.successful, 90)
        self.assertEqual(metadata.failed, 10)
        self.assertEqual(metadata.validation_status, ValidationStatus.PENDING)

    def test_metadata_with_optional_fields(self):
        """Test ImportMetadata with optional fields."""
        now = datetime.now(UTC)

        metadata = ImportMetadata(
            import_id="test-import-456",
            source="test-source",
            source_version="v1.0.0",
            imported_at=now,
            total_records=50,
            successful=45,
            failed=5,
            validation_status=ValidationStatus.APPROVED,
            notes="Import completed successfully",
        )

        self.assertEqual(metadata.source_version, "v1.0.0")
        self.assertEqual(metadata.validation_status, ValidationStatus.APPROVED)
        self.assertEqual(metadata.notes, "Import completed successfully")


class TestImportProgress(unittest.TestCase):
    """Tests for ImportProgress model."""

    def test_create_empty_progress(self):
        """Test creating empty ImportProgress."""
        progress = ImportProgress()

        self.assertEqual(progress.total, 0)
        self.assertEqual(progress.processed, 0)
        self.assertEqual(progress.successful, 0)
        self.assertEqual(progress.failed, 0)
        self.assertIsNone(progress.current_item)

    def test_percent_complete_zero_total(self):
        """Test percent_complete returns 0 when total is 0."""
        progress = ImportProgress(total=0, processed=0)
        self.assertEqual(progress.percent_complete, 0.0)

    def test_percent_complete_calculation(self):
        """Test percent_complete calculation."""
        progress = ImportProgress(total=100, processed=50)
        self.assertEqual(progress.percent_complete, 50.0)

        progress.processed = 75
        self.assertEqual(progress.percent_complete, 75.0)

        progress.processed = 100
        self.assertEqual(progress.percent_complete, 100.0)

    def test_progress_tracking(self):
        """Test tracking progress through import."""
        progress = ImportProgress(total=10)

        self.assertEqual(progress.processed, 0)
        self.assertEqual(progress.percent_complete, 0.0)

        progress.processed = 5
        progress.successful = 4
        progress.failed = 1

        self.assertEqual(progress.percent_complete, 50.0)
        self.assertEqual(progress.successful, 4)
        self.assertEqual(progress.failed, 1)


class TestValidationResult(unittest.TestCase):
    """Tests for ValidationResult model."""

    def test_create_valid_result(self):
        """Test creating valid ValidationResult."""
        result = ValidationResult(is_valid=True)

        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.warnings), 0)
        self.assertFalse(result.has_errors)
        self.assertFalse(result.has_warnings)

    def test_create_invalid_result_with_errors(self):
        """Test creating invalid ValidationResult with errors."""
        result = ValidationResult(is_valid=False, errors=["Error 1", "Error 2"], warnings=["Warning 1"])

        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 2)
        self.assertEqual(len(result.warnings), 1)
        self.assertTrue(result.has_errors)
        self.assertTrue(result.has_warnings)

    def test_has_errors_property(self):
        """Test has_errors property."""
        result_no_errors = ValidationResult(is_valid=True)
        self.assertFalse(result_no_errors.has_errors)

        result_with_errors = ValidationResult(is_valid=False, errors=["Error"])
        self.assertTrue(result_with_errors.has_errors)

    def test_has_warnings_property(self):
        """Test has_warnings property."""
        result_no_warnings = ValidationResult(is_valid=True)
        self.assertFalse(result_no_warnings.has_warnings)

        result_with_warnings = ValidationResult(is_valid=True, warnings=["Warning"])
        self.assertTrue(result_with_warnings.has_warnings)
