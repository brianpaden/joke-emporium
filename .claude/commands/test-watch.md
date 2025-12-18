# Run Tests in Watch Mode

Run the test suite continuously, re-running tests when files change for fast feedback during development.

## Options

Since the project uses pytest, implement watch mode using one of these approaches:

1. **pytest-watch** (if available):
   ```
   uv run ptw tests/ -- -v
   ```

2. **pytest with looponfail** (built-in):
   ```
   uv run pytest tests/ -f --looponfail
   ```

3. **Manual implementation**: Use a file watcher to run tests on changes

## Configuration

- Run tests in verbose mode
- Show failures immediately
- Only re-run failed tests until they pass
- Then run full suite

## What to Display

- Clear indication when tests are running
- Last run timestamp
- Pass/fail status
- Coverage summary (if available)
- Instructions for stopping (Ctrl+C)

## Helpful for

- TDD (Test-Driven Development)
- Refactoring with confidence
- Rapid iteration on fixes
