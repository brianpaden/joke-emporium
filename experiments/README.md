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
- ⏳ **`test_normalization.py`** - Test different text normalization approaches (future)
- ⏳ **`analyze_performance.py`** - Performance analysis on varying dataset sizes (future)

## Quick Start

### 1. Find Natural Duplicates

```bash
uv run python experiments/scripts/find_natural_duplicates.py
```

Output: `experiments/output/natural_duplicates.json`

### 2. Mine Edge Cases

```bash
uv run python experiments/scripts/mine_edge_cases.py
```

Output: `experiments/output/edge_cases.json`

### 3. Create Test Fixtures

```bash
uv run python experiments/scripts/sample_real_jokes.py
```

Output: `tests/fixtures/real_joke_samples.json`

## Data Sources

All scripts use the taivop dataset downloaded to `temp/imports/taivop_joke-dataset/`:

- `reddit_jokes.json` (194,553 jokes)
- `stupidstuff.json` (3,773 jokes)
- `wocka.json` (10,019 jokes)

**Total: 208,345 jokes**

## Related Documentation

- [DEDUPLICATION_EXPERIMENTS.md](../docs/experiments/DEDUPLICATION_EXPERIMENTS.md) - Detailed experiment plan
- [REAL_DATA_INTEGRATION.md](../docs/experiments/REAL_DATA_INTEGRATION.md) - Real data integration strategy

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
