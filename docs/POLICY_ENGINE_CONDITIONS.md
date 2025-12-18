# Policy Engine: Supported Conditions and Recommendations

## Current Supported Operators

The policy engine supports the following operators (as documented in HANDOFF_POLICY_ENGINE.md):

- `==` - Equals
- `!=` - Not equals
- `>` - Greater than
- `>=` - Greater than or equal
- `<` - Less than
- `<=` - Less than or equal
- `in` - Value in list
- `not_in` - Value not in list

**Note:** Null/None checking is NOT currently supported but is critical for handling optional fields.

## Available Fields for Conditions

Based on the `StagingJokeDB` model, the following fields are available:

### Core Identification
- `joke_uuid` (string) - Unique identifier
- `version` (int) - Schema version
- `staging_id` (computed) - Not in DB, would need property

### Content Fields
- `content_json` (string) - Raw JSON, would need parsing
- `text_preview` (string, max 150 chars) - Cached preview text

### Categorization
- `structure` (string) - Joke structure type (QUESTION_ANSWER, ONE_LINER, etc.)
- `maturity_rating` (string) - G, PG, PG-13, R, X
- `cognitive_type` (string) - Cognitive humor type

### Metadata
- `language` (string) - Language code (default "en")
- `source_platform` (string) - Source platform (REDDIT, TWITTER, etc.)
- `source_url` (string) - Original URL
- `verified` (bool) - Manually verified flag

### Dates/Timestamps
- `scraped_date` (datetime)
- `created_date` (datetime)
- `added_date` (datetime)
- `last_modified` (datetime)
- `reviewed_at` (datetime)
- `merged_at` (datetime)

### Quality Metrics (Cached)
- `weighted_avg_funniness` (float, 0-100) - **Most useful**
- `weighted_avg_quality` (float, 1-5) - **Most useful**
- `total_ratings_count` (int) - Number of ratings

### JSON Fields (require parsing)
- `tags_json` (string) - Array of tags
- `flags_json` (string) - Object of content flags
- `engagement_json` (string) - Engagement metrics
- `gtvh_json` (string) - Academic annotation
- `metadata_json` (string) - Additional metadata

### Review/Validation Status
- `review_status` (string) - PENDING, APPROVED, REJECTED, UNDER_REVIEW, DUPLICATE, MERGED
- `review_notes` (string) - Review comments
- `reviewed_by` (string) - Reviewer username
- `validation_status` (string) - Validation status
- `validation_notes` (string) - Validation errors

### Duplicate Detection
- `duplicate_of_uuid` (string) - UUID of original
- `duplicate_similarity` (float, 0-1) - Similarity score

### Import Tracking
- `import_batch_id` (int) - Foreign key to import batch
- `merged_to_uuid` (string) - UUID in production

## Recommended Additions

### 1. Enhanced Field Access

**Nested JSON Field Access** (Critical Priority)

Current limitation: Can't directly query JSON fields like `flags.nsfw` or `tags` array.

Recommended solution:
```python
class PolicyCondition:
    def evaluate(self, joke: StagingJokeDB) -> bool:
        # Parse JSON fields on-demand
        if self.field.startswith("flags."):
            flag_name = self.field.split(".", 1)[1]
            flags = json.loads(joke.flags_json)
            current = flags.get(flag_name, False)
        elif self.field.startswith("tags."):
            # Support tags.contains or tags array operations
            tags = json.loads(joke.tags_json)
            current = tags
        elif self.field.startswith("categories."):
            # Parse categories from content_json
            content = json.loads(joke.content_json)
            categories = content.get("categories", [])
            current = categories
        else:
            # Regular field access
            current = getattr(joke, self.field, None)
```

**Example improved conditions:**
```yaml
conditions:
  - flags.nsfw: false
  - flags.racist: false
  - tags.contains: "family-friendly"  # NEW operator
  - categories.includes: "ANIMALS"    # NEW operator
```

### 2. New Operators (High Priority)

#### String Operators
```yaml
contains: "substring"        # Text contains substring
not_contains: "bad_word"     # Text doesn't contain substring
matches: "^\\d+$"            # Regex match
starts_with: "Why"           # Starts with prefix
ends_with: "!"               # Ends with suffix
length_gt: 10                # Length greater than
length_lt: 500               # Length less than
```

**Use cases:**
```yaml
# Detect test data
- text_preview.contains: "[test]"
  action: reject

# Reject very short jokes
- text_preview.length_lt: 20
  action: reject

# Only approve jokes in specific format
- text_preview.starts_with: "Why"
  text_preview.contains: "?"
  action: approve
```

#### Array Operators
```yaml
contains: "value"            # Array contains value
not_contains: "value"        # Array doesn't contain value
contains_any: ["val1", "val2"]  # Contains any of values
contains_all: ["val1", "val2"]  # Contains all values
empty: true                  # Array is empty
not_empty: true              # Array has items
size_gt: 5                   # Array size > 5
size_lt: 10                  # Array size < 10
```

**Use cases:**
```yaml
# Reject jokes with too many tags
- tags.size_gt: 15
  action: reject

# Require at least one category
- categories.empty: true
  action: reject

# Flag jokes with specific tag combinations
- tags.contains_any: ["offensive", "controversial"]
  action: flag_for_review
```

#### Null/None Checking Operators (CRITICAL PRIORITY)
```yaml
is_null: true                # Field is None/null
is_not_null: true            # Field has a value (not None)
```

**Implementation:**
```python
case "is_null": return current is None
case "is_not_null": return current is not None
```

**Use cases:**
```yaml
# Flag jokes missing critical metadata
- created_date.is_null: true
  action: flag_for_review

# Require verified jokes to have source URL
- verified: true
  source_url.is_null: true
  action: reject
  reason: "Verified jokes must have source URL"

# Only approve jokes with complete data
- weighted_avg_funniness.is_not_null: true
  total_ratings_count: ">= 5"
  action: approve

# Flag unverified content missing author
- verified: false
  author_name.is_null: true
  action: flag_for_review
```

#### Date/Time Operators
```yaml
days_ago_gt: 30              # More than 30 days old
days_ago_lt: 7               # Less than 7 days old
before: "2024-01-01"         # Before specific date
after: "2023-01-01"          # After specific date
```

**Use cases:**
```yaml
# Prioritize recent content
- created_date.is_not_null: true
  created_date.days_ago_lt: 30
  weighted_avg_funniness: ">= 70"
  action: approve

# Reject very old unverified content
- created_date.is_not_null: true
  created_date.before: "2020-01-01"
  verified: false
  action: reject

# Flag jokes missing creation date
- created_date.is_null: true
  action: flag_for_review
```

#### Numeric Range Operators
```yaml
between: [10, 50]            # Value between min and max
not_between: [0, 10]         # Value outside range
```

**Use cases:**
```yaml
# Approve medium-high quality
- weighted_avg_funniness.between: [60, 100]
  action: approve

# Flag borderline content
- weighted_avg_funniness.between: [40, 60]
  action: flag_for_review
```

### 3. Computed/Derived Conditions (Medium Priority)

**Ratio Calculations**
```yaml
# Engagement rate calculation
engagement_rate_gt: 0.1      # upvotes / views > 10%
approval_rate_gt: 0.8        # upvotes / (upvotes + downvotes) > 80%
```

**Multi-field Logic**
```yaml
# Has sufficient ratings and good score
has_sufficient_data:
  total_ratings_count: ">= 5"
  weighted_avg_funniness: ">= 70"

# Content length appropriate for structure
appropriate_length:
  structure: "ONE_LINER"
  text_preview.length_lt: 200
```

**Implementation:**
```python
class ComputedCondition:
    """Conditions that compute values from multiple fields."""

    @staticmethod
    def engagement_rate(joke: StagingJokeDB) -> float:
        engagement = json.loads(joke.engagement_json or '{}')
        views = engagement.get('views', 0)
        upvotes = engagement.get('upvotes', 0)
        return (upvotes / views) if views > 0 else 0.0

    @staticmethod
    def approval_rate(joke: StagingJokeDB) -> float:
        engagement = json.loads(joke.engagement_json or '{}')
        upvotes = engagement.get('upvotes', 0)
        downvotes = engagement.get('downvotes', 0)
        total = upvotes + downvotes
        return (upvotes / total) if total > 0 else 0.5
```

### 4. OR Logic Support (Medium Priority)

Current limitation: Only AND logic within a policy (all conditions must match).

**Proposed syntax:**
```yaml
policies:
  auto_approve:
    - name: "high_quality_from_any_source"
      conditions_any:  # OR logic - any condition group matches
        - group_1:
            - source_platform: "REDDIT"
            - weighted_avg_funniness: ">= 90"
        - group_2:
            - source_platform: "TWITTER"
            - weighted_avg_funniness: ">= 95"
            - verified: true
        - group_3:
            - weighted_avg_funniness: ">= 100"  # Always approve if excellent
      action: approve
```

**Alternative syntax (more explicit):**
```yaml
conditions:
  - or:
      - weighted_avg_funniness: ">= 100"
      - and:
          - verified: true
          - weighted_avg_funniness: ">= 80"
```

### 5. Conditional Transformations (Low Priority)

**Auto-fix common issues before policy evaluation:**
```yaml
transformations:
  - name: "normalize_maturity"
    if:
      maturity_rating.null: true
      flags.nsfw: true
    then:
      set_maturity_rating: "R"

  - name: "add_missing_categories"
    if:
      text_preview.contains: "programming"
      categories.not_contains: "PROGRAMMING"
    then:
      add_category: "PROGRAMMING"
```

### 6. Aggregation/Batch Conditions (Low Priority)

**Conditions across entire import batch:**
```yaml
batch_conditions:
  - name: "low_quality_batch"
    if:
      avg_weighted_funniness: "< 30"
      percentage_with_ratings: "< 20"
    then:
      action: reject_all
      reason: "Low quality batch"
```

## Practical Policy Examples

### Example 1: Comprehensive Reddit Import Policy
```yaml
policies:
  auto_approve:
    - name: "high_quality_safe_reddit"
      conditions:
        - source_platform: "REDDIT"
        - weighted_avg_funniness: ">= 80"
        - total_ratings_count: ">= 10"
        - maturity_rating.in: ["G", "PG", "PG-13"]
        - flags.racist: false
        - flags.sexist: false
        - flags.explicit: false
        - text_preview.length_gt: 20
        - text_preview.not_contains: "[deleted]"
        - text_preview.not_contains: "[removed]"
      action: approve

    - name: "verified_content_any_rating"
      conditions:
        - verified: true
        - weighted_avg_funniness: ">= 60"
        - total_ratings_count: ">= 5"
      action: approve

  auto_reject:
    - name: "deleted_or_removed_content"
      conditions_any:
        - text_preview.contains: "[deleted]"
        - text_preview.contains: "[removed]"
        - text_preview.contains: "[TEST]"
      action: reject
      reason: "Deleted/removed/test content"

    - name: "low_quality_with_data"
      conditions:
        - weighted_avg_funniness: "< 20"
        - total_ratings_count: ">= 10"
      action: reject
      reason: "Consistently low rated"

    - name: "inappropriate_content"
      conditions_any:
        - flags.racist: true
        - flags.sexist: true
        - and:
            - flags.explicit: true
            - maturity_rating: "G"  # Inconsistent rating
      action: reject
      reason: "Content policy violation"

    - name: "too_short"
      conditions:
        - text_preview.length_lt: 10
      action: reject
      reason: "Joke too short"

  flag_for_review:
    - name: "borderline_nsfw"
      conditions:
        - maturity_rating: "R"
        - weighted_avg_funniness.between: [50, 80]
        - flags.nsfw: true
        - flags.explicit: false
      action: flag

    - name: "missing_metadata"
      conditions_any:
        - created_date.is_null: true
        - source_url.is_null: true
        - structure.is_null: true
      action: flag

    - name: "potential_duplicate"
      conditions:
        - duplicate_similarity: ">= 0.85"
        - duplicate_similarity: "< 0.95"
      action: flag

    - name: "unusual_engagement"
      conditions:
        - engagement_rate_gt: 0.5  # Very high engagement
        - weighted_avg_funniness: "< 50"  # But low rating
      action: flag
```

### Example 2: Strict Content Policy
```yaml
# config/policies/strict.yaml
policies:
  auto_approve:
    - name: "family_friendly_only"
      conditions:
        - maturity_rating: "G"
        - weighted_avg_funniness: ">= 70"
        - flags.nsfw: false
        - flags.political: false
        - flags.religious: false
        - verified: true
      action: approve

  auto_reject:
    # Reject everything else by default
    - name: "not_family_friendly"
      conditions:
        - maturity_rating.not_in: ["G"]
      action: reject
      reason: "Only G-rated content allowed in strict mode"
```

### Example 3: Permissive Quality-Based Policy
```yaml
# config/policies/permissive.yaml
policies:
  auto_approve:
    - name: "any_good_joke"
      conditions:
        - weighted_avg_funniness: ">= 60"
        - total_ratings_count: ">= 3"
        - text_preview.length_gt: 15
      action: approve

  auto_reject:
    - name: "clearly_bad"
      conditions:
        - weighted_avg_funniness: "< 20"
        - total_ratings_count: ">= 5"
      action: reject
```

## Implementation Priority

### Phase 1 (MVP - Essential)
1. ✅ Basic operators: `==`, `!=`, `>`, `>=`, `<`, `<=`
2. ✅ Nested field access: `flags.nsfw`, `metadata.source`
3. **NEW:** `is_null`, `is_not_null` for None checks (CRITICAL - many fields are optional)
4. **NEW:** `in`, `not_in` for list membership
5. **NEW:** JSON field parsing (flags, tags, categories)

### Phase 2 (High Value)
6. String operators: `contains`, `not_contains`, `starts_with`, `ends_with`, `length_gt`, `length_lt`
7. Array operators: `contains`, `empty`, `size_gt`
8. Date operators: `days_ago_gt`, `days_ago_lt`, `before`, `after`
9. Numeric: `between`, `not_between`

### Phase 3 (Advanced)
10. OR logic support (`conditions_any`)
11. Computed conditions (engagement_rate, approval_rate)
12. Regex matching
13. Batch-level conditions

### Phase 4 (Future)
14. Conditional transformations
15. Machine learning integration
16. Policy templates with parameters

## Testing Recommendations

For each new operator, create unit tests:

```python
def test_is_null_operator():
    """Test is_null operator for None/null fields."""
    condition = PolicyCondition("created_date", "is_null", True)
    joke = create_test_joke(created_date=None)
    assert condition.evaluate(joke) is True

    joke_with_date = create_test_joke(created_date=datetime.now())
    assert condition.evaluate(joke_with_date) is False

def test_is_not_null_operator():
    """Test is_not_null operator."""
    condition = PolicyCondition("source_url", "is_not_null", True)
    joke = create_test_joke(source_url="https://example.com")
    assert condition.evaluate(joke) is True

    joke_without_url = create_test_joke(source_url=None)
    assert condition.evaluate(joke_without_url) is False

def test_contains_operator():
    condition = PolicyCondition("text_preview", "contains", "chicken")
    joke = create_test_joke(text_preview="Why did the chicken cross the road?")
    assert condition.evaluate(joke) is True

def test_nested_flag_access():
    condition = PolicyCondition("flags.nsfw", "==", True)
    joke = create_test_joke(flags_json='{"nsfw": true}')
    assert condition.evaluate(joke) is True

def test_array_size_operator():
    condition = PolicyCondition("tags", "size_gt", 5)
    joke = create_test_joke(tags_json='["a","b","c","d","e","f"]')
    assert condition.evaluate(joke) is True

def test_null_check_with_nested_field():
    """Test null checking with nested JSON fields."""
    condition = PolicyCondition("metadata.custom_field", "is_null", True)
    joke = create_test_joke(metadata_json='{"other_field": "value"}')
    assert condition.evaluate(joke) is True  # custom_field doesn't exist

    joke_with_field = create_test_joke(metadata_json='{"custom_field": "value"}')
    assert condition.evaluate(joke_with_field) is False
```

## Documentation Needs

When implementing:
1. Update HANDOFF_POLICY_ENGINE.md with full operator reference
2. Create POLICY_COOKBOOK.md with real-world examples
3. Add inline examples to default config/import_policies.yaml
4. Document performance implications of complex conditions
5. Create migration guide for updating existing policies

## Performance Considerations

- **JSON parsing overhead** - Cache parsed JSON for batch operations
- **Regex operations** - Compile patterns once, not per joke
- **Complex conditions** - Profile and optimize hot paths
- **Database queries** - Consider adding indexes for frequently filtered fields
- **Batch processing** - Process jokes in chunks if memory becomes an issue

Estimated processing time with optimizations:
- Simple conditions: ~0.1ms per joke (195k jokes in 20 seconds)
- Complex conditions with JSON parsing: ~0.3ms per joke (195k jokes in 60 seconds)
