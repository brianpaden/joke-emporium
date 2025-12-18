# Maturity Rating & Content Classification Experiments

**Purpose:** Research and validate approaches for automatically detecting and categorizing joke content to assign appropriate maturity ratings and content flags.

**Status:** Planning / Experimental
**Created:** 2025-12-17

---

## Overview

This document explores strategies for analyzing joke content to:
1. Automatically suggest maturity ratings (G, PG, PG-13, R, X)
2. Detect and flag content types (profanity, sexual, dark humor, offensive, etc.)
3. Validate rating consistency across the dataset
4. Identify edge cases requiring manual review

### Current Schema

**MaturityRating Enum** (from `models/enums.py`):
- `G` - General - all ages
- `PG` - Parental guidance - may reference adult themes mildly
- `PG13` - Parents strongly cautioned - mild profanity, innuendo
- `R` - Restricted - strong profanity, explicit themes
- `X` - Adults only - extremely explicit

**ContentFlags Model** (from `models/flags.py`):
- `profanity`: Contains profanity or strong language
- `dark_humor`: Contains dark, morbid, or gallows humor
- `offensive`: May be offensive to some audiences
- `political`: Contains political content or satire
- `sexual`: Contains sexual content or innuendo
- `violent`: Contains violent or graphic content
- `stereotypical`: Uses stereotypes or potentially insensitive characterizations
- `religious`: Contains religious content or themes
- `requires_context`: Requires specific cultural or contextual knowledge

---

## Standardized Rating Definitions

### MPAA Film Rating System

Based on the Motion Picture Association rating system, which provides clear guidelines:

**G (General Audiences):**
- **Language:** Common everyday expressions, no stronger words
- **Violence:** Minimal depictions
- **Nudity/Sex:** None
- **Drug Use:** None

**PG (Parental Guidance Suggested):**
- **Language:** Some profanity possible
- **Violence:** Some depictions (not intense)
- **Nudity/Sex:** Brief nudity possible
- **Drug Use:** None

**PG-13 (Parents Strongly Cautioned):**
- **Language:** One use of harsher sexually-derived expletive allowed; more than one requires R
- **Violence:** Depictions allowed, but generally not both realistic AND extreme/persistent
- **Nudity/Sex:** More than brief nudity requires PG-13, but generally not sexually oriented
- **Drug Use:** Drug use content may require PG-13

**R (Restricted):**
- **Language:** Hard language, multiple uses of strong expletives
- **Violence:** Intense or persistent violence
- **Nudity/Sex:** Sexually-oriented nudity, adult themes, adult activity
- **Drug Use:** Drug abuse

**NC-17/X (Adults Only):**
- **Content:** Extreme violence, explicit sexual activity, aberrational behavior
- **Note:** Most parent would consider too strong for children

### TV Parental Guidelines System

Alternative system with content descriptors:

**Content Descriptors:**
- **D** (Suggestive Dialogue) - Sexual references
- **L** (Language) - Coarse/offensive language, profanity, vulgar slang, racial slurs
- **S** (Sexual Content) - Visual innuendo and intercourse
- **V** (Violence) - Violent content

---

## Experiment Plan

### Experiment 1: Profanity Detection Baseline

**Goal:** Evaluate profanity detection libraries on real joke data

**Libraries to Test:**
1. **better-profanity** - Fast, wordlist-based, leetspeak detection
2. **profanity-check** - ML-based, context-aware
3. **profanity-filter** - Fuzzy matching with Levenshtein

**Metrics:**
- Precision: % of flagged jokes that actually contain profanity
- Recall: % of profane jokes that are detected
- False positive rate: Clean jokes flagged as profane
- Performance: Jokes processed per second

**Test Set:**
- Sample 1,000 random jokes from taivop dataset
- Manual annotation of 100 jokes for ground truth
- Include edge cases: euphemisms, creative spellings, context-dependent words

**Script:** `experiments/scripts/test_profanity_detection.py`

### Experiment 2: Content Analysis & Maturity Rating

**Goal:** Develop multi-factor content analysis to suggest maturity ratings

**Content Factors to Analyze:**

1. **Profanity Severity**
   - Mild: "damn", "hell", "crap"
   - Moderate: "ass", "bitch", "shit"
   - Strong: "f*ck" and derivatives
   - Extreme: Sexually explicit terms

2. **Sexual Content Detection**
   - Innuendo patterns (double entendre)
   - Sexual terminology
   - Body part references in sexual context
   - Explicit descriptions

3. **Violence Indicators**
   - Death/killing references
   - Injury/harm descriptions
   - Weapon mentions
   - Graphic violence terms

4. **Dark Humor Markers**
   - Death/mortality themes
   - Tragedy references
   - Morbid situations
   - Gallows humor patterns

5. **Offensive Content**
   - Stereotype usage (racial, gender, religious, etc.)
   - Slurs or derogatory terms
   - Sensitive topics (disability, tragedy, etc.)

**Rating Algorithm:**

```python
def suggest_maturity_rating(joke_text: str) -> tuple[MaturityRating, ContentFlags]:
    """Suggest maturity rating based on content analysis."""

    # Initialize flags
    flags = ContentFlags()

    # Analyze profanity
    profanity_level = analyze_profanity(joke_text)
    flags.profanity = profanity_level > 0

    # Analyze sexual content
    sexual_score = analyze_sexual_content(joke_text)
    flags.sexual = sexual_score > SEXUAL_THRESHOLD

    # Analyze violence
    violence_score = analyze_violence(joke_text)
    flags.violent = violence_score > VIOLENCE_THRESHOLD

    # Analyze dark humor
    dark_humor_score = analyze_dark_humor(joke_text)
    flags.dark_humor = dark_humor_score > DARK_HUMOR_THRESHOLD

    # Determine rating based on highest severity
    if profanity_level >= EXTREME or sexual_score >= EXPLICIT:
        rating = MaturityRating.X
    elif profanity_level >= STRONG or sexual_score >= HIGH or violence_score >= HIGH:
        rating = MaturityRating.R
    elif profanity_level >= MODERATE or sexual_score >= MODERATE:
        rating = MaturityRating.PG13
    elif profanity_level >= MILD or sexual_score >= MILD:
        rating = MaturityRating.PG
    else:
        rating = MaturityRating.G

    return rating, flags
```

**Script:** `experiments/scripts/analyze_maturity_ratings.py`

### Experiment 3: Dataset Distribution Analysis

**Goal:** Understand maturity rating distribution in existing data

**Analysis:**
- Count jokes by category in taivop dataset
- Identify common profanity patterns
- Find edge cases requiring manual review
- Validate that auto-ratings match manual expectations

**Outputs:**
- Distribution histogram (G vs PG vs PG-13 vs R vs X)
- Common profanity words and frequencies
- False positive examples
- Ambiguous cases requiring rules refinement

**Script:** `experiments/scripts/analyze_dataset_maturity.py`

### Experiment 4: Custom Wordlists & Calibration

**Goal:** Build joke-specific profanity lists and calibrate thresholds

**Approach:**
1. Extract all flagged terms from dataset
2. Manually categorize by severity (mild, moderate, strong, extreme)
3. Build custom wordlists for better-profanity
4. Test with different threshold combinations
5. Optimize for F1 score on validation set

**Wordlist Categories:**
- **Mild:** Socially acceptable in PG contexts
- **Moderate:** Requires PG-13 (single use acceptable)
- **Strong:** Requires R rating (or multiple uses → R)
- **Extreme:** Automatically X rating
- **Euphemisms:** Mild substitutes (track separately)

**Script:** `experiments/scripts/calibrate_profanity_thresholds.py`

### Experiment 5: Multi-Dimensional Classification

**Goal:** Test whether content flags improve rating accuracy

**Hypothesis:** Combining multiple content signals (profanity + sexual + violence) produces more accurate ratings than profanity alone.

**Test:**
1. Rate jokes with profanity-only analyzer
2. Rate jokes with multi-dimensional analyzer
3. Compare against manual ground truth
4. Measure accuracy improvement

**Metrics:**
- Accuracy: % correct ratings
- Cohen's Kappa: Inter-rater reliability
- Confusion matrix: Which ratings are confused most often

**Script:** `experiments/scripts/test_multidimensional_classification.py`

---

## Implementation Strategy

### Phase 1: Profanity Detection (Sprint 4)

1. Install and evaluate profanity detection libraries
2. Run `test_profanity_detection.py` on sample dataset
3. Choose best library (likely `better-profanity` for speed)
4. Create custom wordlists for joke-specific terms

### Phase 2: Content Analysis Module (Sprint 4)

1. Create `src/joke_emporium/analysis/` module
2. Implement `ContentAnalyzer` class
3. Add methods for each content type:
   - `analyze_profanity()`
   - `analyze_sexual_content()`
   - `analyze_violence()`
   - `analyze_dark_humor()`
   - `suggest_maturity_rating()`

### Phase 3: Integration with Import Pipeline (Sprint 5)

1. Add content analysis to `BaseImporter.transform()`
2. Auto-populate `maturity_rating` and `flags` fields
3. Add review flag for low-confidence ratings
4. Allow manual override during staging review

### Phase 4: Validation & Refinement (Ongoing)

1. Track auto-rating vs manual-rating discrepancies
2. Refine thresholds based on real usage
3. Build training set for potential ML classifier (future)

---

## Expected Outcomes

### Success Criteria

1. **High Recall for Profanity:** 95%+ of profane jokes detected
2. **Low False Positives:** <5% of clean jokes flagged
3. **Rating Accuracy:** 80%+ agreement with manual ratings
4. **Performance:** Process 1000+ jokes/second
5. **Coverage:** Auto-rate 90%+ of imports (10% manual review)

### Deliverables

1. **Documentation:**
   - Maturity rating guidelines (this document)
   - Profanity detection evaluation report
   - Custom wordlist documentation

2. **Code:**
   - `ContentAnalyzer` class in `src/joke_emporium/analysis/`
   - Profanity wordlists in `data/wordlists/`
   - Integration with import pipeline

3. **Experiment Results:**
   - `experiments/output/profanity_detection_comparison.json`
   - `experiments/output/maturity_rating_distribution.json`
   - `experiments/output/content_analysis_validation.json`

---

## Open Questions

1. **Context Sensitivity:** How do we handle words that are profane in some contexts but not others?
   - Example: "ass" in "donkey" vs "kick your ass"

2. **Cultural Variations:** Different cultures have different profanity standards. Do we need region-specific ratings?

3. **Innuendo Detection:** Sexual innuendo is hard to detect algorithmically. Do we need ML or can rules suffice?

4. **Rating Appeals:** Should we allow users to dispute auto-ratings during import review?

5. **Multi-Language:** When we expand beyond English, do rating standards differ by language/culture?

---

## References

### External Resources

- [MPAA Film Rating System](https://www.filmratings.com/)
- [TV Parental Guidelines](https://www.tvguidelines.org/)
- [better-profanity Documentation](https://pypi.org/project/better-profanity/)
- [profanity-check Documentation](https://pypi.org/project/profanity-check/)
- [OWASP Content Classification](https://owasp.org/www-community/controls/Content_Classification)

### Internal Documentation

- [Joke Schema Documentation](../SCHEMA_OUTLINE.md)
- [Import Framework Guide](../../README_IMPORT_FRAMEWORK.md)
- [Database Schema](../DATABASE.md)
- [Deduplication Experiments](DEDUPLICATION_EXPERIMENTS.md)

---

## Experiment Timeline

**Sprint 4 (Current):**
- ✅ Research standardized rating definitions
- ⏳ Create experiment plan (this document)
- ⏳ Implement `test_profanity_detection.py`
- ⏳ Implement `analyze_maturity_ratings.py`
- ⏳ Run initial profanity detection tests
- ⏳ Choose profanity library

**Sprint 5 (Future):**
- Implement `ContentAnalyzer` module
- Create custom wordlists
- Integrate with import pipeline
- Validate on full dataset

**Sprint 6 (Future):**
- Refine thresholds based on real data
- Build comprehensive test suite
- Document rating guidelines for manual review
- Consider ML-based classifier for ambiguous cases
