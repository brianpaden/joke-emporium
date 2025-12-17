"""Command-line interface for joke importers."""

import logging
import sys
from pathlib import Path

import click

from joke_emporium.db.models.staging import ReviewStatus
from joke_emporium.db.staging import (
    approve_batch_by_quality,
    approve_staging_joke,
    delete_import_batch,
    get_all_import_batches,
    get_import_batch,
    get_staging_jokes_by_status,
    get_staging_session,
    init_staging_db,
    reject_staging_joke,
    update_review_status,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@click.group()
def cli() -> None:
    """Joke Emporium import management CLI.

    Manage data imports, staging database, and validation.
    """
    pass


@cli.command("import")
@click.argument("source", type=click.Choice(["taivop"]))
@click.option("--validate/--no-validate", default=True, help="Validate jokes before import")
@click.option("--max-records", type=int, default=None, help="Maximum records to import (for testing)")
@click.option(
    "--staging-db",
    type=click.Path(),
    default=None,
    help="Path to staging database (default: data/staging.db)",
)
def import_cmd(source: str, validate: bool, max_records: int | None, staging_db: str | None) -> None:
    """Import jokes from a data source.

    SOURCE: Data source to import from (currently supports: taivop)

    Examples:
        # Import from taivop dataset with validation
        python -m joke_emporium.importers.cli import taivop

        # Import without validation (faster, less safe)
        python -m joke_emporium.importers.cli import taivop --no-validate

        # Import only 100 records for testing
        python -m joke_emporium.importers.cli import taivop --max-records 100
    """
    try:
        # Initialize staging database
        db_url = f"sqlite:///{staging_db}" if staging_db else None
        init_staging_db(db_url)

        click.echo(f"Starting import from source: {source}")
        click.echo(f"Validation: {'enabled' if validate else 'disabled'}")
        if max_records:
            click.echo(f"Max records: {max_records}")

        # Import based on source
        if source == "taivop":
            try:
                from joke_emporium.importers.taivop import TaivopImporter
            except ImportError:
                click.echo("Error: TaivopImporter not implemented yet.", err=True)
                click.echo("This importer will be available in Sprint 2.", err=True)
                click.echo("\nTo implement it, create: src/joke_emporium/importers/taivop.py", err=True)
                sys.exit(1)

            importer = TaivopImporter()

            with next(get_staging_session()) as session:
                metadata = importer.import_to_staging(session=session, validate=validate, max_records=max_records)

                click.echo("\n" + "=" * 60)
                click.echo("Import Complete!")
                click.echo("=" * 60)
                click.echo(f"Import ID: {metadata.import_id}")
                click.echo(f"Source: {metadata.source}")
                click.echo(f"Total records: {metadata.total_records}")
                click.echo(
                    f"Successful: {metadata.successful} ({metadata.successful / metadata.total_records * 100:.1f}%)"
                )
                click.echo(f"Failed: {metadata.failed} ({metadata.failed / metadata.total_records * 100:.1f}%)")
                click.echo(f"Status: {metadata.validation_status.value}")

                click.echo("\nNext steps:")
                click.echo(f"  1. Inspect staging: python -m joke_emporium.importers.cli inspect {metadata.import_id}")
                click.echo(
                    f"  2. Merge to production: python -m joke_emporium.importers.cli merge {metadata.import_id}"
                )

        else:
            click.echo(f"Unknown source: {source}", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error during import: {e}", err=True)
        logger.exception("Import failed")
        sys.exit(1)


@cli.command("list")
@click.option("--status", type=click.Choice(["pending", "approved", "rejected"]), help="Filter by status")
@click.option(
    "--staging-db",
    type=click.Path(),
    default=None,
    help="Path to staging database",
)
def list_imports(status: str | None, staging_db: str | None) -> None:
    """List all import batches.

    Examples:
        # List all imports
        python -m joke_emporium.importers.cli list

        # List only pending imports
        python -m joke_emporium.importers.cli list --status pending
    """
    try:
        db_url = f"sqlite:///{staging_db}" if staging_db else None
        init_staging_db(db_url)

        with next(get_staging_session()) as session:
            batches = get_all_import_batches(session, validation_status=status)

            if not batches:
                click.echo("No import batches found.")
                return

            click.echo(f"\nFound {len(batches)} import batch(es):\n")
            click.echo(
                f"{'Import ID':<38} {'Source':<25} {'Date':<20} {'Total':<8} {'Success':<8} {'Failed':<8} {'Status':<10}"
            )
            click.echo("-" * 130)

            for batch in batches:
                click.echo(
                    f"{batch.import_id:<38} "
                    f"{batch.source:<25} "
                    f"{batch.imported_at.strftime('%Y-%m-%d %H:%M'):<20} "
                    f"{batch.total_records:<8} "
                    f"{batch.successful:<8} "
                    f"{batch.failed:<8} "
                    f"{batch.validation_status:<10}"
                )

    except Exception as e:
        click.echo(f"Error listing imports: {e}", err=True)
        sys.exit(1)


@cli.command("approve")
@click.argument("staging_id", type=int)
@click.option("--notes", default=None, help="Optional approval notes")
@click.option(
    "--staging-db",
    type=click.Path(),
    default=None,
    help="Path to staging database",
)
def approve(staging_id: int, notes: str | None, staging_db: str | None) -> None:
    """Approve a staging joke for production.

    STAGING_ID: Database ID of the staging joke

    Example:
        python -m joke_emporium.importers.cli approve 123 --notes "Looks good"
    """
    try:
        db_url = f"sqlite:///{staging_db}" if staging_db else None
        init_staging_db(db_url)

        with next(get_staging_session()) as session:
            if approve_staging_joke(session, staging_id, notes):
                click.echo(f"Approved staging joke {staging_id}")
            else:
                click.echo(f"Staging joke not found: {staging_id}", err=True)
                sys.exit(1)

    except Exception as e:
        click.echo(f"Error approving joke: {e}", err=True)
        sys.exit(1)


@cli.command("reject")
@click.argument("staging_id", type=int)
@click.argument("reason")
@click.option(
    "--staging-db",
    type=click.Path(),
    default=None,
    help="Path to staging database",
)
def reject(staging_id: int, reason: str, staging_db: str | None) -> None:
    """Reject a staging joke.

    STAGING_ID: Database ID of the staging joke
    REASON: Reason for rejection

    Example:
        python -m joke_emporium.importers.cli reject 123 "Inappropriate content"
    """
    try:
        db_url = f"sqlite:///{staging_db}" if staging_db else None
        init_staging_db(db_url)

        with next(get_staging_session()) as session:
            if reject_staging_joke(session, staging_id, reason):
                click.echo(f"Rejected staging joke {staging_id}: {reason}")
            else:
                click.echo(f"Staging joke not found: {staging_id}", err=True)
                sys.exit(1)

    except Exception as e:
        click.echo(f"Error rejecting joke: {e}", err=True)
        sys.exit(1)


@cli.command("delete")
@click.argument("import_id")
@click.option("--yes", is_flag=True, help="Skip confirmation")
@click.option(
    "--staging-db",
    type=click.Path(),
    default=None,
    help="Path to staging database",
)
def delete(import_id: str, yes: bool, staging_db: str | None) -> None:
    """Delete an import batch and all its staging jokes.

    IMPORT_ID: UUID of the import batch to delete

    Example:
        python -m joke_emporium.importers.cli delete <import_id> --yes
    """
    try:
        db_url = f"sqlite:///{staging_db}" if staging_db else None
        init_staging_db(db_url)

        if not yes:
            confirm = click.confirm(f"Delete import batch {import_id} and all its jokes?")
            if not confirm:
                click.echo("Cancelled.")
                return

        with next(get_staging_session()) as session:
            if delete_import_batch(session, import_id):
                click.echo(f"Deleted import batch {import_id}")
            else:
                click.echo(f"Import batch not found: {import_id}", err=True)
                sys.exit(1)

    except Exception as e:
        click.echo(f"Error deleting import: {e}", err=True)
        sys.exit(1)


@cli.command("reset")
@click.option("--yes", is_flag=True, help="Skip confirmation")
@click.option(
    "--staging-db",
    type=click.Path(),
    default=None,
    help="Path to staging database",
)
def reset(yes: bool, staging_db: str | None) -> None:
    """Reset/clear the staging database.

    WARNING: This will delete ALL import batches and staging jokes!

    Example:
        python -m joke_emporium.importers.cli reset --yes
    """
    try:
        db_path = Path(staging_db) if staging_db else Path("data/staging.db")

        if not db_path.exists():
            click.echo(f"Staging database does not exist: {db_path}")
            return

        if not yes:
            click.echo(f"WARNING: This will delete the staging database at: {db_path}")
            click.echo("All import batches and staging jokes will be permanently removed.")
            confirm = click.confirm("Are you sure you want to continue?")
            if not confirm:
                click.echo("Cancelled.")
                return

        # Delete the database file
        db_path.unlink()
        click.echo(f"Deleted staging database: {db_path}")

        # Reinitialize with empty database
        db_url = f"sqlite:///{db_path}"
        init_staging_db(db_url)
        click.echo("Reinitialized empty staging database")
        click.echo("\nStaging database has been reset successfully.")

    except Exception as e:
        click.echo(f"Error resetting database: {e}", err=True)
        sys.exit(1)


@cli.command("flag")
@click.argument("staging_id", type=int)
@click.option("--notes", default=None, help="Review notes")
@click.option(
    "--staging-db",
    type=click.Path(),
    default=None,
    help="Path to staging database",
)
def flag(staging_id: int, notes: str | None, staging_db: str | None) -> None:
    """Flag a staging joke for manual review.

    STAGING_ID: Database ID of the staging joke

    Example:
        python -m joke_emporium.importers.cli flag 123 --notes "Check category"
    """
    try:
        db_url = f"sqlite:///{staging_db}" if staging_db else None
        init_staging_db(db_url)

        with next(get_staging_session()) as session:
            if update_review_status(session, staging_id, ReviewStatus.UNDER_REVIEW, notes=notes):
                click.echo(f"Flagged staging joke {staging_id} for review")
            else:
                click.echo(f"Staging joke not found: {staging_id}", err=True)
                sys.exit(1)

    except Exception as e:
        click.echo(f"Error flagging joke: {e}", err=True)
        sys.exit(1)


@cli.command("approve-batch")
@click.argument("import_id")
@click.option("--min-score", type=float, help="Minimum score to approve")
@click.option(
    "--staging-db",
    type=click.Path(),
    default=None,
    help="Path to staging database",
)
def approve_batch_cmd(import_id: str, min_score: float | None, staging_db: str | None) -> None:
    """Approve all jokes in an import batch.

    IMPORT_ID: UUID of the import batch

    Examples:
        # Approve all jokes in batch
        python -m joke_emporium.importers.cli approve-batch <import_id>

        # Approve only high-quality jokes
        python -m joke_emporium.importers.cli approve-batch <import_id> --min-score 1000
    """
    try:
        db_url = f"sqlite:///{staging_db}" if staging_db else None
        init_staging_db(db_url)

        with next(get_staging_session()) as session:
            count = approve_batch_by_quality(session, import_id, min_score=min_score)
            click.echo(f"Approved {count} jokes from import {import_id}")

    except Exception as e:
        click.echo(f"Error approving batch: {e}", err=True)
        sys.exit(1)


@cli.command("review")
@click.argument("import_id", required=False)
@click.option(
    "--status",
    type=click.Choice(["pending", "approved", "rejected", "under_review", "duplicate", "merged", "all"]),
    default="all",
    help="Filter by review status",
)
@click.option("--limit", type=int, default=20, help="Max jokes to show")
@click.option("-v", "--verbose", count=True, help="Increase verbosity (use -v, -vv, or -vvv for more detail)")
@click.option("--max-chars", type=int, default=None, help="Max characters to show for joke text (default: 100, -v: 300, -vv: 500, -vvv: unlimited)")
@click.option(
    "--staging-db",
    type=click.Path(),
    default=None,
    help="Path to staging database",
)
def review_cmd(import_id: str | None, status: str, limit: int, verbose: int, max_chars: int | None, staging_db: str | None) -> None:
    """Review jokes before merging to production.

    IMPORT_ID: Optional UUID of the import batch to filter by

    Verbosity levels:
        (default): Shows ID, status, and 100 chars of text
        -v: Adds tags, scores, and 300 chars of text
        -vv: Adds maturity, structure, review notes, and 500 chars of text
        -vvv: Shows all fields including engagement, GTVH, and full text

    Examples:
        # Review all pending jokes across all imports
        python -m joke_emporium.importers.cli review --status pending

        # Review approved jokes from specific import with basic details
        python -m joke_emporium.importers.cli review <import_id> --status approved -v

        # Show full details with all metadata
        python -m joke_emporium.importers.cli review <import_id> -vvv

        # Review jokes from specific import
        python -m joke_emporium.importers.cli review <import_id>
    """
    try:
        db_url = f"sqlite:///{staging_db}" if staging_db else None
        init_staging_db(db_url)

        with next(get_staging_session()) as session:
            # Get import batch ID if specified
            batch_id = None
            if import_id:
                batch = get_import_batch(session, import_id)
                if not batch:
                    click.echo(f"Import batch not found: {import_id}", err=True)
                    sys.exit(1)
                batch_id = batch.id

            # Get jokes
            jokes = get_staging_jokes_by_status(
                session, import_batch_id=batch_id, status=None if status == "all" else status, limit=limit
            )

            if not jokes:
                click.echo(f"No jokes found with status: {status}")
                return

            # Determine max characters for text display based on verbosity
            if max_chars is None:
                if verbose == 0:
                    max_chars = 100
                elif verbose == 1:
                    max_chars = 300
                elif verbose == 2:
                    max_chars = 500
                else:  # verbose >= 3
                    max_chars = 999999  # Effectively unlimited

            if import_id:
                click.echo(f"\nReviewing {len(jokes)} joke(s) from import {import_id}")
            else:
                click.echo(f"\nReviewing {len(jokes)} joke(s) across all imports")
            click.echo("=" * 80)

            for staging_joke in jokes:
                import json

                # Parse joke content
                content_data = json.loads(staging_joke.content_json)
                joke_text = " ".join(elem.get("text", "") for elem in content_data)

                # Show joke ID and status (always shown)
                status_icon = {
                    "pending": "[ ]",
                    "approved": "[+]",
                    "rejected": "[X]",
                    "under_review": "[?]",
                    "duplicate": "[=]",
                    "merged": "[>]",
                }.get(staging_joke.review_status, "[?]")

                click.echo(f"\n{status_icon} ID: {staging_joke.id} | UUID: {staging_joke.joke_uuid}")
                click.echo(f"   Status: {staging_joke.review_status}")

                # Show joke text with configurable max length (always shown)
                preview = joke_text[:max_chars] + "..." if len(joke_text) > max_chars else joke_text
                click.echo(f"   Text: {preview}")

                # Level 1+ (-v): Show tags and scores
                if verbose >= 1:
                    tags_data = json.loads(staging_joke.tags_json) if staging_joke.tags_json else []
                    if tags_data:
                        tag_preview = tags_data[:5] if verbose < 3 else tags_data
                        click.echo(f"   Tags: {', '.join(tag_preview)}")
                    if staging_joke.weighted_avg_funniness:
                        click.echo(f"   Avg Funniness: {staging_joke.weighted_avg_funniness:.1f}")
                    if staging_joke.weighted_avg_quality:
                        click.echo(f"   Avg Quality: {staging_joke.weighted_avg_quality:.1f}")
                    if staging_joke.total_ratings_count:
                        click.echo(f"   Total Ratings: {staging_joke.total_ratings_count}")

                # Level 2+ (-vv): Show maturity, structure, review notes
                if verbose >= 2:
                    click.echo(f"   Maturity: {staging_joke.maturity_rating}")
                    if staging_joke.structure:
                        click.echo(f"   Structure: {staging_joke.structure}")
                    if staging_joke.cognitive_type:
                        click.echo(f"   Cognitive Type: {staging_joke.cognitive_type}")
                    if staging_joke.review_notes:
                        click.echo(f"   Review Notes: {staging_joke.review_notes}")
                    if staging_joke.reviewed_by:
                        click.echo(f"   Reviewed By: {staging_joke.reviewed_by}")
                    if staging_joke.reviewed_at:
                        click.echo(f"   Reviewed At: {staging_joke.reviewed_at}")

                # Level 3+ (-vvv): Show everything including engagement, GTVH, metadata
                if verbose >= 3:
                    click.echo(f"   Language: {staging_joke.language}")
                    if staging_joke.source_platform:
                        click.echo(f"   Source Platform: {staging_joke.source_platform}")
                    if staging_joke.source_url:
                        click.echo(f"   Source URL: {staging_joke.source_url}")

                    # Dates
                    if staging_joke.created_date:
                        click.echo(f"   Created: {staging_joke.created_date}")
                    if staging_joke.scraped_date:
                        click.echo(f"   Scraped: {staging_joke.scraped_date}")
                    click.echo(f"   Added: {staging_joke.added_date}")
                    click.echo(f"   Modified: {staging_joke.last_modified}")

                    # Flags
                    flags_data = json.loads(staging_joke.flags_json) if staging_joke.flags_json else {}
                    if flags_data:
                        click.echo(f"   Flags: {flags_data}")

                    # Engagement
                    if staging_joke.engagement_json:
                        engagement_data = json.loads(staging_joke.engagement_json)
                        click.echo(f"   Engagement: {engagement_data}")

                    # GTVH
                    if staging_joke.gtvh_json:
                        gtvh_data = json.loads(staging_joke.gtvh_json)
                        click.echo(f"   GTVH: {gtvh_data}")

                    # Metadata
                    if staging_joke.metadata_json:
                        metadata = json.loads(staging_joke.metadata_json)
                        click.echo(f"   Metadata: {metadata}")

                    # Duplicate info
                    if staging_joke.duplicate_of_uuid:
                        click.echo(f"   Duplicate Of: {staging_joke.duplicate_of_uuid}")
                        if staging_joke.duplicate_similarity:
                            click.echo(f"   Similarity: {staging_joke.duplicate_similarity:.2%}")

                    # Merge info
                    if staging_joke.merged_to_uuid:
                        click.echo(f"   Merged To: {staging_joke.merged_to_uuid}")
                        click.echo(f"   Merged At: {staging_joke.merged_at}")

                    click.echo(f"   Verified: {staging_joke.verified}")
                    click.echo(f"   Import Batch ID: {staging_joke.import_batch_id}")

                click.echo("   " + "-" * 76)

            click.echo(f"\nShowing {len(jokes)} joke(s)")

    except Exception as e:
        click.echo(f"Error reviewing jokes: {e}", err=True)
        logger.exception("Review failed")
        sys.exit(1)


@cli.command("merge")
@click.argument("import_id")
@click.option("--dry-run", is_flag=True, help="Preview merge without committing")
@click.option(
    "--staging-db",
    type=click.Path(),
    default=None,
    help="Path to staging database",
)
@click.option(
    "--prod-db",
    type=click.Path(),
    default=None,
    help="Path to production database",
)
def merge(import_id: str, dry_run: bool, staging_db: str | None, prod_db: str | None) -> None:
    """Merge approved staging jokes to production database.

    IMPORT_ID: UUID of the import batch to merge

    Only merges jokes with status='approved'.
    All operations are transactional (all-or-nothing).

    Examples:
        # Preview merge
        python -m joke_emporium.importers.cli merge <import_id> --dry-run

        # Perform merge
        python -m joke_emporium.importers.cli merge <import_id>
    """
    try:
        from joke_emporium.db.merge import merge_approved_jokes
        from joke_emporium.db.production import get_production_session, init_production_db

        # Initialize databases
        staging_db_url = f"sqlite:///{staging_db}" if staging_db else None
        init_staging_db(staging_db_url)

        prod_db_url = f"sqlite:///{prod_db}" if prod_db else None
        init_production_db(prod_db_url)

        with next(get_staging_session()) as staging_session:
            # Get import batch
            batch = get_import_batch(staging_session, import_id)
            if not batch:
                click.echo(f"Import batch not found: {import_id}", err=True)
                sys.exit(1)

            with next(get_production_session()) as production_session:
                try:
                    stats = merge_approved_jokes(
                        staging_session, production_session, batch.id, batch.source, dry_run=dry_run
                    )

                    if dry_run:
                        click.echo("\n[DRY RUN] - No changes committed\n")
                    else:
                        click.echo("\n[MERGE COMPLETE]\n")

                    click.echo("=" * 60)
                    click.echo(f"Total jokes reviewed: {stats['total']}")
                    click.echo(f"Merged to production: {stats['merged']}")
                    click.echo(f"Skipped (duplicate): {stats['skipped_duplicate']}")
                    click.echo(f"Failed: {stats['failed']}")
                    click.echo("=" * 60)

                except Exception as e:
                    click.echo(f"\n[FAILED] Merge failed: {e}")
                    if not dry_run:
                        click.echo("All changes rolled back (transaction failed)")
                    raise

    except ImportError as e:
        click.echo(f"Error: Missing module for merge: {e}", err=True)
        click.echo("Make sure merge.py is implemented.", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error merging import: {e}", err=True)
        logger.exception("Merge failed")
        sys.exit(1)


if __name__ == "__main__":
    cli()
