"""Merge staging jokes to production database."""

import logging
from datetime import UTC, datetime

from sqlmodel import Session

from joke_emporium.db.deduplication import check_duplicate_in_production
from joke_emporium.db.models.staging import ReviewStatus
from joke_emporium.db.production import save_joke_to_production
from joke_emporium.db.staging import get_staging_jokes_by_status
from joke_emporium.models.joke import Joke

logger = logging.getLogger(__name__)


def merge_approved_jokes(
    staging_session: Session, production_session: Session, import_batch_id: int, source_name: str, dry_run: bool = False
) -> dict[str, int]:
    """Merge approved jokes from staging to production.

    Args:
        staging_session: Staging database session
        production_session: Production database session
        import_batch_id: Import batch to merge
        source_name: Source name for provenance
        dry_run: If True, don't actually commit changes

    Returns:
        Statistics dict with counts
    """
    stats = {
        "total": 0,
        "merged": 0,
        "skipped_duplicate": 0,
        "failed": 0,
    }

    # Get approved jokes
    approved_jokes = get_staging_jokes_by_status(
        staging_session, import_batch_id=import_batch_id, status=ReviewStatus.APPROVED
    )

    stats["total"] = len(approved_jokes)

    for staging_joke in approved_jokes:
        try:
            # Parse joke from JSON

            joke = Joke.model_validate_json(staging_joke.content_json)

            # Check for duplicates in production
            is_duplicate, duplicate_uuid = check_duplicate_in_production(production_session, joke)

            if is_duplicate:
                # Mark as duplicate in staging
                staging_joke.review_status = ReviewStatus.DUPLICATE
                staging_joke.duplicate_of_uuid = duplicate_uuid
                staging_joke.duplicate_similarity = 1.0
                if not dry_run:
                    staging_session.add(staging_joke)
                stats["skipped_duplicate"] += 1
                logger.info(f"Skipped duplicate joke: {joke.id} (duplicate of {duplicate_uuid})")
                continue

            if not dry_run:
                # Save to production
                saved_uuid = save_joke_to_production(
                    production_session, joke, import_batch_id, source_name, staging_joke_id=staging_joke.id
                )

                # Update staging record
                staging_joke.review_status = ReviewStatus.MERGED
                staging_joke.merged_to_uuid = saved_uuid
                staging_joke.merged_at = datetime.now(UTC)
                staging_session.add(staging_joke)

            stats["merged"] += 1
            logger.info(f"Merged joke: {joke.id}")

        except Exception as e:
            logger.error(f"Failed to merge staging joke {staging_joke.id}: {e}")
            stats["failed"] += 1
            continue

    if not dry_run:
        try:
            staging_session.commit()
            production_session.commit()
        except Exception as e:
            logger.error(f"Failed to commit merge transaction: {e}")
            staging_session.rollback()
            production_session.rollback()
            raise

    return stats
