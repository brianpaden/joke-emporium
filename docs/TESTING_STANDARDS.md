# Testing Standards

## Overview

This document defines the testing standards and best practices for the Joke Emporium project. Following these standards ensures code quality, maintainability, and reliability.

## Core Principles

### 1. Test Framework

- **Framework**: Python `unittest` module for writing tests
- **Test Runner**: `pytest` for executing tests
- **Location**: All tests are located in `./tests/` directory

### 2. Test Philosophy

> **Tests define the truth. Code must conform to tests, not the other way around.**

- Tests verify **desired behavior** and **requirements**
- Failing tests indicate bugs in the code, not the tests
- **NEVER modify tests to make them pass** - fix the underlying issue instead
- When tests fail:
  1. Investigate the root cause
  2. Document the issue if it cannot be fixed immediately
  3. Fix the code or create a bug ticket
  4. Only modify tests if requirements have legitimately changed

### 3. Code Quality Standards

- All code follows **PEP 8** style guide
- Type hints required for all functions and methods
- Docstrings required for all public APIs
- Code is linted with `task lint`
- Code is formatted with `task format`

## Test Execution

### Running Tests

```bash
# Run all tests
task test

# Run tests with coverage report
task test:coverage

# Run only test collection (verify test discovery)
task test:collect

# Run specific test file
pytest tests/test_models.py

# Run specific test class
pytest tests/test_models.py::TestJoke

# Run specific test method
pytest tests/test_models.py::TestJoke::test_create_valid_joke

# Run with verbose output
pytest -v tests/

# Run with debug output
pytest -vv tests/

# Run and stop at first failure
pytest -x tests/
```

### Code Quality Checks

```bash
# Lint code (check for issues)
task lint

# Format code (auto-fix formatting)
task format
```

## Test Structure

### Directory Layout

```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures and configuration
├── test_models/
│   ├── __init__.py
│   ├── test_joke.py
│   ├── test_author.py
│   ├── test_ratings.py
│   └── test_enums.py
├── test_db/
│   ├── __init__.py
│   ├── test_session.py
│   ├── test_operations.py
│   └── test_models/
│       ├── test_joke_db.py
│       └── test_author_db.py
├── test_importers/
│   ├── __init__.py
│   ├── test_base.py
│   ├── test_taivop.py
│   └── test_validation.py
├── test_validation/
│   ├── __init__.py
│   ├── test_rules.py
│   └── test_deduplication.py
└── fixtures/
    ├── sample_jokes.json
    ├── taivop_sample.json
    └── test_data.py
```

### File Naming Conventions

- Test files: `test_*.py`
- Test classes: `Test*` (e.g., `TestJoke`, `TestDatabase`)
- Test functions: `test_*` (e.g., `test_create_joke`, `test_invalid_rating`)
- Fixture files: Place in `tests/fixtures/`
- Shared utilities: `tests/conftest.py` or `tests/utils.py`

## Test Categories

### Unit Tests

Test individual functions, methods, or classes in isolation.

**Characteristics:**
- Fast execution (< 1ms per test typically)
- No external dependencies (database, network, filesystem)
- Use mocks/stubs for dependencies
- Focus on single unit of code

**Example:**
```python
import unittest
from joke_emporium.models.joke import Joke
from joke_emporium.models.content import JokeElement
from joke_emporium.models.enums import ElementType, MaturityRating


class TestJokeModel(unittest.TestCase):
    """Unit tests for Joke model."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_content = [
            JokeElement(type=ElementType.SETUP, text="Why did the chicken cross the road?"),
            JokeElement(type=ElementType.PUNCHLINE, text="To get to the other side!")
        ]

    def test_create_valid_joke(self):
        """Test creating a valid joke with minimal required fields."""
        joke = Joke(
            id="test-uuid-1",
            content=self.valid_content,
            metadata={
                "language": "en",
                "added_date": "2024-01-01T00:00:00Z",
                "last_modified": "2024-01-01T00:00:00Z"
            }
        )
        self.assertEqual(joke.id, "test-uuid-1")
        self.assertEqual(len(joke.content), 2)
        self.assertEqual(joke.maturity_rating, MaturityRating.G)

    def test_empty_content_raises_error(self):
        """Test that empty content raises ValidationError."""
        with self.assertRaises(ValidationError):
            Joke(
                id="test-uuid-2",
                content=[],  # Invalid: empty content
                metadata={...}
            )

    def test_weighted_avg_funniness_no_ratings(self):
        """Test weighted_avg_funniness returns None when no ratings exist."""
        joke = Joke(id="test-uuid-3", content=self.valid_content, metadata={...})
        self.assertIsNone(joke.weighted_avg_funniness)
```

### Integration Tests

Test interaction between multiple components.

**Characteristics:**
- May use test database
- Test component interactions
- Slower than unit tests
- Use real implementations when practical

**Example:**
```python
import unittest
from joke_emporium.db.session import init_db, get_session
from joke_emporium.db.operations import save_joke, get_joke_by_uuid
from joke_emporium.models.joke import Joke


class TestDatabaseOperations(unittest.TestCase):
    """Integration tests for database operations."""

    @classmethod
    def setUpClass(cls):
        """Set up test database once for all tests."""
        init_db("sqlite:///:memory:")  # In-memory database

    def setUp(self):
        """Set up fresh session for each test."""
        self.session = next(get_session())

    def tearDown(self):
        """Clean up session after each test."""
        self.session.rollback()
        self.session.close()

    def test_save_and_retrieve_joke(self):
        """Test saving a joke and retrieving it by UUID."""
        joke = self._create_test_joke()

        # Save joke
        joke_db = save_joke(self.session, joke)
        self.assertIsNotNone(joke_db.id)

        # Retrieve joke
        retrieved = get_joke_by_uuid(self.session, joke.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, joke.id)
        self.assertEqual(len(retrieved.content), len(joke.content))

    def _create_test_joke(self) -> Joke:
        """Helper method to create a test joke."""
        # ... create and return joke
```

### End-to-End Tests

Test complete workflows from start to finish.

**Example:**
```python
class TestImportWorkflow(unittest.TestCase):
    """End-to-end tests for import workflow."""

    def test_complete_import_pipeline(self):
        """Test complete import from download to merge."""
        # 1. Download data
        # 2. Parse and transform
        # 3. Save to staging
        # 4. Validate
        # 5. Merge to production
        # 6. Verify final state
```

## Coverage Requirements

### Positive Cases (Happy Path)

Test that code works correctly with valid inputs.

**Example:**
```python
def test_valid_rating_source(self):
    """Test creating RatingSource with valid data."""
    rating = RatingSource(
        source="reddit",
        min_rating=1.0,
        max_rating=5.0,
        total_ratings=100,
        avg_funniness=3.5
    )
    self.assertEqual(rating.normalized_avg_funniness, 0.625)  # (3.5-1)/(5-1)
```

### Negative Cases (Error Handling)

Test that code properly handles invalid inputs and error conditions.

**Example:**
```python
def test_invalid_rating_range(self):
    """Test that invalid rating range raises ValueError."""
    with self.assertRaises(ValueError):
        RatingSource(
            source="reddit",
            min_rating=5.0,
            max_rating=1.0,  # Invalid: max < min
            total_ratings=100,
            avg_funniness=3.5
        )

def test_negative_total_ratings(self):
    """Test that negative total_ratings raises ValidationError."""
    with self.assertRaises(ValidationError):
        RatingSource(
            source="reddit",
            min_rating=1.0,
            max_rating=5.0,
            total_ratings=-1,  # Invalid: negative
            avg_funniness=3.5
        )
```

### Edge Cases (Boundary Conditions)

Test boundary values and special conditions.

**Example:**
```python
def test_zero_ratings(self):
    """Test handling of zero ratings."""
    rating = RatingSource(
        source="reddit",
        min_rating=1.0,
        max_rating=5.0,
        total_ratings=0,  # Edge case: zero ratings
        avg_funniness=0.0
    )
    # Verify behavior with zero ratings

def test_very_long_joke_text(self):
    """Test joke with extremely long text."""
    long_text = "A" * 10000  # 10k characters
    joke = Joke(
        id="test-uuid",
        content=[JokeElement(type=ElementType.BODY, text=long_text)],
        metadata={...}
    )
    self.assertEqual(len(joke.text_preview), 100)  # Should truncate

def test_unicode_content(self):
    """Test joke with unicode characters."""
    joke = Joke(
        id="test-uuid",
        content=[JokeElement(type=ElementType.BODY, text="Why did 👨‍💻 quit? 🐛!")],
        metadata={...}
    )
    self.assertIn("👨‍💻", joke.content[0].text)

def test_empty_string_vs_none(self):
    """Test distinction between empty string and None."""
    # Test both empty string and None for optional fields
    pass

def test_max_list_size(self):
    """Test behavior with maximum list sizes."""
    # Test with large number of categories, tags, etc.
    pass
```

## Test Structure Best Practices

### Use unittest.TestCase

```python
import unittest


class TestMyFeature(unittest.TestCase):
    """Tests for MyFeature.

    This test class covers:
    - Valid input handling
    - Invalid input handling
    - Edge cases
    """

    @classmethod
    def setUpClass(cls):
        """Run once before all tests in this class.

        Use for expensive setup that can be shared across tests.
        """
        pass

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests in this class."""
        pass

    def setUp(self):
        """Run before each test method.

        Use for test-specific setup.
        """
        pass

    def tearDown(self):
        """Run after each test method.

        Use for cleanup.
        """
        pass

    def test_specific_behavior(self):
        """Test that specific behavior works correctly.

        Each test should:
        1. Have a clear, descriptive name
        2. Have a docstring explaining what it tests
        3. Follow Arrange-Act-Assert pattern
        4. Test one specific behavior
        """
        # Arrange: Set up test data
        data = {"key": "value"}

        # Act: Execute the code being tested
        result = process_data(data)

        # Assert: Verify the outcome
        self.assertEqual(result, expected_value)
```

### Assertion Methods

Use appropriate assertion methods for clarity:

```python
# Equality
self.assertEqual(a, b)
self.assertNotEqual(a, b)

# Identity
self.assertIs(a, b)
self.assertIsNot(a, b)

# Truthiness
self.assertTrue(x)
self.assertFalse(x)

# None
self.assertIsNone(x)
self.assertIsNotNone(x)

# Membership
self.assertIn(item, container)
self.assertNotIn(item, container)

# Type checking
self.assertIsInstance(obj, SomeClass)
self.assertNotIsInstance(obj, SomeClass)

# Exceptions
with self.assertRaises(ValueError):
    dangerous_function()

with self.assertRaises(ValueError) as cm:
    dangerous_function()
self.assertIn("expected message", str(cm.exception))

# Warnings
with self.assertWarns(DeprecationWarning):
    deprecated_function()

# Approximate equality (floats)
self.assertAlmostEqual(a, b, places=7)
self.assertNotAlmostEqual(a, b, places=7)

# Collections
self.assertCountEqual(list1, list2)  # Same elements, any order
self.assertListEqual(list1, list2)   # Exact order
self.assertDictEqual(dict1, dict2)
self.assertSetEqual(set1, set2)

# Greater/Less
self.assertGreater(a, b)
self.assertGreaterEqual(a, b)
self.assertLess(a, b)
self.assertLessEqual(a, b)

# Regex
self.assertRegex(text, pattern)
self.assertNotRegex(text, pattern)
```

## Fixtures and Test Data

### Using conftest.py

```python
# tests/conftest.py
import pytest
from joke_emporium.models.joke import Joke
from joke_emporium.models.content import JokeElement
from joke_emporium.models.enums import ElementType


@pytest.fixture
def sample_joke():
    """Create a sample joke for testing."""
    return Joke(
        id="fixture-uuid-1",
        content=[
            JokeElement(type=ElementType.SETUP, text="Why did the chicken cross the road?"),
            JokeElement(type=ElementType.PUNCHLINE, text="To get to the other side!")
        ],
        metadata={
            "language": "en",
            "added_date": "2024-01-01T00:00:00Z",
            "last_modified": "2024-01-01T00:00:00Z",
            "verified": False
        }
    )


@pytest.fixture
def test_db():
    """Create an in-memory test database."""
    from joke_emporium.db.session import init_db, get_session

    init_db("sqlite:///:memory:")
    session = next(get_session())

    yield session

    session.close()
```

### Using Fixtures in Tests

```python
# With pytest fixtures (automatic)
def test_using_fixture(sample_joke):
    """Test using pytest fixture."""
    assert sample_joke.id == "fixture-uuid-1"


# With unittest (manual)
class TestWithFixture(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures manually."""
        self.sample_joke = create_sample_joke()

    def test_something(self):
        """Test using self.sample_joke."""
        self.assertEqual(self.sample_joke.id, "fixture-uuid-1")
```

### External Test Data

```python
# tests/fixtures/test_data.py
SAMPLE_JOKES = [
    {
        "id": "test-1",
        "content": [{"type": "body", "text": "Why did the programmer quit?"}],
        # ... more fields
    },
    # ... more jokes
]


# Load from JSON
import json
from pathlib import Path

def load_test_jokes():
    """Load test jokes from JSON file."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_jokes.json"
    with open(fixture_path) as f:
        return json.load(f)
```

## Mocking and Patching

### When to Mock

- External API calls (HTTP requests)
- Database operations (in unit tests)
- File system operations
- Time-dependent code
- Random number generation
- Expensive computations

### Using unittest.mock

```python
from unittest.mock import Mock, MagicMock, patch, call


class TestWithMocks(unittest.TestCase):

    def test_mock_function(self):
        """Test using a mock object."""
        mock_func = Mock(return_value=42)
        result = mock_func(1, 2, 3)

        self.assertEqual(result, 42)
        mock_func.assert_called_once_with(1, 2, 3)

    @patch('joke_emporium.importers.taivop.httpx.get')
    def test_download_with_mock(self, mock_get):
        """Test download with mocked HTTP request."""
        # Configure mock
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = '{"jokes": []}'

        # Execute
        result = download_jokes()

        # Verify
        mock_get.assert_called_once()
        self.assertEqual(result, {"jokes": []})

    def test_multiple_calls(self):
        """Test function called multiple times."""
        mock_func = Mock()
        mock_func.side_effect = [1, 2, 3]

        self.assertEqual(mock_func(), 1)
        self.assertEqual(mock_func(), 2)
        self.assertEqual(mock_func(), 3)

        self.assertEqual(mock_func.call_count, 3)

    @patch('joke_emporium.db.operations.datetime')
    def test_time_dependent(self, mock_datetime):
        """Test code that depends on current time."""
        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)

        # Test code that uses datetime.now()
        result = create_joke_with_timestamp()

        self.assertEqual(result.metadata.added_date, datetime(2024, 1, 1, 12, 0, 0))
```

## Parameterized Tests

### Using unittest

```python
from parameterized import parameterized


class TestRatingNormalization(unittest.TestCase):

    @parameterized.expand([
        # (min, max, value, expected_normalized)
        (1, 5, 1, 0.0),      # Minimum
        (1, 5, 5, 1.0),      # Maximum
        (1, 5, 3, 0.5),      # Middle
        (0, 10, 5, 0.5),     # Different scale
        (1, 10, 5.5, 0.5),   # Float values
    ])
    def test_normalize_rating(self, min_val, max_val, value, expected):
        """Test rating normalization with various inputs."""
        rating = RatingSource(
            source="test",
            min_rating=min_val,
            max_rating=max_val,
            total_ratings=1,
            avg_funniness=value
        )
        self.assertAlmostEqual(rating.normalized_avg_funniness, expected, places=5)
```

### Using pytest

```python
import pytest


@pytest.mark.parametrize("min_val,max_val,value,expected", [
    (1, 5, 1, 0.0),
    (1, 5, 5, 1.0),
    (1, 5, 3, 0.5),
    (0, 10, 5, 0.5),
    (1, 10, 5.5, 0.5),
])
def test_normalize_rating(min_val, max_val, value, expected):
    """Test rating normalization with various inputs."""
    rating = RatingSource(
        source="test",
        min_rating=min_val,
        max_rating=max_val,
        total_ratings=1,
        avg_funniness=value
    )
    assert abs(rating.normalized_avg_funniness - expected) < 0.00001
```

## Test Documentation

### Docstrings

Every test should have a clear docstring:

```python
def test_feature_name(self):
    """Test that feature_name correctly handles valid input.

    Given: A valid joke with all required fields
    When: The joke is saved to the database
    Then: The joke is persisted with correct computed fields
    """
    pass
```

### Test Class Documentation

```python
class TestJokeValidation(unittest.TestCase):
    """Tests for joke validation rules.

    This test suite covers:
    - Content validation (length, format)
    - Enum validation (categories, maturity rating)
    - Required field validation
    - Optional field handling
    - Edge cases (empty, None, unicode)

    See: docs/VALIDATION.md for validation rules
    """
    pass
```

## Coverage Standards

### Minimum Coverage

- **Overall**: 80% line coverage (enforced by `task test:coverage`)
- **Critical paths**: 100% coverage for:
  - Data validation logic
  - Database operations
  - Import/export functions
  - Data transformations

### Coverage Reports

```bash
# Generate coverage report
task test:coverage

# View HTML report
open htmlcov/index.html

# Check coverage of specific file
pytest --cov=joke_emporium.models.joke --cov-report=term-missing tests/
```

### Coverage Exclusions

Mark code that shouldn't be tested:

```python
def complex_function():
    try:
        # main logic
        pass
    except Exception as e:  # pragma: no cover
        # Emergency fallback - too complex to test
        log_error(e)
        raise
```

## Performance Testing

### Test Performance

```python
import time


class TestPerformance(unittest.TestCase):

    def test_bulk_insert_performance(self):
        """Test that bulk insert completes in reasonable time."""
        start = time.time()

        # Insert 1000 jokes
        for i in range(1000):
            save_joke(session, create_test_joke())

        elapsed = time.time() - start
        self.assertLess(elapsed, 5.0, "Bulk insert took too long")
```

### Using pytest-benchmark

```python
def test_joke_validation_performance(benchmark):
    """Benchmark joke validation."""
    joke = create_test_joke()
    result = benchmark(validate_joke, joke)
    assert result.is_valid
```

## Async Testing

### Testing Async Code

```python
import asyncio
import unittest


class TestAsyncImporter(unittest.TestCase):

    def test_async_download(self):
        """Test async download function."""
        async def run_test():
            result = await download_jokes_async()
            self.assertIsNotNone(result)

        asyncio.run(run_test())


# Or with pytest
@pytest.mark.asyncio
async def test_async_download():
    """Test async download function."""
    result = await download_jokes_async()
    assert result is not None
```

## Debugging Tests

### Running Single Test with Debug Output

```bash
# Run with print statements shown
pytest -s tests/test_models.py::TestJoke::test_create_joke

# Run with pdb on failure
pytest --pdb tests/

# Run with pdb on error
pytest --pdbcls=IPython.terminal.debugger:TerminalPdb tests/
```

### Adding Debug Output

```python
import logging


class TestWithDebug(unittest.TestCase):

    def setUp(self):
        """Enable debug logging for tests."""
        logging.basicConfig(level=logging.DEBUG)

    def test_something(self):
        """Test with debug output."""
        logger = logging.getLogger(__name__)
        logger.debug(f"Testing with data: {self.test_data}")
        # ... test code
```

## Common Patterns

### Testing Exceptions

```python
def test_exception_with_message(self):
    """Test that exception contains expected message."""
    with self.assertRaises(ValueError) as context:
        invalid_function()

    self.assertIn("expected error text", str(context.exception))


def test_exception_attributes(self):
    """Test custom exception attributes."""
    with self.assertRaises(CustomError) as context:
        raise_custom_error()

    self.assertEqual(context.exception.error_code, "ERR_001")
```

### Testing Database Transactions

```python
def test_transaction_rollback(self):
    """Test that failed transaction rolls back properly."""
    try:
        with session.begin():
            save_joke(session, joke1)
            save_joke(session, invalid_joke)  # This will fail
    except ValidationError:
        pass

    # Verify joke1 was not saved (rolled back)
    result = get_joke_by_uuid(session, joke1.id)
    self.assertIsNone(result)
```

### Testing File Operations

```python
import tempfile
from pathlib import Path


def test_file_export(self):
    """Test exporting jokes to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "jokes.json"

        export_jokes(output_path, [joke1, joke2])

        self.assertTrue(output_path.exists())
        with open(output_path) as f:
            data = json.load(f)
        self.assertEqual(len(data), 2)
```

## Anti-Patterns to Avoid

### Don't: Modify Tests to Make Them Pass

```python
# BAD: Changing test to match broken code
def test_calculate_average(self):
    """Test average calculation."""
    # Bug found: returns 0 instead of proper average
    # WRONG FIX: Change assertion
    self.assertEqual(calculate_average([1, 2, 3]), 0)  # ❌ Wrong!

# GOOD: Fix the code or document the issue
def test_calculate_average(self):
    """Test average calculation."""
    self.assertEqual(calculate_average([1, 2, 3]), 2.0)  # ✓ Correct
    # If this fails, fix calculate_average(), not the test!
```

### Don't: Write Overly Broad Tests

```python
# BAD: Test tries to test everything
def test_entire_system(self):
    """Test the entire system."""  # Too broad!
    # 200 lines of test code...

# GOOD: Break into focused tests
def test_joke_creation(self):
    """Test joke creation."""
    # ...

def test_joke_validation(self):
    """Test joke validation."""
    # ...

def test_joke_persistence(self):
    """Test joke persistence."""
    # ...
```

### Don't: Use Sleep for Timing

```python
# BAD: Using sleep to wait for async operation
def test_async_operation(self):
    start_operation()
    time.sleep(5)  # Hope it's done by now... ❌
    self.assertTrue(is_complete())

# GOOD: Poll with timeout or use proper async patterns
def test_async_operation(self):
    start_operation()
    for _ in range(50):  # 5 seconds max
        if is_complete():
            break
        time.sleep(0.1)
    self.assertTrue(is_complete())
```

### Don't: Depend on Test Execution Order

```python
# BAD: Test depends on previous test
class BadTests(unittest.TestCase):
    def test_01_create(self):
        self.db_id = save_to_db(data)  # ❌

    def test_02_read(self):
        result = read_from_db(self.db_id)  # ❌ Depends on test_01

# GOOD: Each test is independent
class GoodTests(unittest.TestCase):
    def setUp(self):
        self.db_id = save_to_db(data)  # ✓

    def test_read(self):
        result = read_from_db(self.db_id)  # ✓ Independent
```

### Don't: Test Implementation Details

```python
# BAD: Testing internal implementation
def test_internal_cache(self):
    obj = MyClass()
    obj.process()
    self.assertEqual(len(obj._cache), 1)  # ❌ Testing private detail

# GOOD: Test public behavior
def test_process_result(self):
    obj = MyClass()
    result = obj.process()
    self.assertEqual(result, expected_value)  # ✓ Testing behavior
```

## Continuous Integration

Tests should:
- Run on every commit
- Block merges if tests fail
- Maintain coverage thresholds
- Run linting checks

### Pre-commit Checklist

Before committing:
```bash
# 1. Format code
task format

# 2. Run linter
task lint

# 3. Run tests
task test:coverage

# 4. Verify all pass
```

## Documentation References

- [unittest documentation](https://docs.python.org/3/library/unittest.html)
- [pytest documentation](https://docs.pytest.org/)
- [PEP 8 Style Guide](https://pep8.org/)
- [Test Coverage with pytest-cov](https://pytest-cov.readthedocs.io/)

## Summary

### Key Takeaways

1. ✅ Use `unittest` for writing tests, `pytest` for running them
2. ✅ Test positive cases, negative cases, and edge cases
3. ✅ Tests define truth - fix code, not tests
4. ✅ Follow PEP 8 and code quality standards
5. ✅ Maintain 80% minimum coverage
6. ✅ Write clear, focused, independent tests
7. ✅ Use appropriate assertions and mocks
8. ✅ Document what each test validates

### Test Quality Checklist

- [ ] Test has clear, descriptive name
- [ ] Test has docstring explaining what it tests
- [ ] Test follows Arrange-Act-Assert pattern
- [ ] Test is independent (doesn't rely on other tests)
- [ ] Test is focused (tests one behavior)
- [ ] Test covers positive, negative, or edge case
- [ ] Test uses appropriate assertions
- [ ] Test is fast (or marked as slow if necessary)
- [ ] Test is maintainable and readable
- [ ] Test will fail if the feature breaks

**Remember**: Good tests are executable documentation that prove your code works correctly!
