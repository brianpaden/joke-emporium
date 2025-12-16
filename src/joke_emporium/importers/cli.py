"""Command-line interface for joke importers."""

import logging
import sys
from pathlib import Path

import click

from joke_emporium.db.staging import (
    approve_staging_joke,
    delete_import_batch,
    get_all_import_batches,
    get_import_batch,
    get_staging_jokes,
    get_staging_session,
    init_staging_db,
    reject_staging_joke,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
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
def import_cmd(
    source: str, validate: bool, max_records: int | None, staging_db: str | None
) -> None:
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
                metadata = importer.import_to_staging(
                    session=session, validate=validate, max_records=max_records
                )

                click.echo("\n" + "=" * 60)
                click.echo("Import Complete!")
                click.echo("=" * 60)
                click.echo(f"Import ID: {metadata.import_id}")
                click.echo(f"Source: {metadata.source}")
                click.echo(f"Total records: {metadata.total_records}")
                click.echo(
                    f"Successful: {metadata.successful} "
                    f"({metadata.successful / metadata.total_records * 100:.1f}%)"
                )
                click.echo(
                    f"Failed: {metadata.failed} "
                    f"({metadata.failed / metadata.total_records * 100:.1f}%)"
                )
                click.echo(f"Status: {metadata.validation_status.value}")

                click.echo("\nNext steps:")
                click.echo(f"  1. Inspect staging: python -m joke_emporium.importers.cli inspect {metadata.import_id}")
                click.echo(f"  2. Merge to production: python -m joke_emporium.importers.cli merge {metadata.import_id}")

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
            click.echo(f"{'Import ID':<38} {'Source':<25} {'Date':<20} {'Total':<8} {'Success':<8} {'Failed':<8} {'Status':<10}")
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


@cli.command("inspect")
@click.argument("import_id")
@click.option("--status", type=click.Choice(["pending", "approved", "rejected"]), help="Filter by status")
@click.option("--limit", type=int, default=10, help="Number of jokes to show")
@click.option(
    "--staging-db",
    type=click.Path(),
    default=None,
    help="Path to staging database",
)
def inspect(import_id: str, status: str | None, limit: int, staging_db: str | None) -> None:
    """Inspect staging jokes for an import batch.

    IMPORT_ID: UUID of the import batch to inspect

    Examples:
        # Inspect first 10 jokes
        python -m joke_emporium.importers.cli inspect <import_id>

        # Inspect only pending jokes
        python -m joke_emporium.importers.cli inspect <import_id> --status pending

        # Show more jokes
        python -m joke_emporium.importers.cli inspect <import_id> --limit 50
    """
    try:
        db_url = f"sqlite:///{staging_db}" if staging_db else None
        init_staging_db(db_url)

        with next(get_staging_session()) as session:
            # Get import batch info
            batch = get_import_batch(session, import_id)
            if not batch:
                click.echo(f"Import batch not found: {import_id}", err=True)
                sys.exit(1)

            click.echo(f"\nImport Batch: {batch.import_id}")
            click.echo(f"Source: {batch.source}")
            click.echo(f"Imported: {batch.imported_at}")
            click.echo(f"Status: {batch.validation_status}")
            click.echo(f"Total: {batch.total_records}, Success: {batch.successful}, Failed: {batch.failed}")

            # Get staging jokes
            jokes = get_staging_jokes(session, import_id=import_id, validation_status=status, limit=limit)

            if not jokes:
                click.echo("\nNo staging jokes found with the specified filters.")
                return

            click.echo(f"\nShowing {len(jokes)} joke(s):\n")

            for i, joke in enumerate(jokes, 1):
                click.echo(f"{i}. ID: {joke.id} | UUID: {joke.joke_uuid}")
                click.echo(f"   Status: {joke.validation_status}")
                click.echo(f"   Preview: {joke.text_preview}")
                if joke.validation_notes:
                    click.echo(f"   Notes: {joke.validation_notes}")
                if joke.duplicate_of:
                    click.echo(f"   Duplicate of: {joke.duplicate_of}")
                click.echo()

    except Exception as e:
        click.echo(f"Error inspecting import: {e}", err=True)
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
        click.echo(f"Reinitialized empty staging database")
        click.echo("\nStaging database has been reset successfully.")

    except Exception as e:
        click.echo(f"Error resetting database: {e}", err=True)
        sys.exit(1)


@cli.command("merge")
@click.argument("import_id")
@click.option("--auto-approve", is_flag=True, help="Auto-approve all pending jokes")
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
def merge(
    import_id: str, auto_approve: bool, staging_db: str | None, prod_db: str | None
) -> None:
    """Merge approved staging jokes to production database.

    IMPORT_ID: UUID of the import batch to merge

    Examples:
        # Merge only approved jokes
        python -m joke_emporium.importers.cli merge <import_id>

        # Auto-approve and merge all jokes
        python -m joke_emporium.importers.cli merge <import_id> --auto-approve
    """
    try:
        click.echo("Merge functionality coming soon!")
        click.echo("This will:")
        click.echo("  1. Query approved jokes from staging")
        click.echo("  2. Check for duplicates in production")
        click.echo("  3. Insert new jokes into production")
        click.echo("  4. Update import batch status")

        # TODO: Implement merge logic

    except Exception as e:
        click.echo(f"Error merging import: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
