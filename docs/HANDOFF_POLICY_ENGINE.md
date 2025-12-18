# Policy-Based Auto-Approval Engine

**Status:** Planning
**Priority:** P0 (Immediate)
**Effort:** 1-2 days
**Impact:** Reduces manual review from 270 hours to <10 hours for 195k jokes

## Problem Statement

Current workflow requires manual review of each joke individually. For the taivop dataset (195k jokes), this is impractical:
- At 5 seconds per joke = 270 hours of manual work
- No bulk operations or filtering
- No policy-based automation
- High risk of human error from fatigue

## Solution Overview

Implement a declarative policy engine using YAML configuration files to define auto-approval, auto-rejection, and flagging rules. Similar to dbt data quality tests and Great Expectations validation rules.

### Core Concept

```yaml
# config/import_policies.yaml
policies:
  auto_approve:
    - name: "high_quality_reddit"
      conditions:
        - weighted_avg_funniness: ">= 100"
        - total_ratings_count: ">= 5"
        - maturity_rating: "G"
        - flags.nsfw: false
        - flags.racist: false
      action: approve

  auto_reject:
    - name: "low_quality"
      conditions:
        - weighted_avg_funniness: "< 10"
        - total_ratings_count: ">= 3"
      action: reject
      reason: "Low quality score with sufficient ratings"

  flag_for_review:
    - name: "borderline_content"
      conditions:
        - maturity_rating: "R"
        - weighted_avg_funniness: ">= 50"
      action: flag
```

## Architecture

### Components

1. **PolicyEngine** - Loads YAML config and applies policies to staging jokes
2. **PolicyCondition** - Single condition evaluator (field, operator, value)
3. **Policy** - Collection of conditions + action + metadata
4. **CLI Integration** - New `apply-policies` command

### File Structure

```
src/joke_emporium/
├── importers/
│   ├── policies.py          # NEW: Policy engine implementation
│   └── cli.py               # MODIFY: Add apply-policies command
config/
├── import_policies.yaml     # NEW: Default policy configuration
└── policies/                # NEW: Example policy templates
    ├── strict.yaml
    ├── permissive.yaml
    └── nsfw_only.yaml
```

## Key Features

### 1. Declarative Rules
- YAML-based configuration (no code changes needed)
- Support nested fields (e.g., `flags.nsfw`, `metadata.source_platform`)
- Multiple operators: `==`, `!=`, `>`, `>=`, `<`, `<=`, `in`, `not_in`
- AND logic within policy (all conditions must match)
- First-match wins across policies

### 2. Three Actions
- **auto_approve** - Mark as ReviewStatus.APPROVED
- **auto_reject** - Mark as ReviewStatus.REJECTED with reason
- **flag_for_review** - Mark as ReviewStatus.UNDER_REVIEW for manual review

### 3. Safety Features
- **Dry-run mode** - Preview what would happen without committing
- **Detailed reporting** - Show stats on actions taken
- **Confirmation prompt** - Require explicit approval before applying
- **Audit trail** - Record which policy approved/rejected each joke

### 4. CLI Interface

```bash
# Preview what would happen
uv run python -m joke_emporium.importers.cli apply-policies <import_id> --dry-run

# Apply with default config
uv run python -m joke_emporium.importers.cli apply-policies <import_id>

# Apply with custom config
uv run python -m joke_emporium.importers.cli apply-policies <import_id> --config config/policies/strict.yaml

# Auto-approve without confirmation
uv run python -m joke_emporium.importers.cli apply-policies <import_id> --yes
```

## Expected Outcomes

Based on taivop dataset analysis:
- **Auto-approve:** ~95,000 jokes (48%) - High quality, safe content
- **Auto-reject:** ~5,000 jokes (2%) - Low scores or inappropriate flags
- **Flag for review:** ~45,000 jokes (23%) - Borderline content needing human judgment
- **Manual review remaining:** ~50,000 jokes (26%) - Edge cases

**Time savings:** From 270 hours → ~10 hours (96% reduction)

## Implementation Steps

### Phase 1: Core Engine (Day 1)
1. Create `src/joke_emporium/importers/policies.py`
   - PolicyCondition class with operator evaluation
   - Policy class with condition matching
   - PolicyEngine class with YAML loading
2. Add unit tests for condition evaluation
3. Test with sample YAML configs

### Phase 2: CLI Integration (Day 2)
1. Add `apply-policies` command to cli.py
2. Implement dry-run mode
3. Add stats reporting
4. Add confirmation prompts
5. Integration tests

### Phase 3: Documentation & Templates (Day 2)
1. Create default `config/import_policies.yaml`
2. Create example templates (strict, permissive, nsfw_only)
3. Update README_IMPORT_FRAMEWORK.md
4. Add docstrings and type hints

## Technical Details

### PolicyCondition Evaluation

```python
@dataclass
class PolicyCondition:
    field: str  # e.g., "weighted_avg_funniness" or "flags.nsfw"
    operator: Literal["==", "!=", ">", ">=", "<", "<=", "in", "not_in"]
    value: Any

    def evaluate(self, joke: StagingJokeDB) -> bool:
        # Navigate nested fields (flags.nsfw → joke.flags.nsfw)
        current = joke
        for part in self.field.split("."):
            current = getattr(current, part, None)
            if current is None:
                return False

        # Apply operator
        match self.operator:
            case "==": return current == self.value
            case ">=": return current >= self.value
            # ... etc
```

### Policy Application Logic

```python
def apply_policies(self, session, import_batch_id, dry_run=False) -> dict:
    stats = {"total": 0, "approved": 0, "rejected": 0, "flagged": 0, "skipped": 0}

    jokes = get_staging_jokes_by_status(session, import_batch_id, ReviewStatus.PENDING)
    stats["total"] = len(jokes)

    for joke in jokes:
        # Try auto-approve policies first
        for policy in self.auto_approve_policies:
            if policy.matches(joke):
                if not dry_run:
                    joke.review_status = ReviewStatus.APPROVED
                    joke.review_notes = f"Auto-approved by policy: {policy.name}"
                stats["approved"] += 1
                break
        else:
            # Try auto-reject policies
            # ... similar logic
            # Try flag policies
            # ... similar logic
            stats["skipped"] += 1

    if not dry_run:
        session.commit()

    return stats
```

## Edge Cases & Considerations

1. **Null values** - Handle jokes missing optional fields gracefully
2. **Type coercion** - Convert string values to correct types for comparison
3. **Policy conflicts** - First-match wins, document precedence order
4. **Performance** - For 195k jokes, should complete in <60 seconds
5. **Rollback** - Should we support undoing policy application? (Future enhancement)

## Testing Strategy

### Unit Tests
- PolicyCondition evaluation for each operator
- Nested field access (flags.nsfw, metadata.source)
- Policy matching with multiple conditions
- YAML config loading and validation

### Integration Tests
- Apply policies to test import batch
- Dry-run mode doesn't commit changes
- Stats reporting accuracy
- Policy precedence (approve before reject)

### Manual Testing
- Run on taivop dataset with dry-run
- Verify stats match expectations
- Check sample of auto-approved jokes
- Verify rejected jokes have valid reasons

## Future Enhancements (Out of Scope)

- Policy versioning and history
- A/B testing different policy sets
- Machine learning to suggest optimal policies
- Web UI for policy editor
- Policy templates marketplace
- Rollback/undo policy application
- Policy simulation mode (what-if analysis)

## Dependencies

- PyYAML (already in project)
- No new external dependencies

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Auto-approve inappropriate content | Dry-run mode, conservative defaults, mandatory confirmation |
| Policy misconfiguration | YAML validation, clear error messages, examples |
| Performance issues with 195k jokes | Batch processing, database indexes, progress reporting |
| Overly complex policy syntax | Keep simple, document clearly, provide templates |

## Success Criteria

1. Can auto-approve 40%+ of jokes safely
2. Dry-run mode shows accurate preview
3. Full batch processing completes in <60 seconds
4. Zero false positives on inappropriate content
5. Clear audit trail of policy decisions
6. Documentation with working examples

## Related Documents

- [docs/POLICY_ENGINE_CONDITIONS.md](POLICY_ENGINE_CONDITIONS.md) - PolicyCondition checks to implement
- [docs/HANDOFF_INTERACTIVE_REVIEW.md](HANDOFF_INTERACTIVE_REVIEW.md) - TUI for manual review
- [docs/DATABASE.md](DATABASE.md) - Staging workflow details
- [docs/IMPORT_PLAN.md](IMPORT_PLAN.md) - Original import framework plan
- Industry reference: dbt tests, Great Expectations, Airflow quality gates
