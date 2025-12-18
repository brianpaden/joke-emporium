# Improve Test Coverage

Analyze current test coverage and suggest specific improvements to reach the 80% threshold.

## Current Situation

The project requires 80% coverage but currently has ~37%. Key uncovered modules:
- `importers/cli.py` - 0% coverage
- `db/staging.py` - 0% coverage
- `db/production.py` - 0% coverage
- `db/operations.py` - 0% coverage

## Analysis Steps

1. Run coverage report to see current state:
   ```
   uv run pytest tests/ --cov=joke_emporium --cov-report=term-missing
   ```

2. Identify the highest-impact modules to test (most lines, most critical)

3. Analyze existing test patterns in `tests/conftest.py` and `tests/test_importers/`

4. Suggest specific test cases for uncovered code:
   - Happy path scenarios
   - Error handling
   - Edge cases
   - Integration points

## Prioritization

Focus on:
1. Core business logic (import pipeline, staging, merge)
2. Database operations
3. CLI commands (can use click.testing.CliRunner)
4. Error handling paths

## Output

Provide:
- Current coverage breakdown by module
- Specific test cases to add (with examples)
- Estimated coverage gain per module
- Priority order for implementation
- Code templates for suggested tests
