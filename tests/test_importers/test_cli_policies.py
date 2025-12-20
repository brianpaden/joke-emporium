"""Integration tests for the apply-policies CLI command.

These tests verify the CLI command works correctly end-to-end with real database files.
"""

from datetime import UTC, datetime

import pytest
from click.testing import CliRunner

from joke_emporium.db.models.staging import ImportBatchDB, ReviewStatus, StagingJokeDB
from joke_emporium.importers.cli import cli


@pytest.fixture
def cli_db(tmp_path):
    """Create a temporary staging database for CLI tests."""
    from joke_emporium.db.staging import init_staging_db

    db_path = tmp_path / "cli_test.db"
    db_url = f"sqlite:///{db_path}"
    init_staging_db(db_url)

    return db_path


@pytest.fixture
def cli_batch(cli_db):
    """Create a sample import batch in the CLI test database."""
    from joke_emporium.db.staging import get_staging_session

    # Use the already-initialized global connection
    with next(get_staging_session()) as session:
        batch = ImportBatchDB(
            import_id="cli-test-batch",
            source="test",
            source_version="1.0",
            imported_at=datetime.now(UTC),
            total_records=0,
            successful=0,
            failed=0,
        )
        session.add(batch)
        session.commit()
        session.refresh(batch)

        yield batch


def create_joke(cli_db, cli_batch, **kwargs):
    """Helper to create a staging joke in the CLI database."""
    from joke_emporium.db.staging import get_staging_session

    defaults = {
        "joke_uuid": f"joke-{datetime.now().timestamp()}",
        "version": 1,
        "content_json": '[{"type": "text", "text": "test"}]',
        "flags_json": '{"nsfw": false}',
        "tags_json": "[]",
        "language": "en",
        "added_date": datetime.now(UTC),
        "last_modified": datetime.now(UTC),
        "import_batch_id": cli_batch.id,
        "original_data_json": "{}",
        "review_status": ReviewStatus.PENDING,
    }
    defaults.update(kwargs)

    # Use the already-initialized global connection
    with next(get_staging_session()) as session:
        joke = StagingJokeDB(**defaults)
        session.add(joke)
        session.commit()
        session.refresh(joke)

        return joke


class TestCLIApplyPoliciesIntegration:
    """Integration tests for the apply-policies CLI command."""

    def test_command_exists(self):
        """Test that the apply-policies command is registered."""
        runner = CliRunner()
        result = runner.invoke(cli, ["apply-policies", "--help"])
        assert result.exit_code == 0
        assert "Apply automated policies" in result.output
        assert "IMPORT_ID" in result.output

    def test_missing_import_batch(self, cli_db):
        """Test error when import batch doesn't exist."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["apply-policies", "nonexistent", "--staging-db", str(cli_db), "--yes"],
        )
        assert result.exit_code == 1
        assert "Import batch not found" in result.output

    def test_missing_config_file(self, cli_db, cli_batch):
        """Test error handling when config file not found."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                cli_batch.import_id,
                "--config",
                "nonexistent.yaml",
                "--staging-db",
                str(cli_db),
                "--yes",
            ],
        )
        assert result.exit_code == 1
        assert "Config file not found" in result.output

    def test_invalid_yaml_syntax(self, cli_db, cli_batch, tmp_path):
        """Test error handling for invalid YAML syntax."""
        config = tmp_path / "bad.yaml"
        config.write_text("invalid: yaml: {", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                cli_batch.import_id,
                "--config",
                str(config),
                "--staging-db",
                str(cli_db),
                "--yes",
            ],
        )
        assert result.exit_code == 1
        assert "YAML" in result.output or "Invalid" in result.output

    def test_invalid_policy_structure(self, cli_db, cli_batch, tmp_path):
        """Test error handling for invalid policy structure."""
        config = tmp_path / "bad_policy.yaml"
        config.write_text(
            """
policies:
  auto_approve:
    - conditions:  # Missing 'name'
        - language: "en"
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                cli_batch.import_id,
                "--config",
                str(config),
                "--staging-db",
                str(cli_db),
                "--yes",
            ],
        )
        assert result.exit_code == 1
        assert "Invalid" in result.output or "requires 'name'" in result.output

    def test_dry_run_no_database_changes(self, cli_db, cli_batch, tmp_path):
        """Test --dry-run doesn't modify database."""
        from joke_emporium.db.staging import get_staging_session

        # Create test jokes
        jokes = []
        for i in range(3):
            joke = create_joke(
                cli_db,
                cli_batch,
                joke_uuid=f"dry-run-{i}",
                weighted_avg_funniness=4.5,
                total_ratings_count=15,
            )
            jokes.append(joke)

        # Create config
        config = tmp_path / "test.yaml"
        config.write_text(
            """
policies:
  auto_approve:
    - name: test
      conditions:
        - weighted_avg_funniness: ">= 4.0"
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                cli_batch.import_id,
                "--config",
                str(config),
                "--staging-db",
                str(cli_db),
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        assert "DRY RUN" in result.output

        # Verify database NOT changed - query jokes by UUID
        with next(get_staging_session()) as session:
            from sqlmodel import select

            for joke in jokes:
                db_joke = session.exec(select(StagingJokeDB).where(StagingJokeDB.joke_uuid == joke.joke_uuid)).one()
                assert db_joke.review_status == ReviewStatus.PENDING

    def test_apply_with_custom_config(self, cli_db, cli_batch, tmp_path):
        """Test applying policies with custom config file."""
        from joke_emporium.db.staging import get_staging_session

        # Create test jokes
        high_quality = create_joke(
            cli_db,
            cli_batch,
            joke_uuid="high-quality",
            weighted_avg_funniness=4.8,
            total_ratings_count=20,
        )

        low_quality = create_joke(
            cli_db,
            cli_batch,
            joke_uuid="low-quality",
            weighted_avg_funniness=1.5,
            total_ratings_count=10,
        )

        # Create config
        config = tmp_path / "custom.yaml"
        config.write_text(
            """
policies:
  auto_approve:
    - name: excellent
      conditions:
        - weighted_avg_funniness: ">= 4.5"
  auto_reject:
    - name: poor
      conditions:
        - weighted_avg_funniness: "< 2.0"
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                cli_batch.import_id,
                "--config",
                str(config),
                "--staging-db",
                str(cli_db),
                "--yes",
            ],
        )

        assert result.exit_code == 0
        assert "Successfully" in result.output or "Approved" in result.output

        # Verify database changes - query jokes by UUID
        with next(get_staging_session()) as session:
            from sqlmodel import select

            db_high = session.exec(select(StagingJokeDB).where(StagingJokeDB.joke_uuid == high_quality.joke_uuid)).one()
            assert db_high.review_status == ReviewStatus.APPROVED

            db_low = session.exec(select(StagingJokeDB).where(StagingJokeDB.joke_uuid == low_quality.joke_uuid)).one()
            assert db_low.review_status == ReviewStatus.REJECTED

    def test_statistics_accuracy(self, cli_db, cli_batch, tmp_path):
        """Test that returned statistics match database changes."""
        # Create diverse jokes
        create_joke(cli_db, cli_batch, joke_uuid="approve-1", weighted_avg_funniness=4.8, total_ratings_count=20)
        create_joke(cli_db, cli_batch, joke_uuid="approve-2", weighted_avg_funniness=4.5, total_ratings_count=15)
        create_joke(cli_db, cli_batch, joke_uuid="reject-1", weighted_avg_funniness=1.2, total_ratings_count=10)
        create_joke(cli_db, cli_batch, joke_uuid="flag-1", weighted_avg_funniness=2.5, total_ratings_count=8)
        create_joke(cli_db, cli_batch, joke_uuid="skip-1", weighted_avg_funniness=3.5, total_ratings_count=3)

        config = tmp_path / "stats.yaml"
        config.write_text(
            """
policies:
  auto_approve:
    - name: high
      conditions:
        - weighted_avg_funniness: ">= 4.0"
        - total_ratings_count: ">= 10"
  auto_reject:
    - name: low
      conditions:
        - weighted_avg_funniness: "< 2.0"
        - total_ratings_count: ">= 5"
  flag_for_review:
    - name: borderline
      conditions:
        - weighted_avg_funniness: ">= 2.0"
        - weighted_avg_funniness: "< 3.0"
        - total_ratings_count: ">= 5"
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                cli_batch.import_id,
                "--config",
                str(config),
                "--staging-db",
                str(cli_db),
                "--yes",
            ],
        )

        assert result.exit_code == 0
        # Check statistics in output
        lines = result.output.split("\n")
        assert any("Approved" in line and "2" in line for line in lines)
        assert any("Rejected" in line and "1" in line for line in lines)
        assert any("Flagged" in line and "1" in line for line in lines)
        assert any("Skipped" in line and "1" in line for line in lines)

    def test_yes_flag_skips_confirmation(self, cli_db, cli_batch, tmp_path):
        """Test --yes flag skips confirmation prompt."""
        create_joke(cli_db, cli_batch, weighted_avg_funniness=4.5)

        config = tmp_path / "test.yaml"
        config.write_text(
            """
policies:
  auto_approve:
    - name: test
      conditions:
        - weighted_avg_funniness: ">= 4.0"
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                cli_batch.import_id,
                "--config",
                str(config),
                "--staging-db",
                str(cli_db),
                "--yes",
            ],
        )

        assert result.exit_code == 0
        assert "Continue?" not in result.output

    def test_empty_import_batch(self, cli_db, cli_batch, tmp_path):
        """Test handling of import batch with no pending jokes."""
        config = tmp_path / "test.yaml"
        config.write_text(
            """
policies:
  auto_approve:
    - name: test
      conditions:
        - language: "en"
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                cli_batch.import_id,
                "--config",
                str(config),
                "--staging-db",
                str(cli_db),
                "--yes",
            ],
        )

        assert result.exit_code == 0
        assert "No pending jokes" in result.output

    def test_review_notes_populated(self, cli_db, cli_batch, tmp_path):
        """Test that review_notes are populated correctly."""
        from joke_emporium.db.staging import get_staging_session

        joke = create_joke(cli_db, cli_batch, weighted_avg_funniness=4.8, total_ratings_count=20)

        config = tmp_path / "test.yaml"
        config.write_text(
            """
policies:
  auto_approve:
    - name: high_quality_policy
      conditions:
        - weighted_avg_funniness: ">= 4.5"
      reason: "Excellent score"
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                cli_batch.import_id,
                "--config",
                str(config),
                "--staging-db",
                str(cli_db),
                "--yes",
            ],
        )

        assert result.exit_code == 0

        # Verify review notes - query joke by UUID
        with next(get_staging_session()) as session:
            from sqlmodel import select

            db_joke = session.exec(select(StagingJokeDB).where(StagingJokeDB.joke_uuid == joke.joke_uuid)).one()
            assert db_joke.review_notes is not None
            assert "high_quality_policy" in db_joke.review_notes
            assert db_joke.reviewed_by == "policy_engine"

    def test_config_validation_warnings(self, cli_db, cli_batch, tmp_path):
        """Test that config validation warnings are displayed."""
        create_joke(cli_db, cli_batch)

        # Config with empty conditions
        config = tmp_path / "bad.yaml"
        config.write_text(
            """
policies:
  auto_approve:
    - name: empty
      conditions: []
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                cli_batch.import_id,
                "--config",
                str(config),
                "--staging-db",
                str(cli_db),
                "--yes",
            ],
        )

        assert "Warning" in result.output or "has no conditions" in result.output

    def test_exit_code_on_success(self, cli_db, cli_batch, tmp_path):
        """Test exit code is 0 on successful application."""
        create_joke(cli_db, cli_batch)

        config = tmp_path / "test.yaml"
        config.write_text(
            """
policies:
  auto_approve:
    - name: test
      conditions:
        - language: "en"
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                cli_batch.import_id,
                "--config",
                str(config),
                "--staging-db",
                str(cli_db),
                "--yes",
            ],
        )

        assert result.exit_code == 0
        assert "Successfully" in result.output or "Approved" in result.output

    def test_policy_breakdown_displayed(self, cli_db, cli_batch, tmp_path):
        """Test policy breakdown shows in output."""
        for _ in range(3):
            create_joke(cli_db, cli_batch, weighted_avg_funniness=4.8, total_ratings_count=20)

        for _ in range(2):
            create_joke(cli_db, cli_batch, weighted_avg_funniness=4.2, total_ratings_count=12)

        config = tmp_path / "test.yaml"
        config.write_text(
            """
policies:
  auto_approve:
    - name: excellent
      conditions:
        - weighted_avg_funniness: ">= 4.5"
        - total_ratings_count: ">= 15"
      priority: 10
    - name: good
      conditions:
        - weighted_avg_funniness: ">= 4.0"
        - total_ratings_count: ">= 10"
      priority: 5
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                cli_batch.import_id,
                "--config",
                str(config),
                "--staging-db",
                str(cli_db),
                "--yes",
            ],
        )

        assert result.exit_code == 0
        assert "Policy Breakdown" in result.output
        assert "excellent" in result.output
        assert "good" in result.output

    def test_mixed_results_output(self, cli_db, cli_batch, tmp_path):
        """Test output with mixed approve/reject/flag/skip results."""
        create_joke(cli_db, cli_batch, weighted_avg_funniness=4.8, total_ratings_count=20, maturity_rating="G")
        create_joke(cli_db, cli_batch, weighted_avg_funniness=1.2, total_ratings_count=10, maturity_rating="G")
        create_joke(cli_db, cli_batch, weighted_avg_funniness=3.0, total_ratings_count=5, maturity_rating="R")
        create_joke(cli_db, cli_batch, weighted_avg_funniness=3.0, total_ratings_count=2, maturity_rating="G")

        config = tmp_path / "test.yaml"
        config.write_text(
            """
policies:
  auto_approve:
    - name: high
      conditions:
        - weighted_avg_funniness: ">= 4.5"
  auto_reject:
    - name: low
      conditions:
        - weighted_avg_funniness: "< 2.0"
        - total_ratings_count: ">= 5"
  flag_for_review:
    - name: mature
      conditions:
        - maturity_rating: "R"
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                cli_batch.import_id,
                "--config",
                str(config),
                "--staging-db",
                str(cli_db),
                "--yes",
            ],
        )

        assert result.exit_code == 0
        assert "Approved" in result.output
        assert "Rejected" in result.output
        assert "Flagged" in result.output
        assert "Skipped" in result.output

    def test_duration_tracking(self, cli_db, cli_batch, tmp_path):
        """Test that duration is tracked and displayed."""
        create_joke(cli_db, cli_batch)

        config = tmp_path / "test.yaml"
        config.write_text(
            """
policies:
  auto_approve:
    - name: test
      conditions:
        - language: "en"
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "apply-policies",
                cli_batch.import_id,
                "--config",
                str(config),
                "--staging-db",
                str(cli_db),
                "--yes",
            ],
        )

        assert result.exit_code == 0
        assert "seconds" in result.output or "Duration" in result.output
