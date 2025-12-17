#!/usr/bin/env python3
"""Test normalization strategies on real data from taivop dataset.

This script validates the normalization recommendations from NORMALIZATION_STRATEGIES.md
against actual duplicate groups and variations found in 208k real jokes.
"""

import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path


def normalize_for_dedup(text: str) -> str:
    """Normalize text for duplicate detection.

    Based on analysis of 208,345 real jokes.
    Achieves 68.5% recall on variations, 100% on exact duplicates.

    Strategy:
    - Unicode normalization (NFC) - handles 3.8% of dataset
    - Casefold - handles 10% SHOUTING
    - Line break normalization - handles 15% multiline
    - Ellipsis normalization (not strict preservation) - 23% of jokes
    - Punctuation removal (except apostrophes)
    - Whitespace normalization

    Note: For deduplication, we normalize ellipsis rather than strictly
    preserving it. This allows "..." and "....." to match.
    """
    # Unicode normalization (handles 3.8%)
    text = unicodedata.normalize('NFC', text)

    # Casefold (handles 10% SHOUTING)
    text = text.casefold()

    # Normalize line breaks (handles 15% multiline)
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Normalize ellipsis to a marker (not strict preservation)
    # This allows multiple dots to match
    text = text.replace('…', '...')  # Unicode ellipsis to ASCII
    text = re.sub(r'\.{2,}', ' ELLIPSIS ', text)  # Multiple dots → marker

    # Remove punctuation (preserve apostrophes and our marker)
    text = re.sub(r"[^\w\s'ELLIPSIS]", '', text)

    # Restore ellipsis as standard marker
    text = text.replace('ELLIPSIS', '...')

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def get_hash(text: str) -> str:
    """Get SHA-256 hash of normalized text."""
    normalized = normalize_for_dedup(text)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def test_on_natural_duplicates():
    """Test normalization on real duplicate groups."""

    print("Testing Normalization on Natural Duplicates")
    print("=" * 70)

    # Load natural duplicates
    dup_file = Path("experiments/output/natural_duplicates.json")
    if not dup_file.exists():
        print(f"Error: {dup_file} not found")
        print("Run find_natural_duplicates.py first")
        return None

    with open(dup_file, encoding="utf-8") as f:
        data = json.load(f)

    duplicates = data.get("examples", [])
    print(f"Loaded {len(duplicates)} duplicate groups")

    # Test: All instances in a group should have same normalized hash
    total_groups = 0
    perfect_matches = 0
    partial_matches = 0

    for group in duplicates[:100]:  # Top 100 groups
        instances = group.get("instances", [])

        if len(instances) < 2:
            continue

        total_groups += 1

        # Get hashes for all instances
        hashes = [get_hash(inst.get("text", "")) for inst in instances]
        unique_hashes = set(hashes)

        if len(unique_hashes) == 1:
            # All instances normalize to same hash
            perfect_matches += 1
        else:
            partial_matches += 1
            # Show example of mismatch
            if total_groups <= 5:
                print(f"\nPartial match in group {total_groups}:")
                print(f"  {len(unique_hashes)} unique hashes from {len(instances)} instances")
                for i, inst in enumerate(instances[:3]):
                    text = inst.get("text", "")[:80]
                    print(f"  [{i}] {text}...")
                    print(f"      Hash: {hashes[i][:16]}...")

    recall = perfect_matches / total_groups if total_groups > 0 else 0

    print(f"\n{'-' * 70}")
    print(f"Results:")
    print(f"  Total groups tested: {total_groups}")
    print(f"  Perfect matches: {perfect_matches} ({recall:.1%})")
    print(f"  Partial matches: {partial_matches}")

    return {
        "total_groups": total_groups,
        "perfect_matches": perfect_matches,
        "partial_matches": partial_matches,
        "recall": recall
    }


def test_on_variations():
    """Test normalization on controlled variations."""

    print("\n" + "=" * 70)
    print("Testing Normalization on Variations")
    print("=" * 70)

    # Load variation test set
    var_file = Path("tests/fixtures/variation_test_set.json")
    if not var_file.exists():
        print(f"Warning: {var_file} not found")
        print("Run create_variations.py first")
        return None

    with open(var_file, encoding="utf-8") as f:
        test_set = json.load(f)

    print(f"Loaded {len(test_set)} test cases")

    # Test: Variations should normalize to same hash as original
    variation_results = {}

    for test_case in test_set[:50]:  # First 50 test cases
        original = test_case["original_text"]
        original_hash = get_hash(original)

        for variation in test_case["variations"]:
            var_type = variation["type"]
            var_text = variation["text"]
            expected = variation.get("expected_match", "unknown")

            # Only test variations where we expect exact match
            if expected not in [True, "fuzzy", "maybe"]:
                continue

            var_hash = get_hash(var_text)
            matched = (var_hash == original_hash)

            if var_type not in variation_results:
                variation_results[var_type] = {"matches": 0, "total": 0}

            variation_results[var_type]["total"] += 1
            if matched:
                variation_results[var_type]["matches"] += 1

    # Calculate recall per variation type
    for var_type, stats in variation_results.items():
        stats["recall"] = stats["matches"] / stats["total"] if stats["total"] > 0 else 0

    # Print results
    print(f"\nResults by variation type:")
    print(f"{'-' * 70}")

    for var_type in sorted(variation_results.keys()):
        stats = variation_results[var_type]
        recall = stats["recall"]
        print(f"  {var_type:25} {stats['matches']:3}/{stats['total']:3} ({recall:6.1%})")

    # Overall stats
    total_matches = sum(s["matches"] for s in variation_results.values())
    total_tests = sum(s["total"] for s in variation_results.values())
    overall_recall = total_matches / total_tests if total_tests > 0 else 0

    print(f"{'-' * 70}")
    print(f"  {'Overall':25} {total_matches:3}/{total_tests:3} ({overall_recall:6.1%})")

    return {
        "variation_results": variation_results,
        "total_matches": total_matches,
        "total_tests": total_tests,
        "overall_recall": overall_recall
    }


def test_edge_cases():
    """Test normalization on edge cases."""

    print("\n" + "=" * 70)
    print("Testing Normalization on Edge Cases")
    print("=" * 70)

    edge_cases = [
        # Unicode variations
        ("café", "cafe", "Unicode accent", False),  # Different meaning
        ("café", "café", "Unicode NFC/NFD", True),  # Same character, different encoding

        # Case variations
        ("Why did the CHICKEN cross the road?", "why did the chicken cross the road?", "Case", True),
        ("WHY DID THE CHICKEN CROSS THE ROAD?", "Why did the chicken cross the road?", "SHOUTING", True),

        # Whitespace variations
        ("Why  did  the  chicken", "Why did the chicken", "Extra spaces", True),
        ("Why\tdid\tthe\tchicken", "Why did the chicken", "Tabs", True),
        ("Why\ndid\nthe\nchicken", "Why did the chicken", "Newlines", True),

        # Punctuation variations
        ("I'm not saying I'm Batman... but have you ever seen us together?",
         "I'm not saying I'm Batman but have you ever seen us together",
         "Punctuation removed (but ellipsis differs)", False),  # Ellipsis is preserved, so these differ
        ("Why did the chicken cross the road?",
         "Why did the chicken cross the road",
         "Question mark", True),

        # Ellipsis normalization (normalized, not removed)
        ("Wait for it...", "Wait for it", "Ellipsis vs no ellipsis", False),  # Different jokes
        ("Wait for it...", "Wait for it…", "Ellipsis unicode", True),  # Same joke
        ("Wait for it...", "Wait for it.....", "Multiple dots", True),  # Same joke, normalized

        # Apostrophes/contractions
        ("You're going to love this", "You're going to love this", "Contraction", True),
        ("You're going to love this", "Youre going to love this", "Apostrophe style", False),  # Different

        # Numbers (not normalized in MVP)
        ("Three guys walk into a bar", "3 guys walk into a bar", "Number words", False),
        ("3 guys walk into a bar", "three guys walk into a bar", "Digit to word", False),
    ]

    results = {
        "passed": 0,
        "failed": 0,
        "failures": []
    }

    for text1, text2, description, should_match in edge_cases:
        hash1 = get_hash(text1)
        hash2 = get_hash(text2)
        matched = (hash1 == hash2)

        if matched == should_match:
            results["passed"] += 1
            status = "PASS"
        else:
            results["failed"] += 1
            status = "FAIL"
            results["failures"].append({
                "description": description,
                "text1": text1,
                "text2": text2,
                "expected": should_match,
                "actual": matched
            })

        print(f"  [{status}] {description:25} - Expected: {should_match}, Got: {matched}")

    print(f"{'-' * 70}")
    print(f"  Passed: {results['passed']}/{len(edge_cases)}")
    print(f"  Failed: {results['failed']}/{len(edge_cases)}")

    if results["failures"]:
        print(f"\n{'-' * 70}")
        print("Failures:")
        for failure in results["failures"]:
            print(f"\n  {failure['description']}:")
            print(f"    Text 1: {failure['text1'][:60]}...")
            print(f"    Text 2: {failure['text2'][:60]}...")
            print(f"    Expected match: {failure['expected']}, Got: {failure['actual']}")

    return results


def test_performance():
    """Test normalization performance on sample data."""

    print("\n" + "=" * 70)
    print("Testing Normalization Performance")
    print("=" * 70)

    # Load sample data
    data_dir = Path("temp/imports/taivop_joke-dataset")
    reddit_file = data_dir / "reddit_jokes.json"

    if not reddit_file.exists():
        print(f"Warning: {reddit_file} not found")
        print("Sample data not available for performance test")
        return None

    with open(reddit_file, encoding="utf-8") as f:
        jokes = json.load(f)

    # Test on first 10k jokes
    sample_size = min(10000, len(jokes))
    sample = jokes[:sample_size]

    import time

    print(f"Normalizing {sample_size:,} jokes...")

    start = time.time()

    for joke in sample:
        text = f"{joke.get('title', '')} {joke.get('body', '')}".strip()
        _ = get_hash(text)

    elapsed = time.time() - start
    rate = sample_size / elapsed

    print(f"\n{'-' * 70}")
    print(f"Results:")
    print(f"  Sample size: {sample_size:,} jokes")
    print(f"  Time: {elapsed:.2f} seconds")
    print(f"  Rate: {rate:,.0f} jokes/sec")
    print(f"  Per joke: {(elapsed / sample_size) * 1000:.2f} ms")

    return {
        "sample_size": sample_size,
        "elapsed": elapsed,
        "rate": rate
    }


def main():
    """Run all normalization tests."""

    print("Normalization Strategy Validation")
    print("=" * 70)
    print("Testing the data-driven normalization approach from")
    print("NORMALIZATION_STRATEGIES.md against real joke data")
    print("=" * 70)

    results = {}

    # Test 1: Natural duplicates
    results["natural_duplicates"] = test_on_natural_duplicates()

    # Test 2: Controlled variations
    results["variations"] = test_on_variations()

    # Test 3: Edge cases
    results["edge_cases"] = test_edge_cases()

    # Test 4: Performance
    results["performance"] = test_performance()

    # Save results
    output_dir = Path("experiments/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "normalization_test_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'=' * 70}")
    print("Testing complete!")
    print(f"Results saved to {output_file}")

    # Summary
    print(f"\n{'=' * 70}")
    print("Summary:")

    if results["natural_duplicates"]:
        recall = results["natural_duplicates"]["recall"]
        print(f"  Natural duplicates recall: {recall:.1%}")

    if results["variations"]:
        recall = results["variations"]["overall_recall"]
        print(f"  Variation recall: {recall:.1%}")

    if results["edge_cases"]:
        passed = results["edge_cases"]["passed"]
        total = passed + results["edge_cases"]["failed"]
        print(f"  Edge case tests passed: {passed}/{total}")

    if results["performance"]:
        rate = results["performance"]["rate"]
        print(f"  Performance: {rate:,.0f} jokes/sec")

    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
