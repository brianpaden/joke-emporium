"""Base importer class for all data sources."""

import logging
from abc import ABC, abstractmethod
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlmodel import Session

from joke_emporium.importers.models import ImportMetadata, ImportProgress, ValidationStatus
from joke_emporium.models.joke import Joke

logger = logging.getLogger(__name__)


class BaseImporter(ABC):
    """Base class for all data source importers.

    This abstract class defines the interface that all importers must implement.
    It provides a common pipeline for downloading, parsing, transforming, and
    importing joke data from various sources.

    Subclasses must implement:
    - download(): Download source data to temp location
    - parse(): Parse raw data into dict format
    - transform(): Transform raw data to Joke model
    """

    # Subclasses must override these
    source_name: str = ""
    source_url: str = ""

    def __init__(self, temp_dir: Path | None = None):
        """Initialize the importer.

        Args:
            temp_dir: Directory for temporary downloads. Defaults to temp/imports/
        """
        if not self.source_name:
            raise ValueError("Subclasses must define source_name")

        self.temp_dir = temp_dir or Path("temp/imports")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Create source-specific temp directory
        self.source_temp_dir = self.temp_dir / self.source_name.replace("/", "_")
        self.source_temp_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def download(self) -> Path:
        """Download source data to temporary location.

        Returns:
            Path to downloaded data (file or directory)

        Raises:
            ImportError: If download fails
        """
        pass

    @abstractmethod
    def parse(self, data_path: Path) -> Iterator[dict[str, Any]]:
        """Parse raw data into dictionary format.

        Args:
            data_path: Path to downloaded data

        Yields:
            Dictionary representing one joke in source format

        Raises:
            ImportError: If parsing fails
        """
        pass

    @abstractmethod
    def transform(self, raw_data: dict[str, Any]) -> Joke | None:
        """Transform raw data dictionary to Joke model.

        Args:
            raw_data: Dictionary in source format

        Returns:
            Joke model instance, or None if transformation fails

        Note:
            Should handle transformation errors gracefully and return None
            rather than raising exceptions.
        """
        pass

    def validate(self, joke: Joke) -> tuple[bool, list[str]]:
        """Validate a joke before import.

        Args:
            joke: Joke model to validate

        Returns:
            Tuple of (is_valid, error_messages)

        Note:
            Default implementation performs basic validation.
            Subclasses can override for source-specific validation.
        """
        errors = []

        # Basic validation
        if not joke.content:
            errors.append("Joke has no content")

        for element in joke.content:
            if not element.text or not element.text.strip():
                errors.append(f"Empty text in {element.type} element")

        if not joke.metadata:
            errors.append("Joke has no metadata")

        return (len(errors) == 0, errors)

    def import_to_staging(
        self,
        session: Session,
        validate: bool = True,
        batch_size: int = 100,
        max_records: int | None = None,
    ) -> ImportMetadata:
        """Execute complete import pipeline to staging database.

        Pipeline steps:
        1. Download source data
        2. Parse into raw dictionaries
        3. Transform to Joke models
        4. Optionally validate
        5. Save to staging database
        6. Return import metadata

        Args:
            session: Database session for staging database
            validate: Whether to validate jokes before import
            batch_size: Number of jokes to batch before committing
            max_records: Maximum number of records to import (for testing)

        Returns:
            ImportMetadata with import statistics

        Raises:
            ImportError: If critical error occurs during import
        """
        import_id = str(uuid4())
        start_time = datetime.now(timezone.utc)

        logger.info(f"Starting import from {self.source_name} (import_id={import_id})")

        progress = ImportProgress()
        metadata = ImportMetadata(
            import_id=import_id,
            source=self.source_name,
            imported_at=start_time,
            total_records=0,
            successful=0,
            failed=0,
            validation_status=ValidationStatus.PENDING,
        )

        try:
            # Step 1: Download
            logger.info("Downloading source data...")
            data_path = self.download()
            logger.info(f"Downloaded to {data_path}")

            # Step 2: Parse and transform
            logger.info("Parsing and transforming data...")

            batch = []
            for raw_data in self.parse(data_path):
                # Check max_records limit
                if max_records and progress.processed >= max_records:
                    logger.info(f"Reached max_records limit ({max_records})")
                    break

                progress.processed += 1
                metadata.total_records += 1

                # Transform
                try:
                    joke = self.transform(raw_data)
                    if joke is None:
                        progress.failed += 1
                        metadata.failed += 1
                        logger.warning(f"Failed to transform record {progress.processed}")
                        continue

                    # Validate
                    if validate:
                        is_valid, errors = self.validate(joke)
                        if not is_valid:
                            progress.failed += 1
                            metadata.failed += 1
                            logger.warning(
                                f"Validation failed for record {progress.processed}: {errors}"
                            )
                            continue

                    # Add to batch
                    batch.append((joke, raw_data))
                    progress.successful += 1

                    # Save batch
                    if len(batch) >= batch_size:
                        self._save_batch(session, batch, import_id)
                        metadata.successful += len(batch)
                        batch = []
                        logger.info(
                            f"Progress: {progress.processed}/{progress.total or '?'} "
                            f"({progress.successful} successful, {progress.failed} failed)"
                        )

                except Exception as e:
                    progress.failed += 1
                    metadata.failed += 1
                    logger.error(f"Error processing record {progress.processed}: {e}")
                    continue

            # Save remaining batch
            if batch:
                self._save_batch(session, batch, import_id)
                metadata.successful += len(batch)

            logger.info(
                f"Import complete: {metadata.successful} successful, "
                f"{metadata.failed} failed out of {metadata.total_records} total"
            )

            return metadata

        except Exception as e:
            logger.error(f"Critical error during import: {e}")
            metadata.notes = str(e)
            raise ImportError(f"Import failed: {e}") from e

    def _save_batch(
        self,
        session: Session,
        batch: list[tuple[Joke, dict[str, Any]]],
        import_id: str,
    ) -> None:
        """Save a batch of jokes to staging database.

        Args:
            session: Database session
            batch: List of (joke, raw_data) tuples
            import_id: Import batch ID

        Note:
            This will be implemented once staging database models are ready.
            For now, it's a placeholder that logs the batch.
        """
        # TODO: Implement actual staging database save
        logger.debug(f"Saving batch of {len(batch)} jokes to staging (import_id={import_id})")
        # This will be implemented with staging database operations

    def cleanup(self) -> None:
        """Clean up temporary files after import.

        Removes downloaded files and temporary directories.
        """
        import shutil

        if self.source_temp_dir.exists():
            logger.info(f"Cleaning up temporary directory: {self.source_temp_dir}")
            shutil.rmtree(self.source_temp_dir)


class ImportError(Exception):
    """Exception raised when import operation fails."""

    pass
