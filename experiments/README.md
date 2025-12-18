# Joke Emporium Experiments

This directory contains experimental scripts and analysis for deduplication research and data exploration.

## Directory Structure

```
experiments/
├── scripts/           # Python scripts for data analysis
├── output/            # Generated results, reports, and data files
├── notebooks/         # Jupyter notebooks for interactive exploration (future)
└── README.md          # This file
```

## Available Scripts

### Data Analysis

- ✅ **`find_natural_duplicates.py`** - Find naturally occurring duplicates across taivop sources
- ✅ **`mine_edge_cases.py`** - Extract edge cases from real data (short, long, unicode, etc.)
- ✅ **`create_variations.py`** - Generate controlled variations of real jokes for testing
- ✅ **`sample_real_jokes.py`** - Create realistic test fixtures from taivop data

### Deduplication Testing

- ✅ **`benchmark_similarity.py`** - Benchmark different similarity metrics
- ✅ **`test_normalization.py`** - Validate normalization strategies against real data
- ✅ **`measure_semantic_duplicates.py`** - Measure semantic duplicate rate to assess embedding value
- 🆕 **`test_enhanced_normalization.py`** - Test enhanced normalization (articles, stop words) on semantic duplicates
- ⏳ **`analyze_performance.py`** - Performance analysis on varying dataset sizes (future)

### Content & Maturity Rating Analysis

- 🆕 **`analyze_maturity_ratings.py`** - Analyze content distribution and suggest maturity ratings
- 🆕 **`test_profanity_detection.py`** - Compare profanity detection libraries (better-profanity, profanity-check, custom)

## Quick Start

### 1. Find Natural Duplicates

```bash
uv run python experiments/scripts/find_natural_duplicates.py
```

**Output:** `experiments/output/natural_duplicates.json` - All duplicate groups found in 208k jokes

### 2. Mine Edge Cases

```bash
uv run python experiments/scripts/mine_edge_cases.py
```

**Output:** `experiments/output/edge_cases.json` - Edge cases by category

### 3. Create Test Fixtures

```bash
uv run python experiments/scripts/sample_real_jokes.py
```

**Output:** `tests/fixtures/real_joke_samples.json` - Diverse samples for testing

### 4. Benchmark Similarity Metrics

```bash
uv run python experiments/scripts/benchmark_similarity.py
```

**Output:** `experiments/output/benchmark_*.json` - Performance metrics for each approach

### 5. Test Normalization Strategies

```bash
uv run python experiments/scripts/test_normalization.py
```

Validates the data-driven normalization approach against real data.

**Output:** `experiments/output/normalization_test_results.json` - Validation results

### 6. Measure Semantic Duplicate Rate (Optional)

```bash
# Install dependencies first (downloads ~500MB model on first run)
uv pip install sentence-transformers scikit-learn tqdm

# Run experiment (takes 1-2 minutes for 2k sample)
uv run python experiments/scripts/measure_semantic_duplicates.py
```

Measures how many "semantic-only" duplicates exist - jokes that are similar in meaning but different in text. This determines whether semantic embeddings (BERT, Word2Vec) would add value beyond hash-based deduplication.

**Performance:**
- 2,000 jokes = ~2M comparisons (~1-2 minutes)
- 5,000 jokes = ~12.5M comparisons (~5-10 minutes)
- 10,000 jokes = ~50M comparisons (~20-30 minutes)

**Output:** `experiments/output/semantic_duplicate_analysis.json` - Rate and examples

**Decision criteria:**
- If <0.5%: Embeddings not worth the cost (stick with hash + Levenshtein)
- If 0.5-1%: Consider for Phase 3 (marginal benefit)
- If >1%: Should prioritize for Phase 2/3 (significant value)

**Note:** This experiment requires additional dependencies and is optional for Sprint 3.

### 7. Test Enhanced Normalization

```bash
# Run after measuring semantic duplicates (step 6)
uv run python experiments/scripts/test_enhanced_normalization.py
```

Tests whether enhanced normalization (article removal, stop word filtering) can catch the "semantic duplicates" found by embeddings using simple text-based normalization instead of expensive embeddings.

**Input:** `experiments/output/semantic_duplicate_analysis.json` (from step 6)

**Output:** `experiments/output/enhanced_normalization_test.json` - Improvement metrics

**Expected findings:**
- Enhanced normalization catches 15-30% more duplicates than baseline
- Remaining duplicates are true retellings needing Levenshtein
- Validates whether to implement enhanced normalization in Sprint 3

### 8. Analyze Maturity Ratings

```bash
uv run python experiments/scripts/analyze_maturity_ratings.py
```

Analyzes jokes for content patterns to understand maturity rating distribution and content flags.

**Output:** `experiments/output/maturity_rating_analysis.json` - Content analysis results

**Analysis includes:**
- Profanity severity distribution (mild, moderate, strong)
- Sexual content detection (explicit terms, innuendo)
- Dark humor patterns (death, mortality themes)
- Violence indicators
- Suggested rating distribution (G, PG, PG-13, R, X)

### 9. Test Profanity Detection Libraries

```bash
# Install optional dependencies
uv pip install better-profanity

# Run comparison
uv run python experiments/scripts/test_profanity_detection.py
```

Compares profanity detection approaches for automatic content flagging.

**Output:** `experiments/output/profanity_detection_comparison.json` - Library comparison

**Libraries tested:**
- better-profanity (fast wordlist-based)
- profanity-check (ML-based, optional)
- Custom wordlist (joke-specific severity levels)

**Metrics:**
- Detection rate and accuracy
- Performance (jokes/second)
- Agreement between libraries

## Data Sources

All scripts use the taivop dataset downloaded to `temp/imports/taivop_joke-dataset/`:

- `reddit_jokes.json` (194,553 jokes)
- `stupidstuff.json` (3,773 jokes)
- `wocka.json` (10,019 jokes)

**Total: 208,345 jokes**

## Related Documentation

- [DEDUPLICATION_EXPERIMENTS.md](../docs/experiments/DEDUPLICATION_EXPERIMENTS.md) - Detailed deduplication experiment plan
- [REAL_DATA_INTEGRATION.md](../docs/experiments/REAL_DATA_INTEGRATION.md) - Real data integration strategy
- [MATURITY_RATING_EXPERIMENTS.md](../docs/experiments/MATURITY_RATING_EXPERIMENTS.md) - Content classification and maturity rating experiments
- [NORMALIZATION_STRATEGIES.md](../docs/experiments/NORMALIZATION_STRATEGIES.md) - Text normalization research

## Results Summary

**Key Findings from Real Data Analysis:**

- **208,345 jokes analyzed** across 3 sources
- **2,590 duplicate groups found** (3.7% duplication rate)
- **Hash-based exact match achieves 100% recall** on real duplicates
- **Aggressive normalization achieves 68.5% recall** on variations
- **Performance: 3.6M comparisons/sec** (exact match)

See [EXPERIMENT_RESULTS.md](output/EXPERIMENT_RESULTS.md) for detailed findings.

**Recommendation:** Hybrid approach (exact + fuzzy fallback) for 99%+ coverage.

## Output Files

Generated files are stored in `experiments/output/` and excluded from git.

**Analysis Results:**
- `ANALYSIS_SUMMARY.md` - High-level findings
- `EXPERIMENT_RESULTS.md` - Detailed experiment results
- `natural_duplicates.json` - 2,590 duplicate groups
- `edge_cases.json` - Edge case examples by category
- `benchmark_duplicates.json` - Performance metrics
- `benchmark_variations.json` - Variation detection results

**Test Fixtures** (in `tests/fixtures/`):
- `real_joke_samples.json` - Diverse samples by category
- `real_jokes_compact.json` - 25 jokes for quick tests
- `edge_case_samples.json` - Edge cases for testing
- `variation_test_set.json` - Controlled variations

Common output formats:
- JSON: Test fixtures, duplicate groups
- CSV: Performance metrics, benchmark results
- TXT: Summary reports

## Notes

- Scripts are designed to work with the existing taivop data download
- All paths are relative to the repository root
- Output files are gitignored to avoid committing large datasets
