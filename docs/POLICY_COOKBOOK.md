# Policy Engine Cookbook

Comprehensive guide to the Joke Emporium Policy Engine for automated review workflows.

## Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Operator Reference](#operator-reference)
4. [Field Access Patterns](#field-access-patterns)
5. [Common Use Cases](#common-use-cases)
6. [Policy Templates](#policy-templates)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)
9. [Performance Tips](#performance-tips)

## Introduction

### What Are Policies?

Policies are declarative YAML rules that automatically approve, reject, or flag staging jokes based on their metadata. Instead of manually reviewing thousands of jokes, you define rules once and let the policy engine handle the repetitive work.

### How Policies Work

The policy engine evaluates each pending joke against your policies using **first-match-wins** precedence:

1. **Auto-Approve Policies** - Checked first
2. **Auto-Reject Policies** - Checked if no approval match
3. **Flag for Review Policies** - Checked if no rejection match
4. **No Match** - Joke remains pending for manual review

Within each category, policies are evaluated by priority (higher priority first), then by definition order.

### Why Use Policies?

**Time Savings:**
- Manual review: ~270 hours for 195k jokes (5 seconds each)
- With policies: ~10 hours (reviewing only flagged/pending jokes)
- Reduction: **96% time savings**

**Consistency:**
- Reproducible decisions
- No reviewer fatigue
- Documented rationale for each decision

**Flexibility:**
- Customize for different platforms (family-friendly, adult, general)
- Adjust quality thresholds based on your needs
- Test with dry-run before applying

## Quick Start

### Running Policies

After importing jokes, apply policies to auto-review them:

```bash
# 1. Preview what policies would do (dry-run)
uv run python -m joke_emporium.importers.cli apply-policies <import-id> --dry-run

# 2. Apply default policies
uv run python -m joke_emporium.importers.cli apply-policies <import-id>

# 3. Use custom policy configuration
uv run python -m joke_emporium.importers.cli apply-policies <import-id> --config config/policies/strict.yaml

# 4. Skip confirmation prompt
uv run python -m joke_emporium.importers.cli apply-policies <import-id> --yes
```

### Your First Policy

Create a simple policy file `my_policies.yaml`:

```yaml
policies:
  auto_approve:
    - name: "high_quality_jokes"
      conditions:
        - weighted_avg_funniness: ">= 80"
        - total_ratings_count: ">= 10"
      action: approve
      reason: "High quality with sufficient community validation"

  auto_reject:
    - name: "deleted_content"
      conditions:
        - flags.deleted: "true"
      action: reject
      reason: "Content was deleted from source"
```

Apply it:

```bash
uv run python -m joke_emporium.importers.cli apply-policies <import-id> --config my_policies.yaml
```

## Operator Reference

### Complete Operator Table

| Operator | Description | Example | Notes |
|----------|-------------|---------|-------|
| `==` | Equality | `maturity_rating: "G"` | Exact match, works with strings, numbers, booleans |
| `!=` | Inequality | `flags.nsfw: "!= true"` | Not equal, opposite of `==` |
| `>` | Greater than | `weighted_avg_funniness: "> 80"` | Numeric comparison only |
| `>=` | Greater or equal | `total_ratings_count: ">= 10"` | Numeric comparison only |
| `<` | Less than | `weighted_avg_funniness: "< 20"` | Numeric comparison only |
| `<=` | Less or equal | `total_ratings_count: "<= 3"` | Numeric comparison only |
| `in` | List membership | `maturity_rating: "in ['G', 'PG']"` | Value must be in the list |
| `not_in` | Not in list | `maturity_rating: "not_in ['R', 'NC-17']"` | Value must not be in list |
| `is_null` | Is null/None | `maturity_rating: "is_null"` | Checks if field is missing/null |
| `is_not_null` | Is not null | `weighted_avg_funniness: "is_not_null"` | Checks if field exists and has value |

### Operator Examples

#### Equality and Inequality

```yaml
# Exact maturity rating
- maturity_rating: "G"  # Shorthand for == "G"
- maturity_rating: "== G"  # Explicit operator

# Not equal
- flags.nsfw: "!= true"
- maturity_rating: "!= R"
```

#### Numeric Comparisons

```yaml
# Quality thresholds
- weighted_avg_funniness: ">= 80"  # 80 or higher
- weighted_avg_funniness: "< 20"   # Below 20
- total_ratings_count: "> 5"       # More than 5

# Range checks (use multiple conditions)
conditions:
  - weighted_avg_funniness: ">= 50"
  - weighted_avg_funniness: "< 80"  # Between 50-80
```

#### List Membership

```yaml
# Match any of multiple values
- maturity_rating: "in ['G', 'PG', 'PG-13']"

# Exclude multiple values
- maturity_rating: "not_in ['R', 'NC-17']"

# Can use with any field
- metadata.source_platform: "in ['reddit', 'twitter']"
```

#### Null Checks

```yaml
# Flag missing data
- maturity_rating: "is_null"

# Require data present
- weighted_avg_funniness: "is_not_null"
- total_ratings_count: "> 0"  # Alternative: has ratings
```

## Field Access Patterns

### Direct Fields

These fields are directly accessible on the `StagingJokeDB` model:

| Field | Type | Description | Example Value |
|-------|------|-------------|---------------|
| `weighted_avg_funniness` | float | Quality score (0-100 scale) | 85.3 |
| `weighted_avg_quality` | float | Alternative quality metric | 82.1 |
| `total_ratings_count` | int | Number of ratings | 25 |
| `text_preview` | str | First 200 chars of joke | "Why did the..." |
| `maturity_rating` | str | G, PG, PG-13, R, NC-17 | "PG" |
| `verified` | bool | Verified by source | true |
| `source` | str | Import source | "taivop" |

**Examples:**

```yaml
# Quality-based
- weighted_avg_funniness: ">= 80"
- total_ratings_count: ">= 10"

# Content rating
- maturity_rating: "in ['G', 'PG']"

# Text validation
- text_preview: "!= ''"  # Not empty

# Source filtering
- source: "reddit"
```

### JSON Fields

These fields are stored as JSON and require nested access using dot notation:

#### Flags (flags.*)

| Field | Type | Description |
|-------|------|-------------|
| `flags.nsfw` | bool | Not safe for work |
| `flags.deleted` | bool | Deleted from source |
| `flags.removed` | bool | Removed by moderators |
| `flags.spam` | bool | Detected as spam |
| `flags.is_test` | bool | Test/sample data |
| `flags.profanity` | bool | Contains profanity |
| `flags.gore` | bool | Gore content |
| `flags.violence` | bool | Violence content |

**Examples:**

```yaml
# Safety checks
- flags.nsfw: "false"
- flags.deleted: "false"
- flags.removed: "false"

# Quality filters
- flags.spam: "false"
- flags.is_test: "false"

# Content warnings
- flags.profanity: "true"
- flags.violence: "false"
```

#### Engagement (engagement.*)

| Field | Type | Description |
|-------|------|-------------|
| `engagement.upvotes` | int | Community upvotes |
| `engagement.downvotes` | int | Community downvotes |
| `engagement.score` | int | Net score (up - down) |
| `engagement.num_comments` | int | Number of comments |

**Examples:**

```yaml
# High engagement
- engagement.upvotes: ">= 100"
- engagement.score: ">= 50"

# Active discussion
- engagement.num_comments: ">= 10"

# Negative reception
- engagement.downvotes: "> 50"
```

#### Metadata (metadata.*)

| Field | Type | Description |
|-------|------|-------------|
| `metadata.source_platform` | str | Platform origin (reddit, twitter) |
| `metadata.subreddit` | str | Reddit subreddit |
| `metadata.language` | str | Language code (en, es, fr) |
| `metadata.original_url` | str | Source URL |

**Examples:**

```yaml
# Platform-specific
- metadata.source_platform: "reddit"
- metadata.subreddit: "Jokes"

# Language filtering
- metadata.language: "en"

# Source validation
- metadata.original_url: "is_not_null"
```

### Nested Object Access

For deeper nesting, continue the dot notation:

```yaml
# Hypothetical deep nesting
- metadata.author.verified: "true"
- gtvh.script_opposition: "is_not_null"
```

## Common Use Cases

### Auto-Approve High-Quality Safe Content

**Goal:** Approve jokes that are excellent quality and family-friendly.

```yaml
auto_approve:
  - name: "premium_family_content"
    conditions:
      - weighted_avg_funniness: ">= 85"
      - total_ratings_count: ">= 15"
      - flags.nsfw: "false"
      - flags.deleted: "false"
      - flags.removed: "false"
      - maturity_rating: "in ['G', 'PG']"
    action: approve
    reason: "Premium quality family-safe content"
    priority: 1
```

**Explanation:**
- Requires excellent quality (85+ on 0-100 scale)
- Needs substantial ratings (15+) for confidence
- Must be safe for all audiences
- Not deleted or removed from source
- Limited to G or PG ratings

### Reject Spam and Test Data

**Goal:** Automatically reject obvious low-quality or problematic content.

```yaml
auto_reject:
  - name: "deleted_or_removed"
    conditions:
      - flags.deleted: "true"
    action: reject
    reason: "Content was deleted from source"
    priority: 1

  - name: "removed_by_moderators"
    conditions:
      - flags.removed: "true"
    action: reject
    reason: "Content removed by moderators"
    priority: 2

  - name: "test_data"
    conditions:
      - flags.is_test: "true"
    action: reject
    reason: "Test data should not be in production"
    priority: 3

  - name: "spam_content"
    conditions:
      - flags.spam: "true"
    action: reject
    reason: "Detected as spam"
    priority: 4

  - name: "very_low_quality"
    conditions:
      - weighted_avg_funniness: "< 20"
      - total_ratings_count: ">= 10"
    action: reject
    reason: "Very low quality confirmed by sufficient ratings"
    priority: 5
```

### Flag Borderline Content for Review

**Goal:** Catch edge cases that need human judgment.

```yaml
flag_for_review:
  - name: "borderline_quality"
    conditions:
      - weighted_avg_funniness: ">= 50"
      - weighted_avg_funniness: "< 80"
      - total_ratings_count: ">= 5"
    action: flag
    reason: "Moderate quality - manual verification needed"

  - name: "missing_maturity_rating"
    conditions:
      - maturity_rating: "is_null"
    action: flag
    reason: "Missing maturity rating - cannot verify safety"

  - name: "insufficient_ratings"
    conditions:
      - total_ratings_count: "< 5"
      - weighted_avg_funniness: ">= 60"
    action: flag
    reason: "Potentially good but needs more ratings"
```

### Handle Missing Metadata

**Goal:** Flag or reject jokes with incomplete data.

```yaml
flag_for_review:
  - name: "no_quality_data"
    conditions:
      - total_ratings_count: "< 1"
    action: flag
    reason: "No ratings - cannot assess quality"

  - name: "missing_content_classification"
    conditions:
      - maturity_rating: "is_null"
      - flags.nsfw: "is_null"
    action: flag
    reason: "Missing content classification metadata"

auto_reject:
  - name: "empty_content"
    conditions:
      - text_preview: ""
    action: reject
    reason: "Empty or missing joke text"
```

### Platform-Specific Filtering

**Goal:** Import only from trusted sources.

```yaml
auto_approve:
  - name: "trusted_subreddit_high_quality"
    conditions:
      - metadata.subreddit: "in ['Jokes', 'cleanjokes', 'dadjokes']"
      - weighted_avg_funniness: ">= 70"
      - total_ratings_count: ">= 8"
      - flags.nsfw: "false"
    action: approve
    reason: "High quality from trusted subreddit"

auto_reject:
  - name: "untrusted_low_engagement"
    conditions:
      - metadata.subreddit: "not_in ['Jokes', 'cleanjokes', 'dadjokes']"
      - engagement.upvotes: "< 10"
    action: reject
    reason: "Low engagement from untrusted source"
```

### High-Engagement Content

**Goal:** Auto-approve viral/popular jokes regardless of ratings.

```yaml
auto_approve:
  - name: "viral_content"
    conditions:
      - engagement.upvotes: ">= 1000"
      - flags.deleted: "false"
      - flags.spam: "false"
    action: approve
    reason: "Viral content with massive engagement"
    priority: 1

  - name: "highly_engaged"
    conditions:
      - engagement.upvotes: ">= 100"
      - engagement.score: ">= 50"
      - weighted_avg_funniness: ">= 60"
    action: approve
    reason: "High engagement with good quality"
    priority: 2
```

## Policy Templates

### Default Balanced Policy

**File:** `config/import_policies.yaml`

**Use Case:** General-purpose platforms accepting most content types

**Strategy:**
- Auto-approve high quality (4.0+ out of 5) with good ratings
- Auto-reject low quality and empty content
- Flag mature content and borderline quality

```yaml
policies:
  auto_approve:
    - name: "high_quality_popular"
      conditions:
        - weighted_avg_funniness: ">= 4.0"
        - total_ratings_count: ">= 10"
      reason: "High quality with sufficient ratings"

    - name: "verified_safe_content"
      conditions:
        - verified: true
        - maturity_rating: "in ['G', 'PG']"
      reason: "Verified safe content"

  auto_reject:
    - name: "low_quality_rated"
      conditions:
        - weighted_avg_funniness: "< 2.0"
        - total_ratings_count: ">= 5"
      reason: "Low quality with sufficient ratings"

    - name: "empty_content"
      conditions:
        - text_preview: ""
      reason: "Empty or missing content"

  flag_for_review:
    - name: "mature_content"
      conditions:
        - maturity_rating: "in ['R', 'NC-17']"
      reason: "Mature content requires manual review"

    - name: "borderline_quality"
      conditions:
        - weighted_avg_funniness: ">= 2.0"
        - weighted_avg_funniness: "< 3.0"
        - total_ratings_count: ">= 3"
      reason: "Borderline quality - manual verification needed"
```

### Strict Family-Friendly Policy

**File:** `config/policies/strict.yaml`

**Use Case:** Children's apps, educational platforms, family entertainment

**Strategy:**
- Only approve premium quality (85+) family-safe content
- Reject all NSFW, adult-rated, deleted, or profane content
- Flag PG-13, borderline quality, and missing ratings

**Key Thresholds:**
- Quality: 85+ (premium), 60-80 (flag), <20 (reject)
- Ratings needed: 15+ for approval, 10+ for rejection confidence
- Maturity: G/PG only, R/NC-17 rejected, PG-13 flagged

See [config/policies/strict.yaml](../config/policies/strict.yaml) for full configuration.

### Permissive Quality-Based Policy

**File:** `config/policies/permissive.yaml`

**Use Case:** General entertainment, comedy apps, social media

**Strategy:**
- Accept most content based on quality, not maturity
- Only reject clearly problematic (spam, deleted, very low quality)
- Minimal flagging for edge cases

**Key Thresholds:**
- Quality: 80+ (excellent auto-approve), 60+ (good auto-approve), <20 (reject)
- Ratings needed: 5-10+ depending on quality tier
- Maturity: All ratings accepted if quality is good

See [config/policies/permissive.yaml](../config/policies/permissive.yaml) for full configuration.

### NSFW Adult Content Only

**File:** `config/policies/nsfw_only.yaml`

**Use Case:** 18+ platforms, adult comedy sites

**Strategy:**
- Auto-approve high-quality NSFW/adult content
- Reject family-friendly content (not appropriate for platform)
- Flag PG-13 borderline and extreme content

**Key Thresholds:**
- Quality: 70+ for adult content
- Maturity: R/NC-17 approved, G/PG rejected, PG-13 flagged
- NSFW flag: Required for approval

**WARNING:** This policy accepts adult content. Ensure age verification is in place.

See [config/policies/nsfw_only.yaml](../config/policies/nsfw_only.yaml) for full configuration.

## Best Practices

### 1. Always Check Delete/Remove Flags

**Problem:** Deleted content may have high ratings from before deletion.

**Solution:** Always include these conditions in auto-approve policies:

```yaml
auto_approve:
  - name: "any_approval_policy"
    conditions:
      # ... your quality conditions ...
      - flags.deleted: "false"
      - flags.removed: "false"
      - flags.is_test: "false"
```

### 2. Use Sufficient Ratings with Quality Checks

**Problem:** A joke with 1 five-star rating might not be truly excellent.

**Solution:** Require multiple ratings for confidence:

```yaml
# Good: Combines quality with validation
- weighted_avg_funniness: ">= 80"
- total_ratings_count: ">= 10"

# Risky: High quality but only 1 rating
- weighted_avg_funniness: ">= 80"
# Missing total_ratings_count check!
```

**Recommended Thresholds:**
- Premium approval (85+): 15+ ratings
- Good approval (70+): 10+ ratings
- Moderate approval (60+): 5+ ratings
- Rejection confidence: 5-10+ ratings

### 3. Order Policies by Specificity (Priority)

**Problem:** Generic policies might match before specific ones.

**Solution:** Use `priority` field (higher = earlier):

```yaml
auto_approve:
  # High priority: Specific premium content
  - name: "premium_verified"
    conditions:
      - verified: true
      - weighted_avg_funniness: ">= 90"
    priority: 1

  # Lower priority: General good content
  - name: "good_quality"
    conditions:
      - weighted_avg_funniness: ">= 70"
    priority: 2
```

### 4. Test with Dry-Run First

**Problem:** Mistakes in policies can approve/reject thousands of jokes incorrectly.

**Solution:** Always preview with `--dry-run`:

```bash
# 1. Dry-run to see what would happen
uv run python -m joke_emporium.importers.cli apply-policies <import-id> --dry-run

# 2. Review the output carefully

# 3. Apply if satisfied
uv run python -m joke_emporium.importers.cli apply-policies <import-id>
```

### 5. Flag Borderline Cases, Don't Auto-Decide

**Problem:** Edge cases need human judgment.

**Solution:** Use flag policies generously:

```yaml
# Don't auto-approve/reject borderline quality
flag_for_review:
  - name: "borderline_quality"
    conditions:
      - weighted_avg_funniness: ">= 50"
      - weighted_avg_funniness: "< 70"
    action: flag

# Don't auto-approve with insufficient data
  - name: "insufficient_ratings"
    conditions:
      - total_ratings_count: "< 5"
      - weighted_avg_funniness: ">= 60"
    action: flag
```

### 6. Document Clear Reasons

**Problem:** Future reviewers won't understand why decisions were made.

**Solution:** Always include descriptive `reason` fields:

```yaml
# Good: Clear, actionable reason
- name: "premium_family_content"
  reason: "Premium quality (85+) family-safe content with 15+ ratings"

# Bad: Vague reason
- name: "policy1"
  reason: "Approved"
```

### 7. Validate Policy Configuration

**Problem:** Typos or logic errors in policies.

**Solution:** The engine has built-in validation:

```python
from joke_emporium.importers.policies import PolicyEngine

engine = PolicyEngine.from_yaml("my_policies.yaml")
issues = engine.validate_config()

if issues:
    for issue in issues:
        print(f"WARNING: {issue}")
```

Common validation checks:
- Duplicate policy names
- Empty conditions
- Dangerous patterns (e.g., auto-approve based only on null checks)

### 8. Use Ranges Carefully

**Problem:** Range conditions need multiple condition objects.

**Solution:** Define both bounds separately:

```yaml
# Correct: Both conditions required
conditions:
  - weighted_avg_funniness: ">= 50"
  - weighted_avg_funniness: "< 80"  # Between 50-80

# Wrong: Would need operator like "between" (not supported)
# conditions:
#   - weighted_avg_funniness: "50-80"  # ❌ Invalid
```

## Troubleshooting

### No Jokes Being Approved/Rejected

**Symptom:** All jokes remain pending after applying policies.

**Causes:**
1. Conditions are too strict (no jokes match)
2. Field names are incorrect
3. Values don't match database data

**Solutions:**

```bash
# 1. Check what's in the database
uv run python -m joke_emporium.importers.cli inspect <import-id> --limit 5

# 2. Try a simpler policy to test
# Test with just one condition:
auto_approve:
  - name: "test_policy"
    conditions:
      - flags.deleted: "false"
    action: approve

# 3. Check field values match
# If maturity_rating is null, this won't match:
- maturity_rating: "G"  # Won't match null values
```

### Policies Matching Unexpected Jokes

**Symptom:** Jokes you didn't expect are being approved/rejected.

**Cause:** Missing conditions or operator precedence.

**Solution:** Add more restrictive conditions:

```yaml
# Before: Too broad
auto_approve:
  - name: "high_quality"
    conditions:
      - weighted_avg_funniness: ">= 80"
      # Missing safety checks!

# After: More restrictive
auto_approve:
  - name: "high_quality"
    conditions:
      - weighted_avg_funniness: ">= 80"
      - total_ratings_count: ">= 10"  # Add validation
      - flags.nsfw: "false"           # Add safety
      - flags.deleted: "false"        # Add cleanup check
```

### JSON Field Not Working

**Symptom:** Conditions on `flags.*` or `engagement.*` don't match.

**Causes:**
1. Field is actually null/missing in database
2. Typo in field name
3. JSON not properly stored

**Solutions:**

```yaml
# Check if field exists first
flag_for_review:
  - name: "check_nsfw_exists"
    conditions:
      - flags.nsfw: "is_null"
    action: flag
    reason: "Missing NSFW flag"

# Then use the field
auto_approve:
  - name: "safe_content"
    conditions:
      - flags.nsfw: "== false"  # Only matches if field exists and is false
```

### Performance Issues

**Symptom:** Policy application is slow.

**Solutions:**

1. **Use batch commits** (default: 1000 jokes per commit):
   ```bash
   # Larger batches for better performance on large imports
   # (Note: batch_size is currently hardcoded, but can be modified in code)
   ```

2. **Simplify conditions:**
   ```yaml
   # Slow: Many complex JSON field accesses
   conditions:
     - flags.nsfw: "false"
     - flags.deleted: "false"
     - flags.removed: "false"
     - flags.spam: "false"
     - engagement.upvotes: ">= 100"
     - engagement.score: ">= 50"

   # Faster: Use direct fields when possible
   conditions:
     - weighted_avg_funniness: ">= 80"
     - total_ratings_count: ">= 10"
     - flags.deleted: "false"  # Only essential JSON fields
   ```

3. **Order policies by likelihood:**
   ```yaml
   # Put common matches first with high priority
   auto_reject:
     - name: "deleted_content"  # Likely to match many
       priority: 1
       conditions:
         - flags.deleted: "true"

     - name: "rare_edge_case"   # Rarely matches
       priority: 10
       conditions:
         # Complex conditions
   ```

### Policy Not Loading

**Symptom:** Error when loading YAML file.

**Causes:**
1. YAML syntax error
2. Invalid operator
3. Missing required fields

**Solutions:**

```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('my_policies.yaml'))"

# Validate policy structure
python -c "
from joke_emporium.importers.policies import PolicyEngine
try:
    engine = PolicyEngine.from_yaml('my_policies.yaml')
    print('✓ Policy loaded successfully')
except Exception as e:
    print(f'✗ Error: {e}')
"
```

Common YAML errors:
```yaml
# Wrong: Inconsistent indentation
policies:
  auto_approve:
  - name: "test"
    conditions:
      - field: "value"  # ❌ Should align with 'name'

# Correct: Consistent indentation
policies:
  auto_approve:
    - name: "test"
      conditions:
        - field: "value"  # ✓ Aligned properly
```

## Performance Tips

### Processing Large Batches Efficiently

For imports with 100k+ jokes:

1. **Use Default Batch Commits:**
   - Engine commits every 1000 jokes automatically
   - Prevents memory issues
   - Provides progress logging

2. **Run During Off-Peak Hours:**
   - Policy application is CPU-intensive
   - Plan for 1000 jokes/second on standard hardware

3. **Monitor Progress:**
   ```bash
   # Watch logs for progress updates
   uv run python -m joke_emporium.importers.cli apply-policies <import-id>
   # Output shows: "Processed 1000/195000 jokes..."
   ```

### Optimizing Policy Evaluation

1. **Put Fast Checks First:**
   ```yaml
   # Good: Check simple fields first
   conditions:
     - flags.deleted: "false"        # Fast: direct field
     - total_ratings_count: ">= 10"  # Fast: direct field
     - weighted_avg_funniness: ">= 80"  # Fast: direct field
     - flags.nsfw: "false"           # Slower: JSON parsing

   # Less optimal: Complex checks first
   conditions:
     - engagement.upvotes: ">= 100"  # Slower: JSON + nested access
     - flags.deleted: "false"        # Should be first
   ```

2. **Use Priority for Common Patterns:**
   ```yaml
   auto_reject:
     # High priority: Catches 30% of jokes quickly
     - name: "deleted_content"
       priority: 1
       conditions:
         - flags.deleted: "true"

     # Lower priority: Rare edge case
     - name: "complex_check"
       priority: 10
       conditions:
         # Many conditions
   ```

3. **Minimize Redundant Checks:**
   ```yaml
   # Inefficient: Checking deleted flag in every policy
   auto_approve:
     - name: "policy1"
       conditions:
         - flags.deleted: "false"  # Repeated
         - condition1: "value"

     - name: "policy2"
       conditions:
         - flags.deleted: "false"  # Repeated
         - condition2: "value"

   # Better: Reject deleted first, then approve clean jokes
   auto_reject:
     - name: "deleted"
       priority: 1
       conditions:
         - flags.deleted: "true"

   auto_approve:
     - name: "policy1"
       conditions:
         - condition1: "value"  # No need to check deleted
     - name: "policy2"
       conditions:
         - condition2: "value"  # Already filtered out
   ```

### Expected Performance

Benchmark results on taivop dataset (195k jokes):

| Operation | Time | Rate |
|-----------|------|------|
| Load policies from YAML | <100ms | - |
| Evaluate single joke | <1ms | 1000+ jokes/sec |
| Apply to 195k jokes (balanced policy) | ~3 minutes | ~1000 jokes/sec |
| Apply to 195k jokes (strict policy) | ~4 minutes | ~800 jokes/sec |
| Dry-run (no commits) | ~2 minutes | ~1600 jokes/sec |

Factors affecting speed:
- Number of policies (more policies = slower)
- Complexity of conditions (JSON fields slower than direct)
- Database I/O (commit frequency)
- Available CPU/memory

## Advanced Patterns

### Conditional Chaining

Use priority to create decision trees:

```yaml
auto_approve:
  # Tier 1: Premium content
  - name: "tier1_premium"
    priority: 1
    conditions:
      - weighted_avg_funniness: ">= 90"
      - total_ratings_count: ">= 20"
    reason: "Tier 1: Premium quality"

  # Tier 2: Excellent content
  - name: "tier2_excellent"
    priority: 2
    conditions:
      - weighted_avg_funniness: ">= 80"
      - total_ratings_count: ">= 15"
    reason: "Tier 2: Excellent quality"

  # Tier 3: Good content
  - name: "tier3_good"
    priority: 3
    conditions:
      - weighted_avg_funniness: ">= 70"
      - total_ratings_count: ">= 10"
    reason: "Tier 3: Good quality"
```

### Platform-Specific Multi-Config

Maintain different configs for different deployments:

```bash
# Production: Strict family-friendly
uv run python -m joke_emporium.importers.cli apply-policies $ID --config config/policies/strict.yaml

# Staging: Permissive for testing
uv run python -m joke_emporium.importers.cli apply-policies $ID --config config/policies/permissive.yaml

# Adult site: NSFW only
uv run python -m joke_emporium.importers.cli apply-policies $ID --config config/policies/nsfw_only.yaml
```

### A/B Testing Policies

Compare policy outcomes:

```bash
# Apply policy A
uv run python -m joke_emporium.importers.cli apply-policies $ID --config policy_a.yaml --dry-run > results_a.txt

# Apply policy B
uv run python -m joke_emporium.importers.cli apply-policies $ID --config policy_b.yaml --dry-run > results_b.txt

# Compare
diff results_a.txt results_b.txt
```

### Audit Trail

Every policy action stores:
- `review_status`: APPROVED/REJECTED/UNDER_REVIEW
- `review_notes`: Policy name and reason
- `reviewed_at`: Timestamp
- `reviewed_by`: "policy_engine"

Query results:

```python
from joke_emporium.db.session import get_staging_session
from joke_emporium.db.models.staging import StagingJokeDB, ReviewStatus

with get_staging_session() as session:
    # Find all auto-approved jokes
    approved = session.query(StagingJokeDB).filter(
        StagingJokeDB.review_status == ReviewStatus.APPROVED,
        StagingJokeDB.reviewed_by == "policy_engine"
    ).all()

    for joke in approved:
        print(f"Joke {joke.id}: {joke.review_notes}")
```

---

## Summary

The Policy Engine provides powerful, flexible automation for joke review:

**Key Takeaways:**
1. Start with built-in templates, customize as needed
2. Always use `--dry-run` before applying new policies
3. Combine quality and quantity checks for confidence
4. Flag borderline cases instead of auto-deciding
5. Document reasons clearly for audit trail
6. Test policies on small batches first

**Next Steps:**
- Review [config/import_policies.yaml](../config/import_policies.yaml) for default policies
- Try specialized templates in [config/policies/](../config/policies/)
- Create custom policies for your use case
- Share successful patterns with the community

For questions or contributions, see the main [README_IMPORT_FRAMEWORK.md](../README_IMPORT_FRAMEWORK.md).
