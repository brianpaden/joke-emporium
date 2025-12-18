# Contributing to Joke Emporium

Thank you for your interest in contributing to Joke Emporium! This guide will help you get started.

## Quick Start (5 Minutes)

### Windows
```powershell
.\setup.ps1
```

### Linux/macOS
```bash
./setup.sh
```

That's it! The setup script will:
- Check Python version (3.10+)
- Install uv package manager
- Install all dependencies
- Set up Git LFS
- Install pre-commit hooks
- Run tests to verify

## Manual Setup

If you prefer manual setup:

```bash
# 1. Install uv
pip install uv

# 2. Install dependencies
uv sync --extra dev --dev

# 3. Install pre-commit hooks
uv pip install pre-commit
uv run pre-commit install

# 4. Run tests
uv run pytest tests/
```

## Development Workflow

### Daily Commands

```bash
# Run tests
make test          # or: task test

# Run tests with coverage
make test-cov      # or: task test:coverage

# Format code
make format        # or: task format

# Lint code
make lint          # or: task lint

# Type check
uv run mypy src/

# View all commands
make help          # or: task --list
```

### Making Changes

1. **Create a branch** from `dev`:
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** with tests:
   - Write code in `src/joke_emporium/`
   - Add tests in `tests/`
   - Follow existing patterns

3. **Format and lint**:
   ```bash
   make format
   make lint
   ```

4. **Run tests**:
   ```bash
   make test-cov
   ```
   Coverage must be at least 80% (note: current coverage is 37%, working to improve)

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add feature X"
   ```
   Pre-commit hooks will automatically:
   - Format code with Ruff
   - Run linters
   - Check types with MyPy
   - Run quick tests

6. **Push and create PR**:
   ```bash
   git push origin feature/your-feature-name
   ```
   Create a pull request to `main` (not `dev`)

## Code Style

We use automated tools, so you don't need to memorize everything:

- **Line length**: 120 characters
- **Formatter**: Ruff (runs on save in VS Code)
- **Linter**: Ruff
- **Type checker**: MyPy (strict mode)
- **Docstrings**: Google style for public APIs

### Python Conventions

```python
from __future__ import annotations

import sys  # stdlib imports
from pathlib import Path

from pydantic import BaseModel  # third-party imports

from joke_emporium.models import Joke  # local imports


class MyClass:
    """Brief description.

    Longer description if needed.

    Args:
        param1: Description
        param2: Description

    Returns:
        Description of return value
    """
    def __init__(self, param1: str, param2: int) -> None:
        self.param1 = param1
        self.param2 = param2
```

## Testing

### Writing Tests

- Place tests in `tests/` mirroring the source structure
- Use descriptive test names: `test_import_creates_staging_jokes_with_correct_metadata()`
- Use fixtures from `tests/conftest.py`
- Test both happy path and error cases

### Running Tests

```bash
# All tests
make test

# With coverage
make test-cov

# Watch mode (re-run on file changes)
make test-watch

# Specific test file
uv run pytest tests/test_importers/test_base.py -v

# Specific test
uv run pytest tests/test_importers/test_base.py::test_function_name -v
```

### Test Fixtures

Use shared fixtures from `tests/conftest.py`:

```python
def test_import_jokes(staging_session, sample_jokes):
    """Test importing jokes to staging database."""
    # staging_session: SQLModel Session for staging DB
    # sample_jokes: List of sample Joke objects
    pass
```

## Project Structure

```
src/joke_emporium/
├── models/              # Pydantic data models
├── db/                  # Database layer (SQLModel)
├── importers/           # Import framework
├── validation/          # Validation rules (future)
└── utils/               # Utility functions

tests/
├── conftest.py         # Shared fixtures
├── fixtures/           # Test data
├── test_importers/     # Importer tests
└── test_db/            # Database tests
```

## Import Framework

### Creating a New Importer

1. **Create importer class**:

```python
# src/joke_emporium/importers/my_source.py
from joke_emporium.importers.base import BaseImporter
from joke_emporium.models import Joke

class MySourceImporter(BaseImporter):
    """Import jokes from My Source."""

    source_name = "my_source"
    source_url = "https://example.com/jokes"

    def download(self) -> Path:
        """Download data from source."""
        # Implement download logic
        pass

    def parse(self, data_path: Path) -> list[dict]:
        """Parse downloaded data."""
        # Implement parsing logic
        pass

    def transform(self, raw_joke: dict) -> Joke:
        """Transform raw data to Joke model."""
        # Implement transformation logic
        pass
```

2. **Add CLI command** in `src/joke_emporium/importers/cli.py`

3. **Add tests** in `tests/test_importers/test_my_source.py`

See `src/joke_emporium/importers/example_importer.py` for a complete example.

## Database System

### Two-Database Architecture

- **Staging** (`data/staging.db`): All imports go here first
- **Production** (`data/jokes.db`): Clean, validated jokes only

### Import Pipeline

```
Source → Download → Parse → Transform → Validate → Staging
  ↓
Review (approve/reject/flag)
  ↓
Deduplication
  ↓
Merge → Production
```

### Working with Databases

```python
from joke_emporium.db.session import get_staging_session
from joke_emporium.db.models import StagingJokeDB

with get_staging_session() as session:
    jokes = session.query(StagingJokeDB).all()
```

## Common Tasks

### Import Sample Data

```bash
# Import 100 jokes for testing
make import-taivop ARGS="--max-records 100"

# List imports
make import-list

# Inspect import
uv run python -m joke_emporium.importers.cli inspect <import-id>

# Approve and merge
uv run python -m joke_emporium.importers.cli approve-batch <import-id>
uv run python -m joke_emporium.importers.cli merge <import-id>
```

### Clean Up

```bash
# Clean Python caches
make clean

# Reset staging database (WARNING: deletes all data)
uv run python -m joke_emporium.importers.cli reset --yes
```

## VS Code Setup

If you use VS Code, recommended extensions will be suggested automatically. Accept them for the best experience:

- **Python** - Python language support
- **Pylance** - Fast language server
- **Ruff** - Formatting and linting
- **MyPy** - Type checking
- **Task** - Run Taskfile commands

Settings are pre-configured in `.vscode/settings.json`.

## Getting Help

- **Documentation**: Check `CLAUDE.md` for project overview
- **Examples**: See `src/joke_emporium/importers/example_importer.py`
- **Tests**: Look at existing tests for patterns
- **Issues**: Open a GitHub issue
- **Claude Commands**: Use custom commands in `.claude/commands/`

## Coverage Goals

**Current Status**: 37% coverage (below 80% target)

Priority modules needing tests:
- `importers/cli.py` (0%)
- `db/staging.py` (0%)
- `db/production.py` (0%)
- `db/operations.py` (0%)

See `.claude/commands/fix-coverage.md` for guidance on improving coverage.

## Pre-commit Hooks

Pre-commit hooks run automatically before each commit:

- Ruff formatting
- Ruff linting
- MyPy type checking
- Quick test run

To skip hooks (not recommended):
```bash
git commit --no-verify
```

To run hooks manually:
```bash
uv run pre-commit run --all-files
```

## Branching Strategy

- `main` - Stable release branch
- `dev` - Development branch
- `feature/*` - Feature branches (branch from `dev`)
- `fix/*` - Bug fix branches (branch from `dev`)

Create PRs to `main`, not `dev`.

## Questions?

Feel free to:
- Open an issue for bugs or feature requests
- Start a discussion for questions
- Check existing documentation in `docs/`

Thank you for contributing!
