# Data Source Import Plan

## Overview

This document outlines the plan for implementing data source importing scripts for the Joke Emporium project. We'll start with a single data source (taivop/joke-dataset) and create a reusable framework that can be extended to other sources.

## Architecture

### Two-Stage Database Approach

We'll implement a two-stage validation approach:

1. **Staging Database** (`data/staging.db`)
   - Receives raw imported data
   - Allows for validation and quality control
   - Includes import metadata (import_id, imported_at, validation_status)
   - Can be inspected before merging into production

2. **Production Database** (`data/jokes.db`)
   - Contains only validated, high-quality jokes
   - Current database schema remains unchanged
   - Receives data via merge operation from staging

### Import Pipeline

```
Source Data → Download → Parse → Transform → Staging DB → Validate → Production DB
```

## Phase 1: Core Import Framework

### 1.1 Directory Structure

```
src/joke_emporium/
├── importers/
│   ├── __init__.py
│   ├── base.py              # Base importer class
│   ├── taivop.py            # taivop/joke-dataset importer
│   ├── models.py            # Import-specific models
│   └── utils.py             # Shared utilities
├── db/
│   ├── staging.py           # Staging database models/ops
│   └── merge.py             # Staging → Production merge logic
└── validation/
    ├── __init__.py
    ├── rules.py             # Validation rules
    └── deduplication.py     # Duplicate detection
```

### 1.2 Data Models

#### Import Metadata Model
```python
class ImportMetadata(BaseModel):
    import_id: str              # UUID for this import batch
    source: str                 # e.g., "taivop/joke-dataset"
    source_version: str | None  # Git commit hash or version
    imported_at: datetime
    total_records: int
    successful: int
    failed: int
    validation_status: ValidationStatus  # pending, validated, rejected
    notes: str | None
```

#### Staging Joke Model
Extends JokeDB with:
- `import_id`: Link to import batch
- `validation_status`: pending/approved/rejected
- `validation_notes`: Why rejected/notes
- `duplicate_of`: UUID if duplicate detected
- `original_data`: JSON blob of raw source data

### 1.3 Base Importer Class

```python
class BaseImporter(ABC):
    """Base class for all data source importers."""

    source_name: str
    temp_dir: Path = Path("temp/imports")

    @abstractmethod
    async def download(self) -> Path:
        """Download source data to temp location."""
        pass

    @abstractmethod
    def parse(self, data_path: Path) -> Iterator[dict]:
        """Parse raw data into dict format."""
        pass

    @abstractmethod
    def transform(self, raw_data: dict) -> Joke | None:
        """Transform raw data to Joke model."""
        pass

    def import_to_staging(
        self,
        session: Session,
        validate: bool = True,
        batch_size: int = 100
    ) -> ImportMetadata:
        """Main import pipeline."""
        # 1. Download
        # 2. Parse
        # 3. Transform
        # 4. Save to staging
        # 5. Optional validation
        # 6. Return metadata
        pass
```

## Phase 2: taivop/joke-dataset Implementation

### 2.1 Source Details

- **URL**: https://github.com/taivop/joke-dataset
- **Format**: JSON files
- **Structure**: Array of joke objects
- **Size**: ~200k jokes
- **Files**:
  - `reddit_jokes.json` (Reddit r/jokes)
  - `stupidstuff.json` (stupidstuff.org)
  - `wocka.json` (wocka.com)

### 2.2 Download Strategy

```python
class TaivopImporter(BaseImporter):
    source_name = "taivop/joke-dataset"
    repo_url = "https://github.com/taivop/joke-dataset"

    async def download(self) -> Path:
        """Download using git clone or direct GitHub API."""
        # Option 1: git clone (gets entire repo)
        # Option 2: GitHub API to download specific files
        # Recommended: GitHub API for specific JSON files

        download_dir = self.temp_dir / f"{self.source_name.replace('/', '_')}"
        download_dir.mkdir(parents=True, exist_ok=True)

        # Download each JSON file
        files = [
            "reddit_jokes.json",
            "stupidstuff.json",
            "wocka.json"
        ]

        for file in files:
            url = f"https://raw.githubusercontent.com/{self.repo_url}/master/{file}"
            # Download to download_dir / file

        return download_dir
```

### 2.3 Data Mapping

**taivop format:**
```json
{
  "id": "1",
  "type": "single",
  "setup": "What do you call a ...",
  "punchline": "...",
  "score": 123,
  "category": "one-liners"
}
```

**Mapping to Joke model:**
- `id` → Include in `metadata.metadata` as `source_id`
- `type` → Map to `StructureType` (single→oneliner, twoPart→qa)
- `setup` + `punchline` → `content` array with JokeElement
- `score` → `ratings` with RatingSource (reddit_score)
- `category` → Try to map to `Category` enum, else add as tag
- Source → `metadata.source` (platform=REDDIT/OTHER)

### 2.4 Transform Logic

```python
def transform(self, raw_data: dict) -> Joke | None:
    """Transform taivop joke format to Joke model."""

    # Generate UUID
    joke_id = str(uuid4())

    # Build content
    content = []
    if raw_data.get("type") == "single":
        content.append(JokeElement(
            type=ElementType.BODY,
            text=raw_data.get("body", "")
        ))
    else:  # two-part
        if setup := raw_data.get("setup"):
            content.append(JokeElement(
                type=ElementType.SETUP,
                text=setup
            ))
        if punchline := raw_data.get("punchline"):
            content.append(JokeElement(
                type=ElementType.PUNCHLINE,
                text=punchline
            ))

    # Map structure
    structure = None
    if raw_data.get("type") == "single":
        structure = StructureType.ONELINER
    elif raw_data.get("type") == "twoPart":
        structure = StructureType.QA

    # Map category
    categories = []
    tags = []
    if cat := raw_data.get("category"):
        try:
            categories.append(Category(cat.lower()))
        except ValueError:
            tags.append(cat)

    # Map ratings
    ratings = []
    if score := raw_data.get("score"):
        ratings.append(RatingSource(
            source="reddit_score",
            min_rating=0,
            max_rating=None,  # Reddit has no max
            total_ratings=1,
            avg_funniness=score,
            votes=None
        ))

    # Detect source platform from file/metadata
    source_platform = SourcePlatform.REDDIT  # or OTHER

    # Build metadata
    metadata = JokeMetadata(
        language="en",
        authors=[Author(
            id="unknown",
            type=AuthorType.ANONYMOUS,
            name="Anonymous"
        )],
        source=Source(
            platform=source_platform,
            url=None,
            scraped_date=None,
            metadata={"source_id": raw_data.get("id")}
        ),
        added_date=datetime.now(timezone.utc),
        last_modified=datetime.now(timezone.utc),
        verified=False
    )

    return Joke(
        id=joke_id,
        content=content,
        categories=categories,
        structure=structure,
        tags=tags,
        ratings=ratings,
        metadata=metadata
    )
```

## Phase 3: Validation Framework

### 3.1 Validation Rules

```python
class ValidationRule(ABC):
    @abstractmethod
    def validate(self, joke: Joke) -> ValidationResult:
        pass

class ValidationResult:
    is_valid: bool
    errors: list[str]
    warnings: list[str]

# Specific rules
class MinimumContentLength(ValidationRule):
    """Ensure joke has minimum text length."""
    min_length: int = 10

class NoEmptyContent(ValidationRule):
    """Ensure all content elements have text."""

class ValidEnumValues(ValidationRule):
    """Ensure enums are valid."""

class DuplicateDetection(ValidationRule):
    """Check for duplicates via text similarity."""
```

### 3.2 Deduplication Strategy

1. **Exact match**: Hash of normalized text
2. **Fuzzy match**: Levenshtein distance > 90% similarity
3. **Store duplicate relationships** in staging DB

```python
def detect_duplicates(
    session: Session,
    joke: Joke,
    threshold: float = 0.9
) -> str | None:
    """
    Returns UUID of duplicate if found, else None.

    Strategy:
    1. Compute text hash (normalized: lowercase, strip punctuation)
    2. Check for exact hash match
    3. If no exact match, check fuzzy similarity for recent jokes
    """
    pass
```

## Phase 4: Staging Database

### 4.1 Extended Models

```python
class StagingJokeDB(JokeDB, table=True):
    """Extended joke model for staging."""
    __tablename__ = "staging_jokes"

    # Import tracking
    import_id: str = Field(index=True)
    validation_status: str = Field(default="pending")  # pending/approved/rejected
    validation_notes: str | None = Field(default=None)
    duplicate_of: str | None = Field(default=None)  # UUID of duplicate

    # Raw data preservation
    original_data_json: str = Field(description="Original source data")

    # Relationships
    import_batch: "ImportBatchDB" = Relationship(back_populates="jokes")

class ImportBatchDB(SQLModel, table=True):
    """Track import batches."""
    __tablename__ = "import_batches"

    id: int | None = Field(default=None, primary_key=True)
    import_id: str = Field(index=True, unique=True)
    source: str
    source_version: str | None
    imported_at: datetime
    total_records: int
    successful: int
    failed: int
    validation_status: str
    notes: str | None

    # Relationships
    jokes: list["StagingJokeDB"] = Relationship(back_populates="import_batch")
```

### 4.2 Staging Operations

```python
# src/joke_emporium/db/staging.py

def init_staging_db(database_url: str | None = None) -> None:
    """Initialize staging database."""
    pass

def save_to_staging(
    session: Session,
    joke: Joke,
    import_id: str,
    original_data: dict
) -> StagingJokeDB:
    """Save joke to staging database."""
    pass

def get_staging_jokes(
    session: Session,
    import_id: str | None = None,
    validation_status: str | None = None
) -> list[StagingJokeDB]:
    """Query staging jokes."""
    pass

def approve_staging_joke(
    session: Session,
    staging_id: int
) -> None:
    """Approve a staging joke for production."""
    pass

def reject_staging_joke(
    session: Session,
    staging_id: int,
    reason: str
) -> None:
    """Reject a staging joke."""
    pass
```

## Phase 5: Merge to Production

### 5.1 Merge Strategy

```python
# src/joke_emporium/db/merge.py

def merge_approved_jokes(
    staging_session: Session,
    prod_session: Session,
    import_id: str,
    auto_approve: bool = False
) -> MergeReport:
    """
    Merge approved jokes from staging to production.

    Process:
    1. Query approved jokes (or all if auto_approve)
    2. For each joke:
       a. Check if duplicate in production
       b. If duplicate, skip or merge ratings
       c. If new, insert
    3. Return merge report
    """
    pass

class MergeReport(BaseModel):
    import_id: str
    total_processed: int
    newly_added: int
    duplicates_skipped: int
    errors: int
    error_details: list[str]
```

### 5.2 Conflict Resolution

When duplicates are detected during merge:
1. **Skip**: Don't add, log as duplicate
2. **Merge ratings**: Add new rating source to existing joke
3. **Manual review**: Flag for human decision

## Phase 6: CLI Interface

### 6.1 Task Commands

Add to `Taskfile.yml`:

```yaml
  import:taivop:
    desc: Import jokes from taivop/joke-dataset
    cmds:
      - '{{.PYTHON}} -m joke_emporium.importers.cli import taivop --validate'

  import:list:
    desc: List all import batches
    cmds:
      - '{{.PYTHON}} -m joke_emporium.importers.cli list

  import:validate:
    desc: Validate staging jokes
    cmds:
      - '{{.PYTHON}} -m joke_emporium.importers.cli validate {{.CLI_ARGS}}'

  import:merge:
    desc: Merge approved staging jokes to production
    cmds:
      - '{{.PYTHON}} -m joke_emporium.importers.cli merge {{.CLI_ARGS}}'

  staging:inspect:
    desc: Inspect staging database
    cmds:
      - '{{.PYTHON}} -m joke_emporium.importers.cli inspect {{.CLI_ARGS}}'
```

### 6.2 CLI Implementation

```python
# src/joke_emporium/importers/cli.py

import click

@click.group()
def cli():
    """Import management CLI."""
    pass

@cli.command()
@click.argument('source', type=click.Choice(['taivop', 'rjokes', 'short-jokes']))
@click.option('--validate/--no-validate', default=True)
@click.option('--auto-merge', is_flag=True, help='Auto-merge to production')
def import_cmd(source: str, validate: bool, auto_merge: bool):
    """Import jokes from a source."""
    pass

@cli.command()
@click.argument('import_id')
@click.option('--auto-approve', is_flag=True)
def merge(import_id: str, auto_approve: bool):
    """Merge staging jokes to production."""
    pass

@cli.command()
@click.option('--status', type=click.Choice(['pending', 'approved', 'rejected']))
def inspect(status: str | None):
    """Inspect staging database."""
    pass
```

## Phase 7: Dependencies

### 7.1 Required Libraries

Add to `pyproject.toml`:

```toml
dependencies = [
    "pydantic>=2.0.0",
    "sqlmodel>=0.0.14",
    "alembic>=1.13.0",
    "httpx>=0.24.0",        # For async HTTP downloads
    "aiofiles>=23.0.0",     # For async file operations
    "click>=8.0.0",         # CLI framework
    "rich>=13.0.0",         # Pretty terminal output
    "python-Levenshtein>=0.21.0",  # For fuzzy matching
]
```

## Phase 8: Testing Strategy

### 8.1 Test Structure

```
tests/
├── importers/
│   ├── test_base.py
│   ├── test_taivop.py
│   └── test_validation.py
├── db/
│   ├── test_staging.py
│   └── test_merge.py
└── fixtures/
    └── taivop_sample.json  # Small sample for testing
```

### 8.2 Test Coverage

- Download functionality (mock HTTP)
- Parsing logic
- Transform logic with edge cases
- Validation rules
- Deduplication logic
- Staging DB operations
- Merge operations

## Implementation Order

### Sprint 1: Foundation
1. Create directory structure
2. Implement base importer class
3. Create staging database models
4. Set up CLI framework
5. Write tests for base functionality

### Sprint 2: taivop Importer
1. Implement TaivopImporter download
2. Implement parsing logic
3. Implement transform logic
4. Add validation rules
5. Write integration tests

### Sprint 3: Validation & Merge
1. Implement deduplication
2. Implement staging operations
3. Implement merge logic
4. Add CLI commands
5. End-to-end testing

### Sprint 4: Polish
1. Error handling improvements
2. Progress bars and logging
3. Documentation
4. Performance optimization

## Example Usage

### Complete Import Workflow

```bash
# 1. Import to staging with validation
task import:taivop

# 2. Inspect staging results
task staging:inspect --status=pending

# 3. Review and manually approve/reject (or auto-approve all)
python -m joke_emporium.importers.cli approve <staging_id>

# 4. Merge approved jokes to production
task import:merge <import_id>

# 5. Verify production database
python -m joke_emporium.db.operations count
```

### Automated Import (No Review)

```bash
# Import and auto-merge in one step
python -m joke_emporium.importers.cli import taivop --auto-merge
```

## Future Extensions

### Additional Importers

Each new source follows the same pattern:

1. Create `src/joke_emporium/importers/<source>.py`
2. Extend `BaseImporter`
3. Implement `download()`, `parse()`, `transform()`
4. Add source-specific field mappings
5. Add CLI command
6. Write tests

### Sources to Add Next

1. **orionw/rJokesData** (TSV format, 550k jokes)
2. **amoudgl/short-jokes-dataset** (CSV/JSON, 231k jokes)
3. **API importers** (icanhazdadjoke.com, JokeAPI.dev)

## Monitoring & Logging

### Import Metrics to Track

- Total jokes processed
- Success/failure rate
- Duplicate detection rate
- Validation failure reasons
- Import duration
- Source data quality scores

### Logging Strategy

```python
import logging

logger = logging.getLogger("joke_emporium.importers")

# Log levels:
# DEBUG: Individual joke processing
# INFO: Batch progress, summary stats
# WARNING: Validation failures, duplicates
# ERROR: Import failures, data corruption
```

## Data Quality Considerations

### Pre-Import Checks

- Validate source data format
- Check file integrity
- Verify schema compatibility

### Post-Import Validation

- Content quality checks
- Language detection
- Profanity/toxicity scanning (future)
- Category distribution analysis

## Rollback Strategy

If an import batch causes issues:

```python
def rollback_import(
    session: Session,
    import_id: str
) -> None:
    """
    Remove all jokes from an import batch.

    For staging: Delete staging records
    For production: Delete by source metadata
    """
    pass
```

## Notes

- Keep original source data in staging for reference
- Use transactions for atomic imports
- Implement idempotent imports (can re-run safely)
- Consider rate limiting for API sources
- Plan for incremental updates (not just full imports)
- Store import provenance for data lineage
