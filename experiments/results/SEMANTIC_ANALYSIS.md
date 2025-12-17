# Semantic Duplicate Analysis - Experiment Design

**Purpose:** Determine whether semantic embeddings (Word2Vec, BERT, Sentence-BERT) would add value for joke deduplication beyond hash-based and Levenshtein approaches.

**Status:** 🆕 Experiment ready to run
**Created:** 2025-12-16

---

## Research Question

**Do jokes have "semantic-only" duplicates?**

That is: jokes that are similar in meaning but different enough in text that hash-based normalization and Levenshtein distance don't catch them.

Examples of semantic duplicates:
```
Original: "Why did the chicken cross the road? To get to the other side."
Paraphrase: "What made the chicken go across the street? To reach the opposite side."

Original: "A man walks into a bar. Ouch!"
Retelling: "Some guy entered a bar. It hurt!"
```

---

## Why This Matters

### If semantic duplicates are **rare** (<0.5%):
- ❌ **Don't use embeddings**
- Hash + Levenshtein is sufficient
- Embeddings add cost without benefit

### If semantic duplicates are **moderate** (0.5-1%):
- ⚠️ **Maybe use embeddings in Phase 3**
- Could add marginal value
- Cost/benefit needs careful analysis

### If semantic duplicates are **common** (>1%):
- ✅ **Use embeddings in Phase 2/3**
- Significant duplicate reduction potential
- Worth the storage and computation cost

---

## Methodology

### 1. Sample Selection
- Random sample of 2,000 jokes from taivop dataset (default)
  - 2,000 jokes = ~2M comparisons (~1-2 minutes)
  - Can increase to 5k or 10k for more confidence
- Stratified across all three sources
- Filter out very short jokes (<20 chars)

### 2. Hash-Based Baseline
- Compute normalized hash for each joke
- Identify hash-based duplicate groups
- These are our "already caught" duplicates

### 3. Semantic Embedding
- Use Sentence-BERT (all-MiniLM-L6-v2)
  - 384 dimensions
  - Pre-trained on semantic similarity tasks
  - Fast and lightweight
- Encode all jokes to vectors
- Compute cosine similarity for all pairs

### 4. Identify Semantic-Only Duplicates
- Find pairs with high semantic similarity (≥85%)
- Exclude pairs already caught by hash
- These are the "semantic-only" duplicates

### 5. Calculate Rate
```
Semantic-only rate = (semantic-only pairs / total jokes) × 100%
```

---

## Expected Results

### Hypothesis 1: Low rate (<0.5%)
**Reasoning:** Our natural duplicate analysis showed 99.5% of duplicates are same-source reposts, which are near-exact text matches.

**If true:**
- Embeddings don't add significant value
- Hash + Levenshtein is optimal
- Focus on Phase 2 (fuzzy fallback) not embeddings

### Hypothesis 2: Moderate rate (0.5-1%)
**Reasoning:** Some cross-source jokes might be retellings.

**If true:**
- Embeddings have marginal value
- Consider for Phase 3 (after MVP and Phase 2)
- Could be useful for recommendation features

### Hypothesis 3: High rate (>1%)
**Reasoning:** Jokes are frequently retold with different wording.

**If true:**
- Embeddings add significant value
- Should prioritize in Phase 2
- Semantic deduplication becomes important

---

## Cost Analysis

### Storage Costs

**Sentence-BERT embeddings:**
- 384 dimensions × 4 bytes = **1.5 KB per joke**
- 200k jokes = **300 MB**

**Current approach (hashes):**
- 32 bytes per joke
- 200k jokes = **6.4 MB**

**Overhead:** 47x larger

### Computation Costs

**One-time encoding (200k jokes):**
- CPU: ~11 minutes
- GPU: ~2 minutes

**Per-import (1000 jokes):**
- CPU: ~3 seconds
- GPU: ~0.5 seconds

### Comparison Costs

**With indexing (FAISS/Annoy):**
- Query: 1-10ms per joke
- vs Hash: <1μs per joke

**Overhead:** 1,000-10,000x slower

---

## Decision Framework

| Semantic Rate | Storage | Compute | Decision |
|--------------|---------|---------|----------|
| <0.1% | ❌ Not worth 300MB | ❌ Not worth setup | ❌ Skip |
| 0.1-0.5% | ⚠️ Expensive | ⚠️ Moderate | ⚠️ Consider Phase 3+ |
| 0.5-1% | ⚠️ Expensive | ⚠️ Moderate | ✅ Consider Phase 3 |
| >1% | ✅ Justified | ✅ Worth it | ✅ Plan for Phase 2/3 |

---

## Alternative Use Cases

Even if semantic duplicates are rare, embeddings could be valuable for:

### 1. Similarity Search (User Feature)
```python
# "Find jokes like this one"
user_query = "Why did the chicken cross the road?"
similar_jokes = index.find_similar(user_query, top_k=10)
```

### 2. Content Recommendation
```python
# "If you liked this joke, you'll like..."
user_likes = ["joke1_id", "joke2_id"]
recommendations = index.recommend_based_on(user_likes)
```

### 3. Topic Clustering
```python
# Group jokes by theme/topic
clusters = cluster_jokes_by_topic(all_jokes, n_clusters=50)
```

### 4. Quality Filtering
```python
# Remove low-quality retellings
is_quality_retelling = similarity < 0.95 and similarity > 0.70
```

**These features don't require real-time embedding** - can be pre-computed and cached.

---

## Running the Experiment

### Prerequisites
```bash
# Install dependencies (first time only)
uv pip install sentence-transformers scikit-learn

# This downloads ~500MB of model files
```

### Run Experiment
```bash
# Basic run (2k sample, takes 1-2 minutes)
uv run python experiments/scripts/measure_semantic_duplicates.py

# For more confidence, edit script to increase sample_size:
# - 2,000 jokes: ~2M comparisons (~1-2 min)
# - 5,000 jokes: ~12.5M comparisons (~5-10 min)
# - 10,000 jokes: ~50M comparisons (~20-30 min)
```

### Outputs
- Console: Real-time progress and results
- JSON: `experiments/output/semantic_duplicate_analysis.json`
  - Semantic-only duplicate rate
  - Top 20 example pairs
  - Performance metrics

---

## Interpreting Results

### Example Output 1: Low Rate
```
Semantic-only duplicate rate: 0.12%
Unique jokes in semantic dups: 5 / 2,000

RECOMMENDATION: ❌ Embeddings NOT recommended
  Rate too low (0.12%)
  Cost/benefit ratio unfavorable
  Stick with hash + Levenshtein approach
```

**Action:** Document findings, skip embeddings for MVP and Phase 2.

### Example Output 2: Moderate Rate
```
Semantic-only duplicate rate: 0.68%
Unique jokes in semantic dups: 27 / 2,000

RECOMMENDATION: ⚠️ Embeddings marginally useful
  Rate is moderate (0.68%)
  Consider for Phase 3 after other optimizations
```

**Action:** Add to Phase 3 roadmap, focus on hash + Levenshtein first.

### Example Output 3: High Rate
```
Semantic-only duplicate rate: 1.85%
Unique jokes in semantic dups: 74 / 2,000

RECOMMENDATION: ✅ Embeddings strongly recommended
  Rate is high (1.85%)
  Should prioritize for Phase 2
  Significant duplicate reduction potential
```

**Action:** Update Phase 2 plan to include semantic deduplication.

---

## Integration Architecture (If Needed)

If semantic duplicates are common enough to justify embeddings:

```python
class JokeDeduplicator:
    """Multi-tier deduplication with optional semantic layer."""

    def __init__(self, use_embeddings: bool = False):
        self.hash_index = {}  # Tier 1: Fast exact match
        self.levenshtein_cache = {}  # Tier 2: Fuzzy match
        self.embedding_index = None  # Tier 3: Semantic match (optional)

        if use_embeddings:
            from sentence_transformers import SentenceTransformer
            import faiss

            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.embedding_index = faiss.IndexFlatIP(384)  # Cosine similarity

    def check_duplicate(self, joke_text: str) -> tuple[bool, str | None]:
        """Check for duplicates across all tiers."""

        # Tier 1: Hash (fastest, 100% precision)
        text_hash = get_hash(joke_text)
        if text_hash in self.hash_index:
            return (True, self.hash_index[text_hash])

        # Tier 2: Levenshtein (fast, 71% recall on variations)
        # ... levenshtein logic ...

        # Tier 3: Embeddings (slower, catches semantic paraphrases)
        if self.embedding_index and self.embedding_index.ntotal > 0:
            embedding = self.model.encode([joke_text])[0]
            D, I = self.embedding_index.search(embedding.reshape(1, -1), k=1)

            if D[0][0] >= 0.85:  # Cosine similarity threshold
                return (True, self.joke_ids[I[0][0]])

        return (False, None)
```

---

## Next Steps

1. ✅ **Created experiment script** - `measure_semantic_duplicates.py`
2. ⏳ **Run experiment** - Execute on 10k sample
3. ⏳ **Analyze results** - Review semantic-only duplicate rate
4. ⏳ **Make decision** - Use decision framework above
5. ⏳ **Update roadmap** - Adjust Phase 2/3 plans based on findings

---

## References

- [Sentence-BERT Paper](https://arxiv.org/abs/1908.10084) - Sentence embeddings using siamese BERT
- [all-MiniLM-L6-v2 Model](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) - Lightweight Sentence-BERT
- [FAISS Library](https://github.com/facebookresearch/faiss) - Fast similarity search
- [Newscatcher Guide](https://www.newscatcherapi.com/blog-posts/ultimate-guide-to-text-similarity-with-python) - Text similarity methods

---

**Experiment Owner:** TBD
**Expected Completion:** Sprint 3 or later (optional)
**Dependencies:** sentence-transformers, scikit-learn
