#!/usr/bin/env python3
"""Measure semantic duplicate rate in joke dataset.

This experiment determines whether semantic embeddings (Word2Vec, BERT, etc.)
would add value for joke deduplication by measuring how many "semantic-only"
duplicates exist - jokes that are similar in meaning but different in text.

If the rate is low (<0.5%), embeddings aren't worth the cost.
If the rate is high (>1%), they should be considered for Phase 3.
"""

import hashlib
import json
import random
import re
import sys
import time
import unicodedata
from pathlib import Path

# Check for sentence-transformers
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    from tqdm import tqdm

    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("Warning: sentence-transformers or tqdm not installed")
    print("Install with: uv pip install sentence-transformers scikit-learn tqdm")
    print()


def normalize_for_dedup(text: str) -> str:
    """Normalize text for duplicate detection (from validated approach)."""
    text = unicodedata.normalize("NFC", text)
    text = text.casefold()
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("…", "...")
    text = re.sub(r"\.{2,}", " ELLIPSIS ", text)
    text = re.sub(r"[^\w\s'ELLIPSIS]", "", text)
    text = text.replace("ELLIPSIS", "...")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_hash(text: str) -> str:
    """Get hash of normalized text."""
    normalized = normalize_for_dedup(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_joke_text(joke: dict, source: str) -> str:
    """Extract text from joke based on source format."""
    if source == "reddit_jokes":
        title = joke.get("title", "")
        body = joke.get("body", "")
        return f"{title} {body}".strip()
    elif source in ["wocka", "stupidstuff"]:
        return joke.get("body", "").strip()
    else:
        return str(joke.get("body", "") or joke.get("title", "")).strip()


def load_sample_jokes(sample_size: int = 10000) -> list[str]:
    """Load a sample of jokes from taivop dataset."""

    data_dir = Path("temp/imports/taivop_joke-dataset")
    if not data_dir.exists():
        print(f"Error: {data_dir} not found")
        print("Please run the taivop import first to download the data.")
        sys.exit(1)

    all_jokes = []

    for json_file in sorted(data_dir.glob("*.json")):
        source_name = json_file.stem
        print(f"Loading {json_file.name}...")

        try:
            with open(json_file, encoding="utf-8") as f:
                jokes = json.load(f)

            if not isinstance(jokes, list):
                continue

            for joke in jokes:
                if not isinstance(joke, dict):
                    continue

                text = get_joke_text(joke, source_name)

                # Filter out very short or empty jokes
                if len(text) >= 20:
                    all_jokes.append({"text": text, "source": source_name, "id": joke.get("id")})

        except Exception as e:
            print(f"  Error: {e}")
            continue

    # Sample randomly
    if len(all_jokes) > sample_size:
        random.seed(42)  # Reproducible
        all_jokes = random.sample(all_jokes, sample_size)

    print(f"\nSampled {len(all_jokes)} jokes")
    return all_jokes


def measure_semantic_duplicates(sample_size: int = 2000, similarity_threshold: float = 0.85):
    """Measure rate of semantic-only duplicates."""

    if not EMBEDDINGS_AVAILABLE:
        print("\nCannot run experiment without sentence-transformers.")
        print("Install with: uv pip install sentence-transformers scikit-learn")
        return None

    print("Measuring Semantic Duplicate Rate")
    print("=" * 70)
    print(f"Sample size: {sample_size:,} jokes")
    print(f"Similarity threshold: {similarity_threshold:.0%}")
    print("=" * 70)

    # Load sample
    print("\n[1/4] Loading sample jokes...")
    jokes = load_sample_jokes(sample_size)
    joke_texts = [j["text"] for j in jokes]

    # Build hash index
    print("\n[2/4] Building hash index...")
    hash_index = {}
    for i, joke in enumerate(jokes):
        text_hash = get_hash(joke["text"])
        if text_hash not in hash_index:
            hash_index[text_hash] = []
        hash_index[text_hash].append(i)

    hash_duplicates = sum(1 for indices in hash_index.values() if len(indices) > 1)
    print(f"  Hash-based duplicates: {hash_duplicates} groups")

    # Compute embeddings
    print("\n[3/4] Computing embeddings...")
    print("  Loading Sentence-BERT model (all-MiniLM-L6-v2)...")

    model = SentenceTransformer("all-MiniLM-L6-v2")

    print(f"  Encoding {len(joke_texts):,} jokes...")
    start = time.time()
    embeddings = model.encode(
        joke_texts,
        show_progress_bar=True,
        batch_size=32,
        normalize_embeddings=True,  # Pre-normalize for faster cosine similarity
    )
    elapsed = time.time() - start

    print(f"  Encoding complete: {elapsed:.1f}s ({len(joke_texts) / elapsed:.0f} jokes/sec)")

    # Find semantic duplicates
    print("\n[4/4] Finding semantic-only duplicates...")

    # Pre-compute all hashes for fast lookup
    print("  Pre-computing hashes...")
    joke_hashes = [get_hash(joke["text"]) for joke in jokes]

    semantic_only_duplicates = []

    # Calculate total pairs for progress bar
    total_pairs = (len(embeddings) * (len(embeddings) - 1)) // 2

    print(f"  Comparing {total_pairs:,} pairs (this may take a few minutes)...")

    start = time.time()

    # Use tqdm for progress tracking
    with tqdm(total=total_pairs, desc="  Comparing pairs", unit="pairs") as pbar:
        for i in range(len(embeddings)):
            # Compute similarities for this joke against all remaining jokes
            for j in range(i + 1, len(embeddings)):
                # Skip if hash already matches (not semantic-only)
                if joke_hashes[i] == joke_hashes[j]:
                    pbar.update(1)
                    continue

                # Compute cosine similarity
                similarity = np.dot(embeddings[i], embeddings[j]) / (
                    np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                )

                # Check if semantically similar
                if similarity >= similarity_threshold:
                    semantic_only_duplicates.append(
                        {
                            "joke1_idx": i,
                            "joke2_idx": j,
                            "joke1": jokes[i]["text"],
                            "joke2": jokes[j]["text"],
                            "similarity": float(similarity),
                            "source1": jokes[i]["source"],
                            "source2": jokes[j]["source"],
                        }
                    )

                pbar.update(1)

    elapsed = time.time() - start
    pairs_checked = total_pairs

    print(f"\n{'-' * 70}")
    print(f"Comparison complete: {elapsed:.1f}s ({pairs_checked / elapsed:.0f} pairs/sec)")

    # Calculate statistics
    total_jokes = len(jokes)
    semantic_only_count = len(semantic_only_duplicates)
    semantic_only_rate = (semantic_only_count / total_jokes) * 100

    # Count unique jokes involved in semantic duplicates
    unique_jokes_in_semantic_dups = len(
        set([d["joke1_idx"] for d in semantic_only_duplicates] + [d["joke2_idx"] for d in semantic_only_duplicates])
    )

    # Results
    print(f"\n{'=' * 70}")
    print("RESULTS")
    print(f"{'=' * 70}")
    print(f"\nSample size: {total_jokes:,} jokes")
    print(f"Similarity threshold: {similarity_threshold:.0%}")
    print("\nDuplicate Detection:")
    print(f"  Hash-based duplicate groups: {hash_duplicates}")
    print(f"  Semantic-only duplicate pairs: {semantic_only_count}")
    print(f"  Unique jokes in semantic dups: {unique_jokes_in_semantic_dups}")
    print(f"\nSemantic-only duplicate rate: {semantic_only_rate:.2f}%")
    print(f"  (per joke: {(unique_jokes_in_semantic_dups / total_jokes) * 100:.2f}%)")

    # Recommendation
    print(f"\n{'=' * 70}")
    print("RECOMMENDATION")
    print(f"{'=' * 70}")

    if semantic_only_rate < 0.1:
        print("\n❌ Embeddings NOT recommended")
        print(f"   Rate too low ({semantic_only_rate:.2f}%)")
        print("   Cost/benefit ratio unfavorable")
        print("   Stick with hash + Levenshtein approach")
    elif semantic_only_rate < 0.5:
        print("\n⚠️  Embeddings marginally useful")
        print(f"   Rate is low ({semantic_only_rate:.2f}%)")
        print("   Consider for Phase 3 after other optimizations")
    elif semantic_only_rate < 1.0:
        print("\n✅ Embeddings worth considering")
        print(f"   Rate is moderate ({semantic_only_rate:.2f}%)")
        print("   Could add value in Phase 3")
        print("   Recommend further analysis")
    else:
        print("\n✅ Embeddings strongly recommended")
        print(f"   Rate is high ({semantic_only_rate:.2f}%)")
        print("   Should prioritize for Phase 2 or 3")
        print("   Significant duplicate reduction potential")

    # Show examples
    print(f"\n{'=' * 70}")
    print("EXAMPLES")
    print(f"{'=' * 70}")

    if semantic_only_duplicates:
        print("\nShowing first 10 semantic-only duplicate pairs:")

        for i, dup in enumerate(semantic_only_duplicates[:10], 1):
            print(f"\n{'-' * 70}")
            print(f"Pair {i} - Similarity: {dup['similarity']:.1%}")
            print(f"Sources: {dup['source1']} / {dup['source2']}")

            text1 = dup["joke1"]
            text2 = dup["joke2"]

            # Truncate if too long
            if len(text1) > 200:
                text1 = text1[:200] + "..."
            if len(text2) > 200:
                text2 = text2[:200] + "..."

            print(f"\nJoke A: {text1}")
            print(f"Joke B: {text2}")
    else:
        print("\n✅ No semantic-only duplicates found!")
        print("   Hash-based approach catches all duplicates")

    # Save results
    output_dir = Path("experiments/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "semantic_duplicate_analysis.json"

    results = {
        "experiment": "semantic_duplicate_measurement",
        "sample_size": total_jokes,
        "similarity_threshold": similarity_threshold,
        "hash_duplicate_groups": hash_duplicates,
        "semantic_only_pairs": semantic_only_count,
        "semantic_only_rate": semantic_only_rate,
        "unique_jokes_in_semantic_dups": unique_jokes_in_semantic_dups,
        "embedding_model": "all-MiniLM-L6-v2",
        "embedding_dimensions": 384,
        "encoding_speed_jokes_per_sec": len(joke_texts) / elapsed,
        "comparison_time_seconds": elapsed,
        "examples": semantic_only_duplicates[:20],  # Save top 20 examples
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'-' * 70}")
    print(f"Results saved to {output_file}")
    print(f"{'=' * 70}")

    return results


def main():
    """Run semantic duplicate measurement experiment."""

    print("Semantic Duplicate Measurement Experiment")
    print("=" * 70)
    print()

    if not EMBEDDINGS_AVAILABLE:
        print("ERROR: Required packages not installed")
        print()
        print("Install with:")
        print("  uv pip install sentence-transformers scikit-learn tqdm")
        print()
        print("These packages are needed for semantic similarity analysis.")
        print("They will download ~500MB of model files on first run.")
        sys.exit(1)

    # Run experiment
    # Start with 2k sample (takes ~1-2 minutes)
    # 2000 jokes = ~2M comparisons
    # Can increase to 5k (12.5M comparisons) or 10k (50M comparisons) if needed
    results = measure_semantic_duplicates(sample_size=5000, similarity_threshold=0.85)

    if results:
        print("\n" + "=" * 70)
        print("Experiment complete!")
        print("=" * 70)


if __name__ == "__main__":
    main()
