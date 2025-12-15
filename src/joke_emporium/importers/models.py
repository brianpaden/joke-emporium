"""Import-specific data models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ValidationStatus(str, Enum):
    """Validation status for imported data."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ImportMetadata(BaseModel):
    """Metadata for an import batch.

    Tracks information about a data import operation including source,
    timing, and success/failure counts.
    """

    import_id: str = Field(..., description="UUID for this import batch")
    source: str = Field(..., description="Source identifier (e.g., 'taivop/joke-dataset')")
    source_version: str | None = Field(default=None, description="Git commit hash or version")
    imported_at: datetime = Field(..., description="When the import was performed")
    total_records: int = Field(default=0, ge=0, description="Total records processed")
    successful: int = Field(default=0, ge=0, description="Successfully imported records")
    failed: int = Field(default=0, ge=0, description="Failed records")
    validation_status: ValidationStatus = Field(
        default=ValidationStatus.PENDING, description="Overall validation status"
    )
    notes: str | None = Field(default=None, description="Additional notes or errors")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "import_id": "550e8400-e29b-41d4-a716-446655440000",
                    "source": "taivop/joke-dataset",
                    "source_version": "abc123def",
                    "imported_at": "2024-01-15T10:30:00Z",
                    "total_records": 1000,
                    "successful": 950,
                    "failed": 50,
                    "validation_status": "pending",
                    "notes": "Import completed with 50 validation errors",
                }
            ]
        }
    }


class ImportProgress(BaseModel):
    """Progress information for ongoing import."""

    total: int = Field(default=0, description="Total items to process")
    processed: int = Field(default=0, description="Items processed so far")
    successful: int = Field(default=0, description="Successfully processed items")
    failed: int = Field(default=0, description="Failed items")
    current_item: str | None = Field(default=None, description="Current item being processed")

    @property
    def percent_complete(self) -> float:
        """Calculate percentage complete."""
        if self.total == 0:
            return 0.0
        return (self.processed / self.total) * 100.0


class ValidationResult(BaseModel):
    """Result of validating a single item."""

    is_valid: bool = Field(..., description="Whether the item is valid")
    errors: list[str] = Field(default_factory=list, description="Validation errors")
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")

    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
