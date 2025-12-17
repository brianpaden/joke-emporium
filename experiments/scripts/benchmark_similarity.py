#!/usr/bin/env python3
"""Benchmark different similarity metrics on real joke data.

Tests various similarity approaches (exact match, Levenshtein, n-grams, etc.)
on real duplicates and variations to measure precision, recall, and performance.
"""

import hashlib
import json
import re
import time
import unicodedata
from pathlib import Path


def normalize_minimal(text: str) -> str:
    """Baseline normalization: casefold + strip."""
    return text.strip().casefold()


def normalize_aggressive(text: str) -> str:
    """Aggressive normalization: remove punctuation, normalize spaces."""
    # Unicode normalization (NFC)
    text = unicodedata.normalize("NFC", text)

    # Casefold
    text = text.casefold()

    # Remove punctuation (except apostrophes in contractions)
    text = re.sub(r"[^\w\s']", "", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def exact_match(text1: str, text2: str, normalize_fn=normalize_minimal) -> bool:
    """Simple exact string match after normalization."""
    return normalize_fn(text1) == normalize_fn(text2)


def hash_match(text1: str, text2: str, normalize_fn=normalize_minimal) -> bool:
    """Hash-based exact match (faster for large datasets)."""
    hash1 = hashlib.sha256(normalize_fn(text1).encode()).hexdigest()
    hash2 = hashlib.sha256(normalize_fn(text2).encode()).hexdigest()
    return hash1 == hash2


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings.

    Simple implementation without external dependencies.
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Cost of insertions, deletions, or substitutions
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def levenshtein_similarity(text1: str, text2: str, threshold: float = 0.95) -> bool:
    """Check if Levenshtein similarity exceeds threshold."""
    normalized1 = normalize_minimal(text1)
    normalized2 = normalize_minimal(text2)

    max_len = max(len(normalized1), len(normalized2))
    if max_len == 0:
        return True

    dist = levenshtein_distance(normalized1, normalized2)
    similarity = 1 - (dist / max_len)

    return similarity >= threshold


def benchmark_on_duplicates():
    """Benchmark similarity metrics on known duplicates."""

    print("Benchmarking Similarity Metrics on Real Duplicates")
    print("=" * 70)

    # Load natural duplicates
    dup_file = Path("experiments/output/natural_duplicates.json")
    if not dup_file.exists():
        print("Error: natural_duplicates.json not found")
        print("Run find_natural_duplicates.py first")
        return

    with open(dup_file, encoding="utf-8") as f:
        data = json.load(f)

    duplicates = data.get("examples", [])
    print(f"Loaded {len(duplicates)} duplicate groups")

    # Test metrics
    metrics = {
        "exact_minimal": lambda t1, t2: exact_match(t1, t2, normalize_minimal),
        "exact_aggressive": lambda t1, t2: exact_match(t1, t2, normalize_aggressive),
        "hash_minimal": lambda t1, t2: hash_match(t1, t2, normalize_minimal),
        "hash_aggressive": lambda t1, t2: hash_match(t1, t2, normalize_aggressive),
        "levenshtein_95": lambda t1, t2: levenshtein_similarity(t1, t2, 0.95),
        "levenshtein_90": lambda t1, t2: levenshtein_similarity(t1, t2, 0.90),
    }

    results = {}

    for metric_name, metric_fn in metrics.items():
        print(f"\nTesting {metric_name}...")

        matches = 0
        comparisons = 0
        start_time = time.time()

        # Test on duplicate groups
        for group in duplicates[:100]:  # Top 100 groups
            instances = group.get("instances", [])

            if len(instances) < 2:
                continue

            # Compare first instance with all others in group
            first_text = instances[0].get("text", "")

            for instance in instances[1:]:
                text = instance.get("text", "")
                comparisons += 1

                if metric_fn(first_text, text):
                    matches += 1

        elapsed = time.time() - start_time

        # All instances in a duplicate group should match
        recall = matches / comparisons if comparisons > 0 else 0

        results[metric_name] = {
            "matches": matches,
            "comparisons": comparisons,
            "recall": recall,
            "time_seconds": elapsed,
            "comparisons_per_second": comparisons / elapsed if elapsed > 0 else 0,
        }

        print(f"  Matches: {matches}/{comparisons}")
        print(f"  Recall: {recall:.2%}")
        print(f"  Time: {elapsed:.3f}s ({comparisons / elapsed:.0f} comp/sec)")

    # Save results
    output_dir = Path("experiments/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "benchmark_duplicates.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            {"test": "duplicate_detection", "duplicate_groups_tested": min(100, len(duplicates)), "results": results},
            f,
            indent=2,
        )

    print(f"\n{'-' * 70}")
    print(f"Results saved to {output_file}")


def benchmark_on_variations():
    """Benchmark similarity metrics on controlled variations."""

    print("\n" + "=" * 70)
    print("Benchmarking Similarity Metrics on Variations")
    print("=" * 70)

    # Load variation test set
    var_file = Path("tests/fixtures/variation_test_set.json")
    if not var_file.exists():
        print("Warning: variation_test_set.json not found")
        print("Run create_variations.py first")
        print("Skipping variation benchmark...")
        return

    with open(var_file, encoding="utf-8") as f:
        test_set = json.load(f)

    print(f"Loaded {len(test_set)} test cases")

    # Test metrics
    metrics = {
        "exact_minimal": lambda t1, t2: exact_match(t1, t2, normalize_minimal),
        "exact_aggressive": lambda t1, t2: exact_match(t1, t2, normalize_aggressive),
        "levenshtein_95": lambda t1, t2: levenshtein_similarity(t1, t2, 0.95),
        "levenshtein_90": lambda t1, t2: levenshtein_similarity(t1, t2, 0.90),
        "levenshtein_85": lambda t1, t2: levenshtein_similarity(t1, t2, 0.85),
    }

    results = {}

    for metric_name, metric_fn in metrics.items():
        print(f"\nTesting {metric_name}...")

        # Track by variation type
        variation_results = {}

        for test_case in test_set[:50]:  # First 50 test cases
            original = test_case["original_text"]

            for variation in test_case["variations"]:
                var_type = variation["type"]
                var_text = variation["text"]
                expected = variation.get("expected_match", "unknown")

                # Only test variations where we expect a match
                if expected not in [True, "fuzzy", "maybe"]:
                    continue

                matched = metric_fn(original, var_text)

                if var_type not in variation_results:
                    variation_results[var_type] = {"matches": 0, "total": 0}

                variation_results[var_type]["total"] += 1
                if matched:
                    variation_results[var_type]["matches"] += 1

        # Calculate recall per variation type
        for _var_type, stats in variation_results.items():
            stats["recall"] = stats["matches"] / stats["total"] if stats["total"] > 0 else 0

        results[metric_name] = variation_results

        # Print summary
        total_matches = sum(s["matches"] for s in variation_results.values())
        total_tests = sum(s["total"] for s in variation_results.values())
        overall_recall = total_matches / total_tests if total_tests > 0 else 0

        print(f"  Overall: {total_matches}/{total_tests} ({overall_recall:.1%})")

    # Save results
    output_file = Path("experiments/output/benchmark_variations.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({"test": "variation_detection", "test_cases": len(test_set[:50]), "results": results}, f, indent=2)

    print(f"\n{'-' * 70}")
    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    benchmark_on_duplicates()
    benchmark_on_variations()

    print(f"\n{'=' * 70}")
    print("Benchmarking complete!")
