# Joke Emporium Makefile
# Cross-platform alternative to Taskfile
# Usage: make <target>

.PHONY: help install test lint format clean dev doctor

# Variables
PYTHON := python
UV := uv
PYTEST := $(UV) run pytest
RUFF := $(UV) run ruff
PROJECT := joke_emporium

# Default target
help:
	@echo "Joke Emporium - Available Commands"
	@echo "==================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install        - Install project dependencies"
	@echo "  make doctor         - Check development environment"
	@echo ""
	@echo "Development:"
	@echo "  make test           - Run test suite"
	@echo "  make test-cov       - Run tests with coverage report"
	@echo "  make test-watch     - Run tests in watch mode"
	@echo "  make lint           - Check code quality"
	@echo "  make format         - Format code"
	@echo "  make clean          - Clean generated files"
	@echo ""
	@echo "Import:"
	@echo "  make import-taivop  - Import from taivop dataset"
	@echo "  make import-list    - List all import batches"
	@echo ""
	@echo "Database:"
	@echo "  make db-init        - Initialize databases"
	@echo "  make db-clean       - Clean staging database"

# Installation
install:
	@echo "Installing dependencies..."
	$(UV) sync --extra dev --dev
	@echo "Installing pre-commit hooks..."
	$(UV) pip install pre-commit
	$(UV) run pre-commit install
	@echo "Setup complete!"

# Development
update:
	@echo "Updating dependencies..."
	$(UV) sync --extra dev --dev

upgrade:
	@echo "Upgrading all dependencies..."
	$(UV) lock --upgrade

# Testing
test:
	@echo "Running test suite..."
	$(PYTEST) tests/ -v

test-cov:
	@echo "Running tests with coverage..."
	$(PYTEST) tests/ \
		--cov=$(PROJECT) \
		--cov-report=term-missing \
		--cov-report=html \
		--cov-report=xml \
		--cov-branch \
		--cov-fail-under=80

test-watch:
	@echo "Running tests in watch mode..."
	$(PYTEST) tests/ -f --looponfail

test-collect:
	@echo "Collecting tests..."
	$(PYTEST) --collect-only tests/

# Code Quality
lint:
	@echo "Linting code..."
	$(RUFF) check .

lint-fix:
	@echo "Fixing lint issues..."
	$(RUFF) check . --fix

format:
	@echo "Formatting code..."
	$(RUFF) format . --respect-gitignore
	$(RUFF) check . --fix --respect-gitignore

typecheck:
	@echo "Type checking..."
	$(UV) run mypy src/

# Cleaning
clean:
	@echo "Cleaning generated files..."
	@rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache
	@rm -rf dist build *.egg-info htmlcov .coverage coverage.xml
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Import commands
import-taivop:
	@echo "Importing from taivop dataset..."
	$(UV) run python -m $(PROJECT).importers.cli import taivop $(ARGS)

import-list:
	@echo "Listing import batches..."
	$(UV) run python -m $(PROJECT).importers.cli list

import-inspect:
	@echo "Inspecting import batch..."
	$(UV) run python -m $(PROJECT).importers.cli inspect $(ID)

import-approve:
	@echo "Approving staging joke..."
	$(UV) run python -m $(PROJECT).importers.cli approve $(ID)

import-reject:
	@echo "Rejecting staging joke..."
	$(UV) run python -m $(PROJECT).importers.cli reject $(ID) "$(REASON)"

import-merge:
	@echo "Merging approved jokes to production..."
	$(UV) run python -m $(PROJECT).importers.cli merge $(ID)

# Database commands
db-init:
	@echo "Initializing databases..."
	@mkdir -p data
	@echo "Databases initialized in data/"

db-clean:
	@echo "WARNING: This will delete the staging database!"
	$(UV) run python -m $(PROJECT).importers.cli reset --yes

# Development environment
dev:
	@echo "Starting development environment..."
	@echo "1. Opening VS Code..."
	@code . 2>/dev/null || echo "VS Code not found in PATH"
	@echo "2. Run 'make test-watch' in another terminal"

doctor:
	@echo "Checking development environment..."
	@echo ""
	@echo "Python:"
	@$(PYTHON) --version || echo "  ERROR: Python not found"
	@echo ""
	@echo "UV:"
	@$(UV) --version || echo "  ERROR: UV not found"
	@echo ""
	@echo "Git:"
	@git --version || echo "  ERROR: Git not found"
	@echo ""
	@echo "Git LFS:"
	@git lfs version 2>/dev/null || echo "  WARNING: Git LFS not found (optional)"
	@echo ""
	@echo "Virtual Environment:"
	@test -d .venv && echo "  .venv exists" || echo "  WARNING: .venv not found - run 'make install'"
	@echo ""
	@echo "Dependencies:"
	@$(UV) pip list 2>/dev/null | head -5 || echo "  Run 'make install' first"

# Quick start
quick-start:
	@echo "Joke Emporium Quick Start Guide"
	@echo "==============================="
	@echo ""
	@echo "1. Setup:     make install"
	@echo "2. Test:      make test"
	@echo "3. Import:    make import-taivop ARGS='--max-records 100'"
	@echo "4. Format:    make format"
	@echo "5. Help:      make help"

# Aliases for convenience
t: test
tc: test-cov
tw: test-watch
l: lint
f: format
c: clean
i: install
