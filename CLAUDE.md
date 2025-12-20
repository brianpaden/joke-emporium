# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Joke Emporium is a comprehensive categorized dataset of jokes with rich metadata and scientific annotations. The project provides:
- Structured Pydantic models for joke data with full type hints
- Multi-dimensional categorization (topics, structure, linguistic mechanisms)
- Multi-source ratings with automatic normalization to 1-5 scale
- Import framework for ingesting jokes from external sources
- Two-database system (staging + production) for data quality control
- SQLite backend using SQLModel (Pydantic + SQLAlchemy)

**Target:** Python 3.10+, currently developing on Python 3.13

## Essential Commands

### Development Setup
```bash
# Initialize development environment
uv sync

# Install with full setup (git lfs, tools)
task install
```

### Testing
```bash
# Run all tests with basic coverage
uv run pytest tests/

# Run with detailed coverage report (requires 80%+ coverage)
task test:coverage

# Run specific test module
uv run pytest tests/test_importers/ -v

# Run single test
uv run pytest tests/test_importers/test_base.py::test_specific_function -v

# Collect tests without running
task test:collect
```

### Code Quality
```bash
# Lint the codebase
task lint
# OR
uv run ruff check .

# Format code (runs ruff format + ruff check --fix)
task format

# Type checking (strict mypy)
uv run mypy src/
```

### Import Workflow
```bash
# Import jokes from taivop dataset
uv run python -m joke_emporium.importers.cli import taivop --max-records 1000

# List all import batches
task import:list

# Inspect staging jokes for an import batch
uv run python -m joke_emporium.importers.cli inspect <import-id>

# Approve a staging joke for production
uv run python -m joke_emporium.importers.cli approve <staging-id>

# Reject a staging joke
uv run python -m joke_emporium.importers.cli reject <staging-id> "reason"

# Apply policies to auto-approve/reject staging jokes
uv run python -m joke_emporium.importers.cli apply-policies <import-id>

# Preview policy application (dry-run)
uv run python -m joke_emporium.importers.cli apply-policies <import-id> --dry-run

# Use custom policy configuration
uv run python -m joke_emporium.importers.cli apply-policies <import-id> --config config/policies/strict.yaml

# Auto-confirm without prompt
uv run python -m joke_emporium.importers.cli apply-policies <import-id> --yes

# Merge approved jokes to production
uv run python -m joke_emporium.importers.cli merge <import-id>

# Delete an import batch
uv run python -m joke_emporium.importers.cli delete <import-id> --yes

# Reset/clear the staging database (WARNING - deletes all data)
uv run python -m joke_emporium.importers.cli reset --yes
```

### Database Migrations
```bash
# Alembic is configured but migrations should be handled through SQLModel
# Production database: data/jokes.db
# Staging database: data/staging.db
```

### Experiments
```bash
# Deduplication research and data exploration scripts
uv run python experiments/scripts/find_natural_duplicates.py
uv run python experiments/scripts/test_normalization.py
uv run python experiments/scripts/benchmark_similarity.py
```

## Architecture

### Directory Structure
```
src/joke_emporium/
├── models/              # Pydantic data models
│   ├── joke.py         # Main Joke model
│   ├── enums.py        # 40+ categories, structure types, linguistic mechanisms
│   ├── content.py      # JokeElement (setup, punchline, etc.)
│   ├── ratings.py      # RatingSource with auto-normalization
│   ├── author.py       # Author model
│   ├── metadata.py     # JokeMetadata
│   ├── gtvh.py         # GTVHAnnotation (academic humor theory)
│   └── collection.py   # Collection model for joke datasets
├── db/                 # Database layer (SQLModel)
│   ├── models/         # SQLModel database models
│   │   ├── joke.py           # JokeDB with cached fields
│   │   ├── author.py         # AuthorDB
│   │   ├── rating.py         # RatingSourceDB, VoteDB
│   │   ├── associations.py   # Many-to-many link tables
│   │   ├── staging.py        # StagingJokeDB, ImportBatchDB
│   │   └── provenance.py     # ProvenanceDB for import tracking
│   ├── session.py      # Database session management
│   ├── operations.py   # Core CRUD operations
│   ├── staging.py      # Staging database operations
│   ├── production.py   # Production database operations
│   ├── merge.py        # Merge staging → production
│   └── deduplication.py # Hash-based duplicate detection
├── importers/          # Import framework
│   ├── base.py         # BaseImporter abstract class
│   ├── models.py       # Import metadata models
│   ├── policies.py     # Policy engine for auto-approval/rejection
│   ├── cli.py          # CLI interface for import commands
│   ├── taivop.py       # TaivopImporter (195k jokes)
│   └── example_importer.py # Reference implementation
├── validation/         # Validation rules (future)
├── io/                 # I/O helpers (future)
└── utils/              # Utility functions

tests/
├── conftest.py         # Shared pytest fixtures
├── fixtures/           # Test data fixtures
├── test_importers/     # Importer tests (77 unit + 16 integration = 93 tests)
└── test_db/            # Database operation tests

experiments/            # Research scripts
├── scripts/            # Analysis and benchmarking
└── output/             # Generated results (gitignored)

docs/                   # Documentation
├── DATABASE.md         # Database schema and operations
├── IMPORT_PLAN.md      # Complete 4-sprint import plan
├── HANDOFF_SPRINT*.md  # Sprint handoff documents
├── TESTING_STANDARDS.md # Testing guidelines
└── POLICY_COOKBOOK.md  # Policy engine guide and examples

config/                 # Configuration files
├── import_policies.yaml    # Default balanced policy
└── policies/               # Specialized policy configurations
    ├── strict.yaml         # Family-friendly, high-quality only
    ├── permissive.yaml     # Quality-based, accepts most content
    └── nsfw_only.yaml      # Adult content focused
```

### Two-Database System

**Staging Database** (`data/staging.db`):
- Receives all imports through `StagingJokeDB` and `ImportBatchDB` tables
- Tracks provenance: source, import batch, original JSON
- Review workflow: pending → approved/rejected/duplicate → merged
- Allows validation before production

**Production Database** (`data/jokes.db`):
- Clean, validated jokes only through `JokeDB` table
- Normalized schema with cached computed fields
- Related tables: `AuthorDB`, `RatingSourceDB`, `VoteDB`, `ProvenanceDB`
- Many-to-many associations for categories and mechanisms

**Import Pipeline:**
```
Source → Download → Parse → Transform → Validate → Staging → Review → Dedup → Merge → Production
```

### Key Data Models

**Joke Model** (`models/joke.py`):
- Core Pydantic model with rich validation
- Fields: id (UUID), version, content (list of JokeElements), categories, structure, mechanisms, maturity_rating, tags, flags, ratings, metadata, gtvh (optional)
- Supports 40+ topic categories, 10+ structure types, 25+ linguistic mechanisms

**JokeDB Model** (`db/models/joke.py`):
- SQLModel version for database storage
- Cached computed fields: `weighted_avg_funniness`, `weighted_avg_quality`, `total_ratings_count`, `text_preview`
- JSON storage for complex fields (content, tags, flags, gtvh)
- Many-to-many relationships via association tables

**Rating Normalization:**
- All ratings automatically normalized to 1-5 scale regardless of source scale
- Supports Reddit (0-1), IMDB (1-10), 5-star systems, etc.
- Weighted averaging across multiple sources

### Import Framework

**BaseImporter** (`importers/base.py`):
- Abstract base class defining the import pipeline
- Subclasses must implement: `download()`, `parse()`, `transform()`
- Automatic validation, staging, and progress tracking
- Built-in error handling and recovery

**Current Importers:**
- `TaivopImporter` - Imports ~195k jokes from taivop/joke-dataset (fully implemented)
- `ExampleImporter` - Reference implementation for new importers

**Creating a New Importer:**
1. Extend `BaseImporter` in a new file
2. Define `source_name` and `source_url` class attributes
3. Implement `download()`, `parse()`, `transform()` methods
4. Add CLI command in `importers/cli.py`
5. Test with `uv run python src/joke_emporium/importers/your_importer.py`

### Policy Engine

**Policy-Based Auto-Approval** (`importers/policies.py`):
- Declarative YAML-based policies for automated joke review
- Supports 10 operators: ==, !=, >, >=, <, <=, in, not_in, is_null, is_not_null
- Nested field access: flags.nsfw, engagement.upvotes, metadata.source_platform
- Actions: approve, reject, flag for manual review
- First-match-wins precedence with priority ordering

**Configuration Files:**
- `config/import_policies.yaml` - Default balanced policy
- `config/policies/strict.yaml` - Family-friendly, high-quality only
- `config/policies/permissive.yaml` - Quality-based, accepts most content
- `config/policies/nsfw_only.yaml` - Adult content focused

**Benefits:**
- Reduces manual review time from 270 hours to ~10 hours (96% reduction for 195k jokes)
- Consistent, reproducible decision-making
- Customizable policies for different platforms and use cases
- Dry-run mode for testing policies before applying

**See:** `docs/POLICY_COOKBOOK.md` for comprehensive examples and best practices

### Deduplication Strategy

Implemented in `db/deduplication.py`, validated with experiments on 208k real jokes:

**Text Normalization:**
- Unicode normalization (NFC) + casefold for better unicode handling
- Line break normalization (\\n → space)
- Ellipsis preservation (23% of jokes have timing markers)
- Punctuation removal (preserves apostrophes for contractions)
- Whitespace normalization

**Duplicate Detection:**
- Primary: Hash-based exact match (100% recall, 3.6M comparisons/sec)
- Secondary: Levenshtein distance for variations (68.5% recall on real data)
- Marks duplicates with `ReviewStatus.DUPLICATE` and tracks similarity score

**Performance:** 3.7% natural duplication rate in 208k joke corpus

## Testing Standards

**Coverage Requirements:**
- Minimum 80% code coverage (`task test:coverage` enforces this)
- Current status: 99% coverage achieved

**Fixture Philosophy:**
- Use real data samples from `tests/fixtures/real_joke_samples.json`
- Edge cases in `tests/fixtures/edge_case_samples.json`
- Shared fixtures in `tests/conftest.py` (staging_session, production_session, etc.)

**Test Organization:**
- `tests/test_importers/` - Import framework tests (22 tests)
- `tests/test_db/` - Database operation tests (10+ tests)
- Use descriptive test names: `test_import_creates_staging_jokes_with_correct_metadata()`

**Running Tests:**
- Always run full suite before commits: `task test`
- Use `pytest -v` for verbose output
- Use `pytest -k pattern` to run specific tests
- Use `pytest --lf` to run last failed tests

## Code Style and Conventions

**Python Style:**
- Line length: 120 characters (enforced by ruff)
- Target version: Python 3.13
- Strict type hints (enforced by mypy)
- Docstrings: Google-style for public APIs

**Ruff Configuration:**
- Enabled: E (pycodestyle errors), W (warnings), F (pyflakes), I (isort), B (bugbear), C4 (comprehensions), UP (pyupgrade)
- Disabled: E501 (line too long - handled by formatter)

**Database Conventions:**
- Pydantic models in `models/` for API/validation
- SQLModel models in `db/models/` for database storage
- Use `{ModelName}DB` suffix for database models (e.g., `JokeDB`, `AuthorDB`)
- Always use indexed fields for foreign keys and UUIDs
- JSON storage for complex nested structures

**Import Conventions:**
- Absolute imports from `joke_emporium.*`
- Group imports: stdlib → third-party → local
- Use `from __future__ import annotations` for forward references

## Current Sprint Status

**Sprint 3 Complete (December 2025):**
- ✅ Production database integration
- ✅ Review workflow (approve/reject/duplicate)
- ✅ Deduplication logic with real data validation
- ✅ Merge staging → production with provenance tracking
- ✅ Policy engine for automated review
- ✅ CLI commands for full workflow
- ✅ Comprehensive tests (99% coverage)

**What Works:**
- Full import pipeline from taivop dataset (195k jokes)
- Staging and review workflow
- Policy-based auto-approval/rejection (96% time savings)
- Hash-based deduplication with 100% recall
- Production merge with provenance tracking
- CLI for all operations

**Next Steps (Future):**
- Additional data sources (Reddit API, CleanComedy, HAHA corpus)
- Web scraping tools
- Statistical analysis tools
- Query API for jokes

## Key Documentation Files

- `README.md` - Quick start and overview
- `README_IMPORT_FRAMEWORK.md` - Import framework guide
- `docs/DATABASE.md` - Database schema and operations
- `docs/IMPORT_PLAN.md` - Complete 4-sprint plan
- `docs/HANDOFF_SPRINT3.md` - Current sprint handoff
- `docs/TESTING_STANDARDS.md` - Testing guidelines
- `docs/POLICY_COOKBOOK.md` - Policy engine guide and examples
- `docs/SCHEMA_OUTLINE.md` - Complete schema documentation
- `docs/RESEARCH_CATEGORIZATION.md` - Scientific humor categorization
- `experiments/README.md` - Deduplication research

## Scientific Background

The schema is informed by academic humor research:
- **GTVH** (General Theory of Verbal Humor) - Attardo & Raskin
- **Chalmers Cognitive Taxonomy** - 4 main joke types
- **Linguistic Analysis** - Phonological, semantic, structural features
- Real-world datasets analyzed: Reddit (195k), Stupidstuff (3.7k), Wocka (10k)

## Common Gotchas

1. **Database Sessions:** Always use context managers for sessions (`with get_staging_session() as session:`)
2. **UUID vs ID:** Models use `id` field for UUID string, database uses auto-increment `id` and separate `joke_uuid`
3. **Rating Normalization:** Automatically handled by `RatingSource.normalized_avg_funniness` computed field
4. **Windows Paths:** Use `Path` objects for cross-platform compatibility
5. **Test Database:** Tests use in-memory SQLite (`:memory:`) with automatic cleanup
6. **Coverage Threshold:** 80% minimum enforced by `task test:coverage`

## Development Workflow

1. Create/checkout feature branch from `dev`
2. Make changes with tests
3. Run `task format` to format and lint
4. Run `task test:coverage` to ensure tests pass with coverage
5. Commit changes
6. Create PR to `main` (not `dev`)
7. Merge after review

## Package Management

Using **uv** (modern Python package manager):
- `uv sync` - Install/sync dependencies
- `uv run <command>` - Run command in virtual environment
- `uv pip install <package>` - Add one-off dependency
- `uv lock --upgrade` - Upgrade all dependencies

Dependencies defined in `pyproject.toml`:
- Core: pydantic, sqlmodel, alembic, httpx, aiofiles, click, rich
- Dev: pytest, pytest-cov, ruff, mypy, pytest-sugar, pymarkdownlnt
