#!/usr/bin/env bash
# Joke Emporium Shell Aliases
# Quick shortcuts for common commands
#
# Usage:
#   source aliases.sh
# Or add to your .bashrc/.zshrc:
#   source /path/to/joke-emporium/aliases.sh

# Color output
alias je-color='export PYTEST_CURRENT_TEST=1'

# Testing
alias je-test='uv run pytest tests/ -v'
alias je-test-f='uv run pytest tests/ -v --tb=short'
alias je-test-x='uv run pytest tests/ -v -x'  # Stop on first failure
alias je-cov='uv run pytest tests/ --cov=joke_emporium --cov-report=term-missing'
alias je-watch='uv run pytest tests/ -f --looponfail'

# Code Quality
alias je-lint='uv run ruff check .'
alias je-fix='uv run ruff check . --fix'
alias je-fmt='uv run ruff format .'
alias je-format='uv run ruff format . && uv run ruff check . --fix'
alias je-type='uv run mypy src/'
alias je-check='uv run ruff check . && uv run mypy src/'

# Import Commands
alias je-import='uv run python -m joke_emporium.importers.cli import'
alias je-list='uv run python -m joke_emporium.importers.cli list'
alias je-inspect='uv run python -m joke_emporium.importers.cli inspect'
alias je-approve='uv run python -m joke_emporium.importers.cli approve'
alias je-reject='uv run python -m joke_emporium.importers.cli reject'
alias je-merge='uv run python -m joke_emporium.importers.cli merge'
alias je-reset='uv run python -m joke_emporium.importers.cli reset'

# Quick Import Workflows
alias je-import-sample='uv run python -m joke_emporium.importers.cli import taivop --max-records 100'
alias je-import-1k='uv run python -m joke_emporium.importers.cli import taivop --max-records 1000'

# Git
alias je-status='git status'
alias je-diff='git diff'
alias je-log='git log --oneline -10'

# Environment
alias je-shell='uv run python'
alias je-py='uv run python'
alias je-activate='source .venv/bin/activate'

# Database
alias je-db-staging='sqlite3 data/staging.db'
alias je-db-prod='sqlite3 data/jokes.db'

# Cleanup
alias je-clean='rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage'
alias je-clean-all='rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage dist build *.egg-info'

# Development
alias je-dev='code .'
alias je-pre-commit='uv run pre-commit run --all-files'

# Information
alias je-help='echo "Joke Emporium Aliases:
Testing:
  je-test         - Run tests
  je-test-f       - Run tests (short traceback)
  je-test-x       - Stop on first failure
  je-cov          - Run with coverage
  je-watch        - Watch mode

Code Quality:
  je-lint         - Check code
  je-fix          - Fix issues
  je-format       - Format code
  je-type         - Type check
  je-check        - Lint + type check

Import:
  je-import       - Import command
  je-list         - List imports
  je-inspect      - Inspect import
  je-import-sample - Import 100 jokes

Utils:
  je-clean        - Clean caches
  je-dev          - Open in VS Code
  je-help         - This help
"'

echo "Joke Emporium aliases loaded! Type 'je-help' for available commands."
