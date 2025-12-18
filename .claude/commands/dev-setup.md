# Development Environment Setup

Set up a complete development environment for a new contributor to the Joke Emporium project.

## Steps to Execute

1. Check Python version (require 3.10+)
2. Check if `uv` is installed, install if missing
3. Run `uv sync --extra dev --dev` to install dependencies
4. Check if git-lfs is installed and initialized
5. Install pre-commit hooks with `uv run pre-commit install`
6. Run test suite to verify: `uv run pytest tests/ -v`
7. Display helpful next steps for the developer

## What to Report

- Python version found
- Whether uv was already installed or newly installed
- Dependency installation success
- Git LFS status
- Pre-commit hooks installation success
- Test results (number passed/failed)
- Any errors encountered with troubleshooting suggestions

## Next Steps to Show Developer

After successful setup, tell them:
- How to run tests: `task test` or `uv run pytest tests/`
- How to format code: `task format`
- How to import sample data: `task import:taivop -- --max-records 100`
- Where to find documentation: `CLAUDE.md` and `README.md`
- Available commands: `task --list`
