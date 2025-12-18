# Future Maturity Rating Experiments

**Purpose:** Document follow-up experiments based on initial findings from maturity rating analysis.

**Created:** 2025-12-17
**Status:** Planning - Prioritized based on initial experiment results

---

## Initial Findings Summary

From experiments run on 500-1,000 jokes from taivop dataset:

### Content Distribution
- **84.8% clean** (no profanity)
- **7.9% mild** profanity (damn, hell, ass)
- **3.7% moderate** profanity (shit, bitch, dick)
- **3.6% strong** profanity (fuck, cunt)
- **6.6% sexual** content (explicit terms)
- **0.8% innuendo** (likely severe undercount)
- **9.4% dark humor**
- **6.0% violence**

### Library Comparison
- **better-profanity:** 23.0% flagged, 21.5 jokes/sec, many false positives
- **Custom wordlist:** 14.2% flagged, 242,193 jokes/sec, more conservative
- **Agreement:** 83.2% (16.8% disagreement is significant)

### Critical Issues Identified
1. **False positives** - "compass" flagged for "ass", "Nazi" flagged as profanity
2. **No context awareness** - Can't distinguish "ass" (donkey) from "ass" (profanity)
3. **Weak innuendo detection** - Only 0.8% detected (way too low)
4. **Performance gap** - better-profanity 11,200x slower than custom
5. **Missing severity** - better-profanity only returns yes/no, not mild/moderate/strong

---

## Prioritized Experiment Queue

### 🔥 High Priority (Do Next)

#### Experiment 6: Context-Aware Profanity Detection

**Goal:** Reduce false positives by checking word context

**Problem:** Simple string matching flags "compass" for "ass", "hello" for "hell"

**Approach:**
```python
# Whitelist patterns that contain profane substrings but aren't profane
FALSE_POSITIVE_PATTERNS = {
    "ass": r"\b(compass|class|grass|pass|bass|mass|brass|massage|ambassador)\b",
    "hell": r"\b(hello|shell|michelle|hell's kitchen|shelling)\b",
    "cock": r"\b(peacock|cockpit|hancock|hitchcock|gamecock)\b",
    "dick": r"\b(dickens|moby dick|benedict|predict|dictate|verdict)\b",
    "nazi": r"\b(ashkenazi)\b",  # Jewish surname
}

def is_profanity_in_context(text: str, word: str) -> bool:
    """Check if word is actually profane in this context."""
    text_lower = text.lower()

    # Check for false positive patterns
    if word in FALSE_POSITIVE_PATTERNS:
        pattern = FALSE_POSITIVE_PATTERNS[word]
        if re.search(pattern, text_lower):
            return False  # Found in safe context

    # Check word boundaries (not part of larger word)
    if not re.search(rf"\b{word}\b", text_lower):
        return False

    return True
```

**Expected Outcomes:**
- Reduce false positive rate from 12.8% to <5%
- Maintain high recall (still catch real profanity)
- Minimal performance impact

**Metrics:**
- False positive rate
- False negative rate (don't miss real profanity)
- Precision/recall/F1 score

**Script:** `experiments/scripts/test_context_aware_detection.py`

**Deliverables:**
- Context-aware profanity detector
- False positive pattern library
- Comparison report vs baseline

---

#### Experiment 9: Calibrate Rating Thresholds

**Goal:** Find optimal thresholds for G/PG/PG-13/R boundaries

**Problem:** Current logic is ad-hoc and untested:
```python
if strong_count > 0: R
elif moderate_count > 1: R
elif moderate_count == 1: PG13
elif mild_count > 0: PG
else: G
```

**Questions to Answer:**
1. Should 1 "damn" be G or PG?
2. Should 2 "damn" be PG or PG-13?
3. Is "ass" in "badass" profanity?
4. How many mild = 1 moderate?
5. Should context affect severity (e.g., "hell" in religious context)?

**Approach:**

**Step 1: Create Ground Truth Dataset**
- Manually rate 200 jokes (50 per rating level)
- Include edge cases and borderline examples
- Get 3+ human raters for reliability
- Calculate inter-rater agreement (Cohen's Kappa)

**Step 2: Test Threshold Variations**
```python
# Test different threshold combinations
THRESHOLD_SETS = [
    # Conservative (higher ratings)
    {"mild_pg": 1, "moderate_pg13": 1, "strong_r": 1},

    # Moderate (current)
    {"mild_pg": 1, "moderate_pg13": 1, "strong_r": 1, "moderate_r": 2},

    # Permissive (lower ratings)
    {"mild_pg": 3, "moderate_pg13": 2, "strong_r": 2},

    # Weighted scoring
    {"mild_weight": 1.0, "moderate_weight": 3.0, "strong_weight": 10.0,
     "pg_threshold": 1, "pg13_threshold": 3, "r_threshold": 10},
]
```

**Step 3: Optimize for Agreement**
- Test each threshold set on ground truth
- Calculate accuracy, Cohen's Kappa
- Find best balance of precision/recall

**Expected Outcomes:**
- Validated rating thresholds
- Ground truth dataset for future testing
- Understanding of systematic biases

**Metrics:**
- Accuracy (% correct ratings)
- Cohen's Kappa (inter-rater reliability)
- Confusion matrix (which ratings confused most)
- Precision/recall per rating level

**Script:** `experiments/scripts/calibrate_rating_thresholds.py`

**Deliverables:**
- Ground truth dataset (`data/ground_truth_ratings.json`)
- Optimal threshold configuration
- Calibration report with confusion matrix

---

### ⚡ Medium Priority (Sprint 5)

#### Experiment 7: Multi-Model Profanity Ensemble

**Goal:** Combine better-profanity + custom wordlists for best accuracy

**Hypothesis:** Ensemble approach gets better precision/recall than either alone

**Approach 1: Voting Ensemble**
```python
def detect_ensemble_voting(text: str) -> dict:
    """Use voting between models."""

    # Run both detectors
    better_result = better_profanity.contains_profanity(text)
    custom_result = detect_custom(text)

    # High confidence if both agree
    if better_result and custom_result["has_profanity"]:
        return {"has_profanity": True, "confidence": "high"}

    # Low confidence if only one flags it
    elif better_result or custom_result["has_profanity"]:
        return {"has_profanity": True, "confidence": "low"}

    # Clean if both agree it's clean
    else:
        return {"has_profanity": False, "confidence": "high"}
```

**Approach 2: Staged Detection**
```python
def detect_ensemble_staged(text: str) -> dict:
    """Use fast detector first, validate with slow detector."""

    # Stage 1: Fast custom wordlist
    custom_result = detect_custom(text)

    # Stage 2: Only validate strong/moderate with better-profanity
    if custom_result["severity"] in ["strong", "moderate"]:
        better_result = better_profanity.contains_profanity(text)

        if not better_result:
            # Downgrade if better-profanity disagrees
            custom_result["severity"] = "mild"

    return custom_result
```

**Approach 3: Specialized Roles**
```python
def detect_ensemble_specialized(text: str) -> dict:
    """Use each detector for what it's best at."""

    # better-profanity: Good at catching variations (f*ck, sh!t)
    # custom: Good at severity levels

    # Use better-profanity for detection
    has_profanity = better_profanity.contains_profanity(text)

    # Use custom for severity classification
    severity = "none"
    if has_profanity:
        custom_result = detect_custom(text)
        severity = custom_result["severity"]

    return {"has_profanity": has_profanity, "severity": severity}
```

**Expected Outcomes:**
- Better precision than better-profanity alone
- Better recall than custom alone
- Acceptable performance (< 1 min for 200k jokes)

**Metrics:**
- Precision, recall, F1 score
- Performance (jokes/sec)
- Agreement with ground truth

**Script:** `experiments/scripts/test_ensemble_profanity.py`

---

#### Experiment 10: Offensive Content Detection

**Goal:** Detect stereotypes, slurs, and offensive content beyond profanity

**Categories to Detect:**

**1. Racial/Ethnic Content**
```python
RACIAL_INDICATORS = {
    "stereotypes": ["blonde jokes", "irish jokes", "polish jokes"],
    "slurs": [...]  # Extensive list, not shown here
    "sensitive_terms": ["negro", "colored", "oriental"],
}
```

**2. Gender Stereotypes**
```python
GENDER_PATTERNS = {
    "stereotypes": [
        r"women (can't|bad at) (driving|parking|math)",
        r"men (only want|never listen)",
        r"like a girl",
    ],
}
```

**3. Religious Content**
```python
RELIGIOUS_INDICATORS = {
    "topics": ["god", "jesus", "allah", "buddha", "jewish", "muslim", "christian"],
    "mockery_patterns": [...]  # Context-dependent
}
```

**4. Disability/Medical**
```python
DISABILITY_SLURS = ["retard", "retarded", "spaz", "cripple", "midget"]
MEDICAL_SENSITIVE = ["cancer", "aids", "autism", "down syndrome"]
```

**5. LGBTQ+ Content**
```python
LGBTQ_INDICATORS = {
    "neutral_terms": ["gay", "lesbian", "transgender", "queer"],
    "slurs": ["faggot", "dyke", "tranny"],
    "check_context": True,  # "gay" can be neutral or offensive
}
```

**Approach:**
```python
def analyze_offensive_content(text: str) -> dict:
    """Detect potentially offensive content."""

    flags = {
        "racial": detect_racial_content(text),
        "gender_stereotype": detect_gender_stereotypes(text),
        "religious": detect_religious_content(text),
        "disability": detect_disability_content(text),
        "lgbtq": detect_lgbtq_content(text),
        "other_slurs": detect_other_slurs(text),
    }

    # Determine if offensive vs just mentioning topic
    severity = "none"
    for category, result in flags.items():
        if result["is_offensive"]:
            severity = max(severity, result["severity"])

    return {
        "flags": flags,
        "overall_severity": severity,
        "requires_review": any(f["is_offensive"] for f in flags.values()),
    }
```

**Challenges:**
- **Context matters:** "That's so gay" (offensive) vs "Gay pride" (neutral)
- **Satire vs reinforcement:** Is it mocking the stereotype or using it?
- **Cultural differences:** What's offensive varies by culture
- **Reclaimed terms:** Some communities reclaim slurs

**Expected Outcomes:**
- Flag obviously offensive content
- Mark ambiguous content for manual review
- Support `offensive` and `stereotypical` content flags

**Metrics:**
- Precision (% flagged that are truly offensive)
- Recall (% offensive content caught)
- False positive rate on neutral content

**Script:** `experiments/scripts/test_offensive_content_detection.py`

**Deliverables:**
- Offensive content detector
- Slur/stereotype wordlists
- Context analysis rules

---

### 🔬 Lower Priority (Future Sprints)

#### Experiment 8: Sexual Innuendo Detection with ML

**Goal:** Better detect double entendres and sexual innuendo

**Problem:** Only 0.8% innuendo detected - severe undercount

**Why It's Hard:**
- Innuendo is subtle and context-dependent
- "That's what she said" structure has infinite variations
- Requires understanding meaning, not just keywords

**Approach 1: Expanded Pattern Matching**
```python
INNUENDO_PATTERNS = {
    "common_phrases": [
        r"that'?s what (he|she|they) said",
        r"if you know what i mean",
        r"wink wink",
        r"in bed$",  # Fortune cookie jokes
    ],

    "double_meaning_contexts": [
        r"\b(hard|stiff|erect)\b.*\b(on|up)\b",
        r"\b(come|came)\b.*\b(inside|in|on)\b",
        r"\b(wet|moist|damp)\b",
        r"\b(big|long|thick|huge)\b.*\b(one|it)\b",
        r"\b(get|getting|got)\b.*\b(laid|lucky|some)\b",
    ],

    "body_parts_suggestive": [
        r"\b(balls|nuts)\b.*\b(tight|in a vice|caught)\b",
        r"\b(wood|morning wood)\b",
    ],
}
```

**Approach 2: Semantic Similarity (Requires sentence-transformers)**
```python
from sentence_transformers import SentenceTransformer

def detect_innuendo_semantic(text: str) -> float:
    """Use embeddings to detect sexual innuendo."""

    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Known innuendo examples
    innuendo_examples = [
        "That's what she said",
        "Size matters",
        "It's not going to suck itself",
        # ... 50+ examples
    ]

    # Embed joke and examples
    joke_embedding = model.encode(text)
    example_embeddings = model.encode(innuendo_examples)

    # Find similarity to known innuendos
    from sklearn.metrics.pairwise import cosine_similarity
    similarities = cosine_similarity([joke_embedding], example_embeddings)[0]

    max_similarity = similarities.max()
    return max_similarity  # 0.0-1.0 score
```

**Approach 3: Supervised Learning (Advanced)**
```python
# Train classifier on manually labeled jokes
# Features:
# - Presence of double-meaning words
# - Sentence structure patterns
# - Semantic embeddings
# - Word co-occurrence patterns

# Requires:
# - 1,000+ labeled jokes (innuendo vs not)
# - Feature engineering
# - Model training (Random Forest, XGBoost, or neural net)
```

**Expected Outcomes:**
- Catch 50%+ of innuendo (up from 0.8%)
- Reduce false positives vs simple keyword matching
- Flag ambiguous cases for review

**Challenges:**
- Requires large labeled dataset
- ML models need ongoing maintenance
- Semantic approaches require heavy dependencies

**Metrics:**
- Precision, recall, F1 on innuendo detection
- Coverage improvement over pattern matching
- Performance (innuendo detection is slowest analysis)

**Script:** `experiments/scripts/test_innuendo_detection.py`

**Dependencies:**
```bash
uv pip install sentence-transformers scikit-learn torch
```

---

#### Experiment 11: Rating Consistency Validation

**Goal:** Measure how consistent auto-ratings are vs human judgment

**Approach:**

**Step 1: Sample Selection**
```python
# Stratified sampling across auto-ratings
sample = {
    "G": 50,      # High confidence G-rated
    "PG": 50,     # Mild profanity
    "PG13": 50,   # Moderate profanity or innuendo
    "R": 50,      # Strong profanity or explicit
}
# Total: 200 jokes
```

**Step 2: Human Rating**
- Get 3-5 independent raters
- Provide rating guidelines
- Collect ratings + confidence scores
- Calculate inter-rater reliability (Fleiss' Kappa)

**Step 3: Analysis**
```python
def analyze_consistency(auto_ratings, human_ratings) -> dict:
    """Compare auto vs human ratings."""

    # Overall agreement
    exact_match = sum(auto == human for auto, human in zip(auto_ratings, human_ratings))
    accuracy = exact_match / len(auto_ratings)

    # Cohen's Kappa
    from sklearn.metrics import cohen_kappa_score
    kappa = cohen_kappa_score(auto_ratings, human_ratings)

    # Confusion matrix
    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(human_ratings, auto_ratings,
                          labels=["G", "PG", "PG13", "R", "X"])

    # Systematic biases
    over_rated = sum(RATING_ORDER[auto] > RATING_ORDER[human]
                     for auto, human in zip(auto_ratings, human_ratings))
    under_rated = sum(RATING_ORDER[auto] < RATING_ORDER[human]
                      for auto, human in zip(auto_ratings, human_ratings))

    return {
        "accuracy": accuracy,
        "cohens_kappa": kappa,
        "confusion_matrix": cm,
        "over_rating_rate": over_rated / len(auto_ratings),
        "under_rating_rate": under_rated / len(auto_ratings),
    }
```

**Expected Findings:**
- Identify which ratings are most confused (e.g., PG vs PG-13)
- Find systematic biases (over-rating or under-rating)
- Measure reliability (Kappa > 0.6 is good)

**Metrics:**
- Accuracy (exact match rate)
- Cohen's/Fleiss' Kappa (inter-rater reliability)
- Confusion matrix
- Bias analysis (over-rating vs under-rating)

**Script:** `experiments/scripts/validate_rating_consistency.py`

**Deliverables:**
- Consistency validation report
- Identified systematic biases
- Recommendations for threshold adjustments

---

## Implementation Recommendations

### Quick Wins (Implement Now)

**1. Fix False Positives**
- Add false positive pattern matching
- Low effort, high impact
- Can integrate immediately

**2. Add Severity Weighting**
```python
# Replace simple thresholds with weighted scoring
severity_score = (
    mild_count * 1.0 +
    moderate_count * 3.0 +
    strong_count * 10.0
)

if severity_score >= 10: rating = MaturityRating.R
elif severity_score >= 3: rating = MaturityRating.PG13
elif severity_score >= 1: rating = MaturityRating.PG
else: rating = MaturityRating.G
```

**3. Use Hybrid Detector**
```python
# Fast custom wordlist + better-profanity validation for strong profanity
def detect_profanity_hybrid(text: str) -> dict:
    custom = detect_custom(text)

    if custom["severity"] in ["strong", "moderate"]:
        # Validate with better-profanity
        if better_profanity.contains_profanity(text):
            return custom
        else:
            # Downgrade if disagreement
            custom["severity"] = "mild" if custom["severity"] == "moderate" else "none"

    return custom
```

### Medium-Term (Sprint 5)

**1. Build Ground Truth Dataset**
- Manually rate 200 jokes
- Use for all future validation
- Critical for threshold calibration

**2. Implement Offensive Content Detection**
- Important for content flags
- Clear ROI for content filtering

**3. Test Ensemble Approaches**
- Validate hybrid detector performance
- Compare voting vs staged approaches

### Long-Term (Future)

**1. ML-Based Innuendo Detection**
- Only if pattern matching insufficient
- Requires significant infrastructure

**2. Consistency Validation**
- After threshold calibration
- Periodic validation, not continuous

**3. Multi-Language Support**
- When expanding beyond English
- Requires language-specific wordlists

---

## Success Criteria

### Must Have
- ✅ Reduce false positive rate to <5%
- ✅ Achieve 80%+ accuracy on ground truth
- ✅ Process 200k jokes in <5 minutes
- ✅ Distinguish severity levels (mild/moderate/strong)

### Should Have
- Detect 50%+ of innuendo (up from 0.8%)
- Flag offensive content with 70%+ precision
- Cohen's Kappa > 0.6 vs human raters

### Nice to Have
- ML-based innuendo classifier
- Multi-rater consensus validation
- Confidence scores for ratings

---

## Resources Required

### Time Investment
- **Experiment 6 (Context-Aware):** 2-4 hours
- **Experiment 9 (Calibration):** 8-12 hours (includes manual rating)
- **Experiment 7 (Ensemble):** 4-6 hours
- **Experiment 10 (Offensive):** 6-10 hours
- **Experiment 8 (Innuendo ML):** 16-24 hours
- **Experiment 11 (Validation):** 12-16 hours (includes human rating)

### Dependencies
- **Core:** better-profanity (already installed)
- **Optional ML:** sentence-transformers, scikit-learn, torch (~500MB)
- **Human raters:** 3-5 people for ground truth creation

### Data Requirements
- Ground truth dataset: 200 manually rated jokes
- Offensive content wordlists: Build incrementally
- Innuendo examples: 50-100 labeled examples

---

## Related Documentation

- [MATURITY_RATING_EXPERIMENTS.md](MATURITY_RATING_EXPERIMENTS.md) - Initial experiment plan
- [MATURITY_RATING_GUIDE.md](../MATURITY_RATING_GUIDE.md) - Rating guidelines
- [Initial Results](../../experiments/output/maturity_rating_analysis.json) - Baseline data
- [Profanity Comparison](../../experiments/output/profanity_detection_comparison.json) - Library comparison

---

## Notes

- Prioritize experiments that fix known issues (false positives)
- Build ground truth early - it's needed for multiple experiments
- Don't over-engineer innuendo detection until pattern matching is exhausted
- Keep performance in mind - 200k jokes is a large dataset
- Consider manual review for edge cases rather than perfect automation
