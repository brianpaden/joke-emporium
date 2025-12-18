# Policy Engine - Execution Plan (Revised)

**Status:** Ready for Implementation
**Priority:** P0 (Immediate)
**Estimated Duration:** 1-2 days
**Agent Strategy:** Python-pro for core implementation, specialized agents for testing/docs/review

## Agent Assignment Philosophy

### When to Use python-pro
Use **python-pro** for tasks requiring:
- Modern Python 3.13 features (dataclasses, match statements, type hints)
- Performance optimization (must process 195k jokes in <60 seconds)
- Complex type systems (nested field access, operator evaluation, type coercion)
- Pydantic integration and SQLModel patterns
- Strict mypy compliance with production-ready code
- Modern tooling (uv, ruff, modern Python patterns)

### When to Use Other Agents
- **backend-architect**: High-level architectural decisions only (not implementation)
- **test-automator**: Test suite design and pytest patterns
- **docs-architect**: User-facing documentation and API docs
- **tutorial-engineer**: Step-by-step guides and examples
- **code-reviewer**: Final review for consistency and best practices

## Phase 1: Core Policy Engine (Day 1)

### Task 1.1: PolicyCondition Implementation
**Agent:** python-pro
**Duration:** 2 hours
**Output:** `src/joke_emporium/importers/policies.py` (PolicyCondition class)

**Requirements:**
- Implement dataclass with modern Python 3.13 patterns
- Support operators: `==`, `!=`, `>`, `>=`, `<`, `<=`, `in`, `not_in`
- Nested field access with dot notation (e.g., `flags.nsfw`)
- Type-safe operator evaluation with proper type coercion
- Handle None/null values gracefully
- Strict type hints for mypy compliance

**Python-Specific Concerns:**
- Use `match` statement for operator dispatch (Python 3.10+)
- Leverage `getattr()` with proper None handling for nested access
- Consider using `operator` module for numeric comparisons
- Ensure proper boolean evaluation for edge cases
- Performance: Single condition evaluation must be O(1)

**Key Code Pattern:**
```python
from dataclasses import dataclass
from typing import Any, Literal
from operator import eq, ne, gt, ge, lt, le

@dataclass
class PolicyCondition:
    field: str
    operator: Literal["==", "!=", ">", ">=", "<", "<=", "in", "not_in"]
    value: Any

    def evaluate(self, obj: Any) -> bool:
        """Evaluate condition against object. O(1) complexity."""
        # Navigate nested fields efficiently
        current = obj
        for part in self.field.split("."):
            current = getattr(current, part, None)
            if current is None:
                return False

        # Fast operator dispatch using match
        match self.operator:
            case "==": return eq(current, self.value)
            case "!=": return ne(current, self.value)
            # ... etc
```

**Acceptance Criteria:**
- All operators work correctly with test fixtures
- Nested field access handles 3+ levels deep
- None values return False (safe default)
- Type hints pass strict mypy check
- No performance regressions (<1ms per evaluation)

---

### Task 1.2: Policy Class Implementation
**Agent:** python-pro
**Duration:** 2 hours
**Output:** `src/joke_emporium/importers/policies.py` (Policy class)

**Requirements:**
- Policy dataclass with name, conditions, action, reason (optional)
- AND logic: all conditions must match
- Integration with PolicyCondition
- Clear error messages for invalid configurations
- Type-safe action enum

**Python-Specific Concerns:**
- Use `Enum` for action types (APPROVE, REJECT, FLAG)
- Leverage `all()` for AND logic across conditions
- Consider using `__post_init__` for validation
- Ensure immutability with frozen dataclass
- Fast matching algorithm: short-circuit on first failure

**Key Code Pattern:**
```python
from enum import Enum
from dataclasses import dataclass, field

class PolicyAction(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    FLAG = "flag"

@dataclass(frozen=True)
class Policy:
    name: str
    conditions: list[PolicyCondition]
    action: PolicyAction
    reason: str | None = None

    def matches(self, obj: Any) -> bool:
        """Check if all conditions match. Short-circuits on first False."""
        return all(condition.evaluate(obj) for condition in self.conditions)
```

**Acceptance Criteria:**
- Matches only when ALL conditions are true
- Short-circuits efficiently (stops on first false)
- Frozen dataclass prevents accidental mutation
- Type hints pass strict mypy
- Clear __repr__ for debugging

---

### Task 1.3: PolicyEngine Core Implementation
**Agent:** python-pro
**Duration:** 3 hours
**Output:** `src/joke_emporium/importers/policies.py` (PolicyEngine class)

**Requirements:**
- Load policies from YAML configuration
- Apply policies to staging jokes with first-match-wins logic
- Support dry-run mode (no database changes)
- Generate detailed statistics report
- Performance: Process 195k jokes in <60 seconds

**Python-Specific Concerns:**
- Efficient YAML parsing with PyYAML
- Batch database queries (avoid N+1)
- Use SQLModel session context managers properly
- Progress tracking without performance penalty
- Consider using itertools/functools for policy matching
- Memory-efficient iteration over large result sets

**Key Code Pattern:**
```python
from pathlib import Path
from typing import Any
import yaml
from sqlmodel import Session, select

class PolicyEngine:
    def __init__(self, config_path: Path):
        """Load and validate YAML configuration."""
        with config_path.open() as f:
            config = yaml.safe_load(f)

        self.auto_approve_policies = self._parse_policies(config, "auto_approve")
        self.auto_reject_policies = self._parse_policies(config, "auto_reject")
        self.flag_policies = self._parse_policies(config, "flag_for_review")

    def apply_policies(
        self,
        session: Session,
        import_batch_id: str,
        dry_run: bool = False
    ) -> dict[str, int]:
        """Apply policies to pending jokes. Returns statistics."""
        # Efficient batch query with single DB roundtrip
        stmt = select(StagingJokeDB).where(
            StagingJokeDB.import_batch_id == import_batch_id,
            StagingJokeDB.review_status == ReviewStatus.PENDING
        )
        jokes = session.exec(stmt).all()

        stats = {"total": len(jokes), "approved": 0, "rejected": 0, "flagged": 0, "skipped": 0}

        for joke in jokes:
            # First-match wins: check approve, then reject, then flag
            if matched_policy := self._find_matching_policy(joke, self.auto_approve_policies):
                if not dry_run:
                    joke.review_status = ReviewStatus.APPROVED
                    joke.review_notes = f"Auto-approved: {matched_policy.name}"
                stats["approved"] += 1
            # ... similar for reject and flag
            else:
                stats["skipped"] += 1

        if not dry_run:
            session.commit()

        return stats
```

**Performance Requirements:**
- Single batch query for all jokes (avoid N+1)
- First-match-wins stops at first policy match
- Target: <60 seconds for 195k jokes (~3,250 jokes/second)
- Memory-efficient: Don't load all jokes into memory at once
- Consider using session.exec().yield_per() for chunking

**Acceptance Criteria:**
- Loads valid YAML without errors
- Processes 1000 test jokes in <2 seconds
- Dry-run mode commits nothing to database
- Statistics are accurate
- First-match-wins logic is correct
- Type hints pass strict mypy

---

### Task 1.4: Unit Tests for Core Engine
**Agent:** test-automator
**Duration:** 2 hours
**Output:** `tests/test_importers/test_policies.py`

**Requirements:**
- Test all operators in PolicyCondition
- Test nested field access (2-3 levels deep)
- Test None/null handling
- Test Policy AND logic
- Test PolicyEngine YAML loading
- Test first-match-wins logic
- Test dry-run vs. commit behavior
- Edge cases: empty policies, invalid YAML, missing fields

**Testing Strategy:**
- Use pytest fixtures from conftest.py (staging_session)
- Real joke samples from fixtures/real_joke_samples.json
- Parametrize operator tests for DRY code
- Mock file I/O for YAML loading tests
- Use tmp_path fixture for temporary YAML files

**Coverage Target:** 90%+ for policies.py

**Acceptance Criteria:**
- 20+ test cases covering all features
- All tests pass with pytest-cov
- No flaky tests
- Fast execution (<5 seconds total)

---

## Phase 2: CLI Integration (Day 2)

### Task 2.1: CLI Command Implementation
**Agent:** python-pro
**Duration:** 2 hours
**Output:** `src/joke_emporium/importers/cli.py` (apply-policies command)

**Requirements:**
- Add `apply-policies` click command
- Support --dry-run flag
- Support --config path (default: config/import_policies.yaml)
- Support --yes flag (skip confirmation)
- Rich console output with statistics
- Confirmation prompt before applying
- Error handling for invalid import IDs

**Python-Specific Concerns:**
- Click integration with proper type hints
- Rich table for statistics display
- Context manager for database session
- Pathlib for config file handling
- Clear error messages with suggestions
- Follow existing CLI patterns in the codebase

**Key Code Pattern:**
```python
import click
from rich.console import Console
from rich.table import Table
from pathlib import Path

@cli.command()
@click.argument("import_id")
@click.option("--dry-run", is_flag=True, help="Preview without applying changes")
@click.option("--config", type=click.Path(exists=True, path_type=Path),
              default=Path("config/import_policies.yaml"), help="Policy config file")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt")
def apply_policies(import_id: str, dry_run: bool, config: Path, yes: bool) -> None:
    """Apply policy-based auto-approval rules to an import batch."""
    console = Console()

    # Load engine and validate
    try:
        engine = PolicyEngine(config)
    except Exception as e:
        console.print(f"[red]Error loading policies: {e}[/red]")
        raise click.Abort()

    # Dry-run preview
    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]")

    # Apply policies
    with get_staging_session() as session:
        stats = engine.apply_policies(session, import_id, dry_run)

    # Display results with Rich table
    table = Table(title="Policy Application Results")
    # ... format stats
    console.print(table)
```

**Acceptance Criteria:**
- Command appears in `--help` output
- Dry-run shows preview without changes
- Confirmation prompt works correctly
- Statistics display is clear and readable
- Error messages are helpful
- Follows existing CLI patterns

---

### Task 2.2: CLI Integration Tests
**Agent:** test-automator
**Duration:** 2 hours
**Output:** `tests/test_importers/test_cli_policies.py`

**Requirements:**
- Test apply-policies command with Click CliRunner
- Test dry-run mode
- Test confirmation prompts
- Test custom config file
- Test error cases (invalid import ID, missing config)
- Test statistics output

**Testing Strategy:**
- Use Click's CliRunner for CLI testing
- Use tmp_path for temporary config files
- Mock console output for assertions
- Integration test with real staging database

**Acceptance Criteria:**
- 10+ test cases for CLI command
- Tests pass with coverage
- No side effects between tests
- Fast execution (<3 seconds)

---

## Phase 3: Configuration & Documentation (Day 2)

### Task 3.1: Default Policy Configuration
**Agent:** python-pro
**Duration:** 1 hour
**Output:** `config/import_policies.yaml`

**Requirements:**
- Conservative defaults for auto-approval
- Clear comments explaining each policy
- Real-world rules based on taivop analysis
- Safe defaults: prefer manual review over auto-approve

**Policy Guidelines:**
- Auto-approve: High scores (>= 100), safe content, sufficient ratings
- Auto-reject: Very low scores (< 10) with sufficient ratings
- Flag: Borderline content, mature ratings with good scores

**Acceptance Criteria:**
- Valid YAML syntax
- PolicyEngine loads without errors
- Conservative rules (low false-positive risk)
- Well-commented for user understanding

---

### Task 3.2: Policy Templates
**Agent:** python-pro
**Duration:** 1 hour
**Output:** `config/policies/strict.yaml`, `permissive.yaml`, `nsfw_only.yaml`

**Requirements:**
- Three template variations:
  - **strict.yaml**: Very conservative, mostly manual review
  - **permissive.yaml**: Aggressive auto-approval
  - **nsfw_only.yaml**: Only approve mature content
- Each with clear documentation

**Acceptance Criteria:**
- All templates load without errors
- Templates demonstrate different strategies
- Comments explain use cases

---

### Task 3.3: Technical Documentation
**Agent:** docs-architect
**Duration:** 2 hours
**Output:** Updates to `README_IMPORT_FRAMEWORK.md`, `CLAUDE.md`

**Requirements:**
- Document policy engine architecture
- Explain YAML configuration format
- Document all operators and field access
- Add CLI usage examples
- Update workflow diagrams
- API documentation for PolicyEngine classes

**Documentation Structure:**
- Overview and motivation
- YAML configuration reference
- Field access patterns (nested fields)
- Operator reference table
- CLI command examples
- Performance considerations

**Acceptance Criteria:**
- Clear for new users
- Complete operator reference
- Working examples
- Links to related docs

---

### Task 3.4: User Tutorial
**Agent:** tutorial-engineer
**Duration:** 2 hours
**Output:** New section in `README_IMPORT_FRAMEWORK.md`

**Requirements:**
- Step-by-step tutorial for first-time users
- Walkthrough of taivop import with policies
- How to customize policies for your needs
- Troubleshooting common issues
- Before/after time savings comparison

**Tutorial Structure:**
1. Import jokes to staging
2. Run dry-run to preview
3. Adjust policies based on preview
4. Apply policies with confirmation
5. Review remaining jokes manually
6. Merge to production

**Acceptance Criteria:**
- Complete end-to-end example
- Copy-paste commands that work
- Screenshots or example output
- Troubleshooting section

---

## Phase 4: Final Review & Polish

### Task 4.1: Code Review & Quality Check
**Agent:** code-reviewer
**Duration:** 1 hour
**Output:** Review feedback and final polish

**Review Checklist:**
- Code follows project style (ruff, mypy)
- Type hints are complete and correct
- Docstrings follow Google style
- Error messages are clear and actionable
- Performance meets requirements (<60s for 195k)
- Security: YAML parsing is safe
- No hardcoded paths or magic numbers
- Consistent naming conventions

**Acceptance Criteria:**
- Zero ruff violations
- Zero mypy errors
- All docstrings present
- Code review approved

---

### Task 4.2: Integration Testing
**Agent:** test-automator
**Duration:** 1 hour
**Output:** Full integration test suite

**Requirements:**
- End-to-end test: import → apply policies → merge
- Performance test with 1000+ jokes
- Test all three policy templates
- Test policy precedence (approve before reject)
- Test audit trail in review_notes

**Acceptance Criteria:**
- Full workflow passes
- Performance meets targets
- Coverage maintains 80%+
- CI/CD passes

---

## Agent Assignment Summary (Revised)

| Phase | Task | Agent | Rationale |
|-------|------|-------|-----------|
| 1.1 | PolicyCondition Implementation | **python-pro** | Core Python: dataclasses, operators, type hints, performance |
| 1.2 | Policy Class | **python-pro** | Modern Python patterns, Enum, frozen dataclass |
| 1.3 | PolicyEngine Core | **python-pro** | YAML parsing, SQLModel integration, batch queries, performance |
| 1.4 | Unit Tests | test-automator | Pytest expertise, fixture design |
| 2.1 | CLI Command | **python-pro** | Click integration, Rich console, error handling |
| 2.2 | CLI Tests | test-automator | CliRunner, integration testing |
| 3.1 | Default Config | **python-pro** | YAML structure, validation rules |
| 3.2 | Policy Templates | **python-pro** | YAML patterns, rule design |
| 3.3 | Technical Docs | docs-architect | API docs, architecture docs |
| 3.4 | User Tutorial | tutorial-engineer | Step-by-step guides |
| 4.1 | Code Review | code-reviewer | Style, quality, consistency |
| 4.2 | Integration Tests | test-automator | End-to-end testing |

**Key Change from Original Plan:**
All Python implementation tasks (1.1, 1.2, 1.3, 2.1, 3.1, 3.2) now use **python-pro** instead of generic "backend-architect" because:
- These tasks require modern Python 3.13 expertise
- Performance optimization is critical (3,250 jokes/second)
- Type safety and mypy compliance are mandatory
- Pydantic/SQLModel patterns are core to the codebase
- python-pro is specifically designed for production Python with uv/ruff/pydantic

---

## Success Criteria

### Functional Requirements
- [ ] Can load policies from YAML config
- [ ] Can evaluate all operators correctly
- [ ] Can handle nested field access (3+ levels)
- [ ] Can apply policies to import batch
- [ ] Dry-run mode shows accurate preview
- [ ] Statistics are correct
- [ ] Audit trail records policy decisions
- [ ] CLI command works with all flags

### Performance Requirements
- [ ] Process 195k jokes in <60 seconds
- [ ] Single condition evaluation: <1ms
- [ ] Memory-efficient (no full batch in memory)
- [ ] Database queries are batched (no N+1)

### Quality Requirements
- [ ] 80%+ test coverage maintained
- [ ] Zero ruff violations
- [ ] Zero mypy errors (strict mode)
- [ ] All docstrings present (Google style)
- [ ] Documentation is complete and clear

### Safety Requirements
- [ ] No auto-approve of flagged content
- [ ] Confirmation prompt works
- [ ] Dry-run commits nothing
- [ ] Clear audit trail for debugging
- [ ] Safe YAML parsing (yaml.safe_load)

---

## Risk Mitigation

| Risk | Mitigation | Agent Responsibility |
|------|------------|---------------------|
| Performance bottleneck | Batch queries, profiling, benchmarks | python-pro |
| YAML parsing errors | Validation, clear error messages | python-pro |
| False positives | Conservative defaults, dry-run mode | python-pro (config) |
| Type safety issues | Strict mypy, comprehensive type hints | python-pro |
| Test coverage gaps | Parametrized tests, edge cases | test-automator |
| Poor documentation | User testing, examples | docs-architect, tutorial-engineer |

---

## Handoff Notes

### For python-pro
- Review `CLAUDE.md` for project conventions
- Check `src/joke_emporium/db/models/staging.py` for StagingJokeDB schema
- Review `src/joke_emporium/importers/cli.py` for existing CLI patterns
- Study `tests/conftest.py` for available fixtures
- Performance is critical: 195k jokes in <60 seconds
- Use modern Python 3.13 features (match, union types)
- Follow strict mypy and ruff rules

### For test-automator
- Use real joke samples from `tests/fixtures/real_joke_samples.json`
- Follow patterns in `tests/test_importers/test_base.py`
- Target 90%+ coverage for new code
- Use parametrize for operator tests
- Integration tests should use staging_session fixture

### For docs-architect
- Update `README_IMPORT_FRAMEWORK.md` with policy engine section
- Add operator reference table
- Include YAML schema documentation
- Link to related docs (DATABASE.md, IMPORT_PLAN.md)

### For tutorial-engineer
- Walk through complete workflow: import → policies → merge
- Include real examples from taivop dataset
- Show before/after time savings
- Add troubleshooting section

### For code-reviewer
- Verify performance requirements are met
- Check YAML security (safe_load only)
- Ensure error messages are actionable
- Validate audit trail completeness

---

## Related Documents
- [docs/HANDOFF_POLICY_ENGINE.md](HANDOFF_POLICY_ENGINE.md) - Original requirements
- [docs/POLICY_ENGINE_CONDITIONS.md](POLICY_ENGINE_CONDITIONS.md) - PolicyCondition specification
- [docs/DATABASE.md](DATABASE.md) - Database schema and operations
- [docs/IMPORT_PLAN.md](IMPORT_PLAN.md) - Overall import framework
- [CLAUDE.md](../CLAUDE.md) - Project conventions and setup
