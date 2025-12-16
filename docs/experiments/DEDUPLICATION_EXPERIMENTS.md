# Deduplication & Similarity Experiments

**Purpose:** Research and document approaches for detecting duplicate jokes in the Joke Emporium dataset.

**Status:** Planning / Experimental
**Last Updated:** 2025-12-16

---

## Overview

This document explores strategies for identifying duplicate jokes across imports. Since imports are one-time operations, we can afford more expensive computations in exchange for accuracy.

### Key Constraints

- **Primary Language:** English (v1)
- **Dataset Size:** Up to 200k jokes per import, most < 5k
- **Performance Budget:** Minutes to hours acceptable for import
- **Storage:** Disk space is cheap, can store hashes/vectors
- **Similarity Context:** Same language only (English vs English)
- **Joke Structure:** Setup + punchline = complete joke; changing either makes it different

### Key Questions

1. What normalization preserves joke meaning while enabling comparison?
2. Which similarity metrics detect duplicates without false positives?
3. Can we detect paraphrased jokes vs minor variations?
4. How do we handle punctuation that's critical to jokes vs formatting?
5. What's the right similarity threshold for different joke types?

---

## Experiment 1: Normalization Strategies

### Goal
Determine optimal text normalization that preserves joke semantics while enabling comparison.

### Approaches to Test

#### 1.1: Minimal Normalization (Baseline)
```python
def normalize_minimal(text: str) -> str:
    """Baseline: casefold + strip whitespace."""
    return text.strip().casefold()
```

**Pros:**
- Simple, fast
- Preserves most joke structure
- Works with unicode

**Cons:**
- Misses obvious duplicates with punctuation differences
- Sensitive to spacing variations

**Test Cases:**
```python
# Should match
"Why did the chicken cross the road?"
"why did the chicken cross the road?"
"  Why did the chicken cross the road?  "

# Should NOT match (different jokes)
"Why did the chicken cross the road?"
"Why did the turkey cross the road?"
```

#### 1.2: Aggressive Normalization
```python
import re
import unicodedata

def normalize_aggressive(text: str) -> str:
    """Aggressive: remove punctuation, normalize spaces, casefold."""
    # Unicode normalization (NFC)
    text = unicodedata.normalize('NFC', text)

    # Casefold
    text = text.casefold()

    # Remove punctuation (except apostrophes in contractions)
    text = re.sub(r"[^\w\s']", '', text)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    return text.strip()
```

**Pros:**
- Catches formatting variations
- Handles unicode variations

**Cons:**
- May lose critical joke elements (ellipsis for timing: "...")
- May merge different jokes with same words

**Test Cases:**
```python
# Should match
"I told my wife she was drawing her eyebrows too high. She looked surprised."
"I told my wife she was drawing her eyebrows too high... She looked surprised!"

# Edge case - should these match?
"Wait for it... the punchline!"
"Wait for it the punchline"  # Lost timing cue
```

#### 1.3: Contextual Normalization
```python
def normalize_contextual(text: str, preserve_timing: bool = True) -> str:
    """Context-aware: preserve joke-critical punctuation."""
    import unicodedata
    import re

    # Unicode normalization
    text = unicodedata.normalize('NFC', text)

    # Casefold
    text = text.casefold()

    if preserve_timing:
        # Preserve ellipsis, em-dash (timing markers)
        text = text.replace('...', ' ELLIPSIS ')
        text = text.replace('—', ' EMDASH ')

    # Remove other punctuation
    text = re.sub(r"[^\w\s']", '', text)

    # Restore timing markers
    if preserve_timing:
        text = text.replace('ELLIPSIS', '...')
        text = text.replace('EMDASH', '—')

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    return text.strip()
```

**Pros:**
- Preserves joke timing
- Handles most formatting variations

**Cons:**
- More complex
- Requires defining "critical" punctuation

#### 1.4: Token-Based Normalization
```python
def normalize_tokens(text: str) -> list[str]:
    """Return normalized token list for comparison."""
    import re

    # Basic normalization
    text = text.casefold()
    text = re.sub(r"[^\w\s']", ' ', text)

    # Tokenize
    tokens = text.split()

    # Optional: stem or lemmatize
    # tokens = [stem(t) for t in tokens]

    return tokens
```

**Use Case:** Bag-of-words comparison (order-independent)

**Pros:**
- Can detect reordered jokes
- Works with Jaccard similarity

**Cons:**
- Loses word order (critical for jokes)
- May need n-grams instead

### Experiment 1 Metrics

For each normalization strategy, measure:

1. **Collision Rate:** How many unique jokes map to same normalized form?
2. **Separation Rate:** How many actual duplicates are NOT detected?
3. **Processing Time:** Time per 1000 jokes
4. **Storage Size:** Bytes per normalized joke

### Test Dataset for Experiment 1

Create `tests/fixtures/normalization_test_cases.json`:

```json
[
  {
    "group": "exact_duplicates",
    "jokes": [
      "Why did the chicken cross the road?",
      "why did the chicken cross the road?",
      "Why did the chicken cross the road?"
    ],
    "expected_match": true
  },
  {
    "group": "formatting_variations",
    "jokes": [
      "I told my wife she was drawing her eyebrows too high. She looked surprised.",
      "I told my wife she was drawing her eyebrows too high... She looked surprised!",
      "I told my wife she was drawing her eyebrows too high - she looked surprised"
    ],
    "expected_match": true
  },
  {
    "group": "number_variations",
    "jokes": [
      "3 guys walk into a bar",
      "Three guys walk into a bar",
      "three guys walk into a bar"
    ],
    "expected_match": true
  },
  {
    "group": "contraction_variations",
    "jokes": [
      "You're going to love this",
      "You are going to love this",
      "Youre going to love this"
    ],
    "expected_match": "case_by_case"
  },
  {
    "group": "different_jokes",
    "jokes": [
      "Why did the chicken cross the road?",
      "Why did the turkey cross the road?",
      "Why did the chicken cross the street?"
    ],
    "expected_match": false
  },
  {
    "group": "timing_critical",
    "jokes": [
      "I'm not saying I'm Batman... but have you ever seen me and Batman in the same room?",
      "I'm not saying I'm Batman but have you ever seen me and Batman in the same room"
    ],
    "expected_match": "timing_dependent"
  }
]
```

---

## Experiment 2: Similarity Metrics

### Goal
Compare different similarity algorithms for duplicate detection.

### Approaches to Test

#### 2.1: Exact Match (Baseline)
```python
def exact_match(text1: str, text2: str, normalize_fn=normalize_minimal) -> bool:
    """Simple exact string match after normalization."""
    return normalize_fn(text1) == normalize_fn(text2)
```

**Complexity:** O(n) where n = string length
**Storage:** None (compute on-demand)

**Pros:**
- Fast
- No false positives
- Easy to understand

**Cons:**
- Misses near-duplicates
- Sensitive to normalization quality

#### 2.2: Levenshtein Distance
```python
from Levenshtein import distance

def levenshtein_similarity(text1: str, text2: str, threshold: float = 0.95) -> bool:
    """Check if Levenshtein similarity exceeds threshold.

    Similarity = 1 - (distance / max_length)
    """
    normalized1 = normalize_minimal(text1)
    normalized2 = normalize_minimal(text2)

    max_len = max(len(normalized1), len(normalized2))
    if max_len == 0:
        return True

    dist = distance(normalized1, normalized2)
    similarity = 1 - (dist / max_len)

    return similarity >= threshold
```

**Complexity:** O(m * n) where m, n = string lengths
**Storage:** None (compute on-demand)

**Pros:**
- Catches typos, minor variations
- Well-understood algorithm
- Adjustable threshold

**Cons:**
- Expensive for long strings
- Not ideal for word reordering
- O(n²) comparison across dataset

**Threshold Testing:**
- 95%: Very similar (1 char different per 20)
- 90%: Moderately similar (1 char different per 10)
- 85%: Loosely similar

#### 2.3: Jaccard Similarity (Token-Based)
```python
def jaccard_similarity(text1: str, text2: str, threshold: float = 0.9) -> bool:
    """Jaccard similarity on word tokens.

    Jaccard = |A ∩ B| / |A ∪ B|
    """
    tokens1 = set(normalize_tokens(text1))
    tokens2 = set(normalize_tokens(text2))

    if not tokens1 and not tokens2:
        return True
    if not tokens1 or not tokens2:
        return False

    intersection = tokens1 & tokens2
    union = tokens1 | tokens2

    similarity = len(intersection) / len(union)
    return similarity >= threshold
```

**Complexity:** O(m + n)
**Storage:** Minimal (token sets)

**Pros:**
- Fast
- Good for word-based duplicates
- Handles word reordering

**Cons:**
- Ignores word order (bad for jokes)
- Sensitive to joke length
- "The dog bit the man" = "The man bit the dog" (100% Jaccard, different jokes)

#### 2.4: Character N-Grams (Shingling)
```python
def ngram_similarity(text1: str, text2: str, n: int = 3, threshold: float = 0.9) -> bool:
    """Character n-gram (shingle) similarity.

    Good for catching substring matches and typos.
    """
    def get_ngrams(text: str, n: int) -> set:
        text = normalize_minimal(text)
        return {text[i:i+n] for i in range(len(text) - n + 1)}

    ngrams1 = get_ngrams(text1, n)
    ngrams2 = get_ngrams(text2, n)

    if not ngrams1 and not ngrams2:
        return True
    if not ngrams1 or not ngrams2:
        return False

    intersection = ngrams1 & ngrams2
    union = ngrams1 | ngrams2

    similarity = len(intersection) / len(union)
    return similarity >= threshold
```

**Complexity:** O(m + n)
**Storage:** O(m + n) for n-grams

**Pros:**
- Catches typos and variations
- Preserves some order information
- Language-agnostic

**Cons:**
- Requires tuning n (typically 3-5)
- May over-match similar but different jokes

#### 2.5: MinHash + LSH (Locality Sensitive Hashing)
```python
from datasketch import MinHash, MinHashLSH

class DuplicateDetector:
    """LSH-based duplicate detection for large datasets."""

    def __init__(self, threshold: float = 0.9, num_perm: int = 128):
        self.threshold = threshold
        self.num_perm = num_perm
        self.lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
        self.minhashes = {}

    def get_minhash(self, text: str) -> MinHash:
        """Create MinHash from text tokens."""
        mh = MinHash(num_perm=self.num_perm)
        tokens = normalize_tokens(text)
        for token in tokens:
            mh.update(token.encode('utf-8'))
        return mh

    def add(self, joke_id: str, text: str):
        """Add joke to index."""
        mh = self.get_minhash(text)
        self.lsh.insert(joke_id, mh)
        self.minhashes[joke_id] = mh

    def query(self, text: str) -> list[str]:
        """Find similar jokes."""
        mh = self.get_minhash(text)
        return self.lsh.query(mh)
```

**Complexity:** O(1) query after O(n) indexing
**Storage:** O(n * num_perm)

**Pros:**
- Fast queries (sublinear)
- Scalable to millions of jokes
- Tunable precision/recall

**Cons:**
- Requires preprocessing
- Memory overhead for index
- Probabilistic (may miss some duplicates)

#### 2.6: Sentence Embeddings (Semantic Similarity)
```python
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class SemanticDuplicateDetector:
    """Semantic similarity using sentence embeddings."""

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', threshold: float = 0.95):
        """Initialize with local sentence transformer model.

        Model: all-MiniLM-L6-v2
        - Size: ~80MB
        - Speed: ~1000 sentences/sec on CPU
        - Embedding dimension: 384
        """
        self.model = SentenceTransformer(model_name)
        self.threshold = threshold
        self.embeddings = {}

    def get_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text."""
        return self.model.encode(text, convert_to_numpy=True)

    def add(self, joke_id: str, text: str):
        """Add joke embedding."""
        self.embeddings[joke_id] = self.get_embedding(text)

    def query(self, text: str, top_k: int = 5) -> list[tuple[str, float]]:
        """Find semantically similar jokes."""
        query_emb = self.get_embedding(text)

        results = []
        for joke_id, emb in self.embeddings.items():
            similarity = cosine_similarity([query_emb], [emb])[0][0]
            if similarity >= self.threshold:
                results.append((joke_id, similarity))

        return sorted(results, key=lambda x: x[1], reverse=True)[:top_k]
```

**Complexity:** O(n) query, O(n) encoding
**Storage:** O(n * 384) for embeddings

**Pros:**
- Understands semantics (paraphrases)
- Works across different phrasings
- Local model (no API costs)

**Cons:**
- Slower than hash-based methods
- Requires ~80MB model download
- May be overkill for exact duplicates

**When to Use:**
- Detecting paraphrased jokes
- Quality-based similarity
- When Levenshtein fails

### Experiment 2 Metrics

For each similarity metric, measure on test dataset:

1. **Precision:** True positives / (True positives + False positives)
2. **Recall:** True positives / (True positives + False negatives)
3. **F1 Score:** Harmonic mean of precision and recall
4. **Processing Time:** Time to compare 1000 joke pairs
5. **Scaling Performance:** Time for 10k, 50k, 100k, 200k jokes

### Test Dataset for Experiment 2

Create `tests/fixtures/similarity_test_cases.json`:

```json
[
  {
    "joke1": "Why did the chicken cross the road? To get to the other side!",
    "joke2": "Why did the chicken cross the road? To get to the other side.",
    "category": "exact_duplicate",
    "expected_similar": true
  },
  {
    "joke1": "I told my wife she was drawing her eyebrows too high. She looked surprised.",
    "joke2": "I told my wife her eyebrows were drawn too high. She looked surprised.",
    "category": "paraphrase",
    "expected_similar": true
  },
  {
    "joke1": "Why don't scientists trust atoms? Because they make up everything!",
    "joke2": "Why dont scientists trust atoms Because they make up everything",
    "category": "formatting",
    "expected_similar": true
  },
  {
    "joke1": "Parallel lines have so much in common. It's a shame they'll never meet.",
    "joke2": "Perpendicular lines have nothing in common. Good thing they always meet.",
    "category": "opposite_joke",
    "expected_similar": false
  },
  {
    "joke1": "I'm reading a book about anti-gravity. It's impossible to put down!",
    "joke2": "I'm reading a book about teleportation. It's impossible to put down!",
    "category": "template_variation",
    "expected_similar": false,
    "notes": "Same template, different subject - not duplicates"
  }
]
```

---

## Experiment 3: Multi-Metric Hybrid Approach

### Goal
Combine multiple metrics for optimal duplicate detection.

### Strategy: Tiered Detection

```python
class HybridDuplicateDetector:
    """Multi-tiered duplicate detection."""

    def __init__(self):
        # Tier 1: Fast exact match (hash-based)
        self.exact_hashes = {}

        # Tier 2: Character n-grams (good for typos)
        self.ngram_index = {}

        # Tier 3: Semantic embeddings (for paraphrases)
        self.semantic_detector = None  # Lazy load

    def check_duplicate(self, text: str) -> tuple[bool, str | None, str]:
        """Check for duplicates using tiered approach.

        Returns:
            (is_duplicate, duplicate_id, detection_tier)
        """
        # Tier 1: Exact match (fastest)
        normalized = normalize_minimal(text)
        hash_key = hash(normalized)

        if hash_key in self.exact_hashes:
            return (True, self.exact_hashes[hash_key], "exact")

        # Tier 2: N-gram similarity (fast, catches typos)
        ngrams = get_ngrams(text, n=3)
        for existing_id, existing_ngrams in self.ngram_index.items():
            similarity = jaccard_similarity_sets(ngrams, existing_ngrams)
            if similarity >= 0.95:
                return (True, existing_id, "ngram")

        # Tier 3: Semantic similarity (expensive, only for edge cases)
        # Only use if explicitly requested or for high-value imports
        if self.semantic_detector and len(self.ngram_index) < 1000:
            results = self.semantic_detector.query(text, top_k=1)
            if results and results[0][1] >= 0.95:
                return (True, results[0][0], "semantic")

        return (False, None, "none")
```

**Performance Profile:**
- Tier 1: 99% of duplicates, O(1)
- Tier 2: 0.9% of duplicates, O(n)
- Tier 3: 0.1% of duplicates, O(n) but expensive

---

## Experiment 4: Structural Comparison

### Goal
Compare joke structure (setup/punchline) separately to handle multi-part jokes.

### Approach: Element-wise Comparison

```python
from joke_emporium.models.joke import Joke
from joke_emporium.models.enums import ElementType

def structural_similarity(joke1: Joke, joke2: Joke, threshold: float = 0.9) -> bool:
    """Compare jokes element-by-element.

    For Q&A jokes: Compare setup and punchline separately.
    Weight punchline more heavily (it's the critical part).
    """
    # Must be same structure
    if joke1.structure != joke2.structure:
        return False

    # Must have same number of elements
    if len(joke1.content) != len(joke2.content):
        return False

    # Compare each element
    similarities = []
    weights = []

    for elem1, elem2 in zip(joke1.content, joke2.content):
        # Must be same element type
        if elem1.type != elem2.type:
            return False

        # Calculate similarity for this element
        sim = levenshtein_similarity(elem1.text, elem2.text, threshold=0.9)
        similarities.append(sim)

        # Weight punchline more heavily
        weight = 2.0 if elem1.type == ElementType.PUNCHLINE else 1.0
        weights.append(weight)

    # Weighted average similarity
    if not similarities:
        return False

    weighted_sim = sum(s * w for s, w in zip(similarities, weights)) / sum(weights)
    return weighted_sim >= threshold
```

**Use Cases:**
- Q&A jokes with different setups but same punchline (probably different jokes)
- Same setup with different punchlines (definitely different jokes)

---

## Experiment 5: Performance Optimization

### Goal
Optimize duplicate detection for large imports (200k jokes).

### Strategies to Test

#### 5.1: Bloom Filters (Pre-screening)
```python
from pybloom_live import BloomFilter

class BloomPrefilter:
    """Fast pre-screening before expensive similarity checks."""

    def __init__(self, capacity: int = 200000, error_rate: float = 0.01):
        self.bloom = BloomFilter(capacity=capacity, error_rate=error_rate)
        self.candidates = {}

    def add(self, joke_id: str, text: str):
        """Add joke to filter."""
        normalized = normalize_minimal(text)

        if normalized in self.bloom:
            # Potential duplicate - add to candidates for full check
            if normalized not in self.candidates:
                self.candidates[normalized] = []
            self.candidates[normalized].append(joke_id)
        else:
            # Definitely unique
            self.bloom.add(normalized)

    def get_candidates(self, text: str) -> list[str]:
        """Get candidate duplicates for full check."""
        normalized = normalize_minimal(text)
        return self.candidates.get(normalized, [])
```

**Benefits:**
- O(1) lookup
- Space-efficient (bits, not strings)
- Fast filtering (99%+ of comparisons)

#### 5.2: Batch Processing
```python
def batch_deduplicate(jokes: list[Joke], batch_size: int = 1000) -> dict:
    """Process jokes in batches for memory efficiency."""
    results = {
        "unique": [],
        "duplicates": [],
        "stats": {}
    }

    detector = HybridDuplicateDetector()

    for i in range(0, len(jokes), batch_size):
        batch = jokes[i:i+batch_size]

        for joke in batch:
            is_dup, dup_id, tier = detector.check_duplicate(joke.text_preview)

            if is_dup:
                results["duplicates"].append({
                    "joke_id": joke.id,
                    "duplicate_of": dup_id,
                    "detection_method": tier
                })
            else:
                detector.add(joke.id, joke.text_preview)
                results["unique"].append(joke.id)

    return results
```

#### 5.3: Parallel Processing
```python
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

def parallel_deduplicate(jokes: list[Joke], workers: int = None) -> dict:
    """Use multiple processes for CPU-bound duplicate detection."""
    if workers is None:
        workers = multiprocessing.cpu_count()

    # Split jokes into chunks
    chunk_size = len(jokes) // workers
    chunks = [jokes[i:i+chunk_size] for i in range(0, len(jokes), chunk_size)]

    with ProcessPoolExecutor(max_workers=workers) as executor:
        results = executor.map(batch_deduplicate, chunks)

    # Merge results
    # ... implementation ...
```

**Expected Performance:**
- Single-threaded: ~1000 jokes/second (Levenshtein)
- Parallel (4 cores): ~4000 jokes/second
- With LSH: ~10,000+ jokes/second

---

## Experiment 6: Storage & Caching

### Goal
Determine optimal storage strategy for duplicate detection.

### Options

#### 6.1: Store Normalized Text
```python
# staging_jokes table
normalized_text: str = Field(index=True)  # For exact matching
text_hash: str = Field(index=True)        # SHA-256 hash
```

**Pros:** Fast exact lookups
**Cons:** Doesn't help with fuzzy matching

#### 6.2: Store N-Gram Signatures
```python
# joke_ngrams table
joke_id: str
ngram_hash: str  # Hash of character 3-grams
signature: str   # MinHash signature (128 bytes)
```

**Pros:** Fast fuzzy matching
**Cons:** Additional storage, complexity

#### 6.3: Store Embeddings
```python
# joke_embeddings table
joke_id: str
embedding: bytes  # Serialized numpy array (384 * 4 bytes = 1.5KB)
```

**Pros:** Semantic search
**Cons:** Large storage (1.5KB per joke = 300MB for 200k jokes)

### Storage Cost Analysis

For 200,000 jokes:
- Normalized text: ~20MB (avg 100 chars/joke)
- Text hashes: ~6.4MB (32 bytes/joke)
- N-gram signatures: ~25MB (128 bytes/joke)
- Embeddings: ~300MB (1.5KB/joke)

**Recommendation:** Start with text hashes + n-gram signatures (~30MB total)

---

## Experiment 7: Real Data Testing

### Goal
Test approaches on actual taivop dataset to measure real-world performance.

### Test Plan

1. **Sample Dataset:**
   - Extract 10k jokes from taivop
   - Manually identify ~100 duplicate pairs
   - Create test set with known duplicates

2. **Inject Known Duplicates:**
   ```python
   # Add variations of known jokes
   variations = [
       ("original", "Why did the chicken cross the road?"),
       ("punctuation", "Why did the chicken cross the road"),
       ("typo", "Why did the chiken cross the road?"),
       ("paraphrase", "Why did the chicken go across the road?"),
   ]
   ```

3. **Measure Performance:**
   - Precision/Recall for each method
   - False positive rate
   - Processing time
   - Memory usage

4. **Edge Cases:**
   - Very short jokes (< 20 chars)
   - Very long jokes (> 500 chars)
   - Jokes with lots of punctuation
   - Jokes with emoji
   - Jokes with numbers

### Success Metrics

- **Precision:** > 95% (few false positives)
- **Recall:** > 90% (catch most duplicates)
- **Processing Time:** < 1 hour for 200k jokes
- **Memory Usage:** < 2GB RAM

---

## Implementation Roadmap

### Phase 1: MVP (Sprint 3)
- Exact match with minimal normalization
- Hash-based lookup for performance
- Simple threshold-based Levenshtein for edge cases

### Phase 2: Enhanced (Post-Sprint 3)
- Character n-gram indexing
- MinHash + LSH for scalability
- Configurable similarity thresholds

### Phase 3: Advanced (Future)
- Sentence embeddings for semantic matching
- Structural comparison (element-wise)
- Cross-language duplicate detection

---

## Recommended Starting Point

For Sprint 3, implement this hybrid approach:

```python
def detect_duplicates_v1(joke: Joke, existing_jokes: list[Joke]) -> tuple[bool, str | None]:
    """Simple but effective duplicate detection.

    1. Exact match on normalized text (hash lookup)
    2. Levenshtein similarity >= 95% as fallback
    """
    normalized = normalize_minimal(joke.text_preview)
    text_hash = hashlib.sha256(normalized.encode()).hexdigest()

    # Check hash index
    if text_hash in hash_index:
        return (True, hash_index[text_hash])

    # Fallback: Check Levenshtein for near-matches
    for existing in existing_jokes[-1000:]:  # Only check recent imports
        if levenshtein_similarity(joke.text_preview, existing.text_preview, threshold=0.95):
            return (True, existing.id)

    # Not a duplicate
    hash_index[text_hash] = joke.id
    return (False, None)
```

**Why This Works:**
- Catches 99%+ of duplicates with exact match
- Handles typos with Levenshtein
- Fast enough for import use case
- Simple to implement and debug

**Future Improvements:**
- Add n-gram indexing (Phase 2)
- Add semantic matching (Phase 3)
- Optimize with LSH (Phase 2)

---

## Open Questions for Further Research

1. **Multi-language support:** How to detect duplicates across languages?
2. **Joke templates:** Should "Why did the X..." jokes be flagged as similar?
3. **Punchline weighting:** Should punchline similarity matter more than setup?
4. **Emoji normalization:** How to handle emoji variations (😂 vs 🤣 vs haha)?
5. **Performance vs Accuracy:** What's the optimal trade-off for 200k jokes?

---

## References & Resources

- [Levenshtein Distance](https://en.wikipedia.org/wiki/Levenshtein_distance)
- [MinHash & LSH](http://infolab.stanford.edu/~ullman/mmds/ch3n.pdf)
- [Sentence Transformers](https://www.sbert.net/)
- [Text Normalization Best Practices](https://unicode.org/reports/tr15/)
- [Datasketch Library](https://github.com/ekzhu/datasketch)

---

## Next Steps

1. Create test fixtures with known duplicates
2. Implement normalization experiments
3. Benchmark similarity metrics on real data
4. Document findings and recommendations
5. Update Sprint 3 implementation based on results
