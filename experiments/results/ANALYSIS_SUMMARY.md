# Taivop Dataset Analysis Summary

**Date:** 2025-12-16
**Dataset:** taivop/joke-dataset (~208k jokes)

---

## Key Findings

### 1. Natural Duplicates

**Total Jokes Analyzed:** 208,345
- reddit_jokes: 194,553
- stupidstuff: 3,773
- wocka: 10,019

**Duplicate Statistics:**
- **Unique jokes:** 200,551 (96.3%)
- **Duplicate groups:** 2,590 (3.7%)
- **Cross-source duplicates:** 14 (0.007%)
- **Same-source duplicates:** 2,576 (99.5% of duplicates)

**Conclusion:** Almost all duplicates are within the same source (primarily Reddit), with very few duplicates across different sources.

### 2. Top Duplicated Jokes (Reddit)

1. "What's brown and rhymes with Snoop? Dr. Dre" - **44 copies**
2. "What's brown and sticky? A stick." - **39 copies**
3. "What do you get when you cross a joke with a rhetorical question?" - **39 copies**
4. "Why did the chicken cross the road? To get to the other side." - **30 copies**
5. "Donald Trump" - **26 copies** (just those two words!)

### 3. Edge Cases Found

| Category | Count | % of Total |
|----------|-------|-----------|
| **Ellipsis** | 48,264 | 23.2% |
| **Has numbers** | 34,856 | 16.7% |
| **Very long** (>500 chars) | 31,300 | 15.0% |
| **Multiline** | 30,229 | 14.5% |
| **Shouting** (CAPS) | 20,568 | 9.9% |
| **Short** (<100 chars) | 15,644 | 7.5% |
| **Long** (>300 chars) | 12,705 | 6.1% |
| **Unicode** | 7,814 | 3.8% |
| **Empty body** | 4,103 | 2.0% |
| **Code-like** | 1,759 | 0.8% |
| **Contains URL** | 1,194 | 0.6% |
| **Punctuation heavy** | 1,178 | 0.6% |
| **Very short** (<20 chars) | 702 | 0.3% |
| **Empty** | 581 | 0.3% |
| **Emoji** | 517 | 0.2% |
| **Number heavy** | 516 | 0.2% |
| **Unicode heavy** | 79 | 0.04% |

### 4. Implications for Deduplication

#### Same-Source Duplicates (Reddit)
- **High frequency**: Some jokes appear 20-44 times
- **Cause**: Users reposting popular jokes on Reddit
- **Strategy**: Hash-based exact match will catch 99% of these

#### Cross-Source Duplicates
- **Very rare**: Only 14 cases across 208k jokes
- **Conclusion**: Different sources have minimal overlap
- **Strategy**: Don't need expensive cross-source comparison

#### Text Normalization Requirements
- **Ellipsis**: 23% of jokes have "..." - preserve timing markers
- **Multiline**: 14.5% have multiple lines - normalize whitespace carefully
- **CAPS**: 10% have shouting - case-folding is important
- **Numbers**: 17% have numbers - may need "3" vs "three" normalization
- **Unicode**: 3.8% have unicode - need proper normalization (NFC)

### 5. Recommended Deduplication Approach

Based on this analysis:

1. **Primary Strategy: Hash-based exact match**
   - Will catch 99%+ of duplicates (same-source Reddit reposts)
   - Fast: O(1) lookup
   - Simple to implement

2. **Normalization:**
   - Case-fold (casefold(), not lower())
   - Unicode normalize (NFC)
   - Trim whitespace
   - Normalize line breaks (\r\n → \n)
   - **Preserve** ellipsis and timing markers

3. **Secondary Strategy (optional):**
   - Levenshtein similarity for near-duplicates (typos)
   - Only needed for high-value imports
   - Threshold: 95%+ similarity

4. **Cross-Source:**
   - Don't optimize for this - only 14 cases
   - Standard normalization will catch these

### 6. Test Fixtures Created

**Files Generated:**
- `tests/fixtures/real_joke_samples.json` (215 KB) - Diverse samples by category
- `tests/fixtures/real_jokes_compact.json` (19 KB) - 25 diverse jokes for quick tests
- `tests/fixtures/edge_case_samples.json` (13 KB) - Edge cases by category
- `experiments/output/natural_duplicates.json` (221 KB) - Top 100 duplicate groups
- `experiments/output/natural_duplicates_full.json` (1.9 MB) - All 2,590 duplicate groups
- `experiments/output/edge_cases.json` (221 KB) - 20 examples per edge case category

### 7. Next Steps

1. ✅ Mine natural duplicates
2. ✅ Identify edge cases
3. ✅ Create real test fixtures
4. **TODO:** Benchmark normalization strategies
5. **TODO:** Test similarity metrics on real duplicates
6. **TODO:** Measure performance on 200k dataset

---

## Data Quality Notes

- **Shortest valid joke:** 15 chars ("I love to Poop.")
- **Longest joke:** 578+ chars (multi-paragraph stories)
- **Most common length:** 50-150 chars
- **Reddit dominates:** 93% of all jokes
- **Duplicate rate:** ~3.7% (mostly Reddit reposts)
