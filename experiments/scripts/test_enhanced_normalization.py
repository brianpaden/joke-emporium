#!/usr/bin/env python3
"""Test enhanced normalization strategies based on semantic duplicate analysis.

This script validates whether enhanced normalization (article removal, stop words, etc.)
can catch the "semantic duplicates" found by embeddings using simple text normalization.

Based on findings from semantic_duplicate_analysis.json which showed 5.48% semantic
duplicate rate - most of which are actually text variations that better normalization
should catch.
"""

import hashlib
import json
import re
import unicodedata
from pathlib import Path


def normalize_for_dedup_baseline(text: str) -> str:
    """Baseline normalization (current approach)."""
    text = unicodedata.normalize("NFC", text)
    text = text.casefold()
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("…", "...")
    text = re.sub(r"\.{2,}", " ELLIPSIS ", text)
    text = re.sub(r"[^\w\s'ELLIPSIS]", "", text)
    text = text.replace("ELLIPSIS", "...")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_for_dedup_enhanced(text: str) -> str:
    """Enhanced normalization with article removal and stop words."""
    # Start with baseline normalization
    text = unicodedata.normalize("NFC", text)
    text = text.casefold()
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("…", "...")
    text = re.sub(r"\.{2,}", " ELLIPSIS ", text)
    text = re.sub(r"[^\w\s'ELLIPSIS]", "", text)
    text = text.replace("ELLIPSIS", "...")

    # ENHANCEMENT 1: Remove articles (a, an, the)
    # Use word boundaries to avoid matching within words
    text = re.sub(r"\b(a|an|the)\b", " ", text, flags=re.IGNORECASE)

    # ENHANCEMENT 2: Remove common filler/stop words
    # These don't change joke meaning but add noise
    stop_words = {
        "just",
        "really",
        "very",
        "actually",
        "basically",
        "literally",
        "totally",
        "completely",
        "absolutely",
        "exactly",
        "definitely",
    }
    words = text.split()
    words = [w for w in words if w not in stop_words]
    text = " ".join(words)

    # Normalize whitespace (cleanup after word removal)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def get_hash(text: str, enhanced: bool = False) -> str:
    """Get hash of normalized text."""
    if enhanced:
        normalized = normalize_for_dedup_enhanced(text)
    else:
        normalized = normalize_for_dedup_baseline(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def analyze_improvements():
    """Analyze how many semantic duplicates the enhanced normalization catches."""

    # Load semantic duplicate analysis results
    results_file = Path("experiments/output/semantic_duplicate_analysis.json")

    if not results_file.exists():
        print(f"Error: {results_file} not found")
        print("Please run measure_semantic_duplicates.py first")
        return

    with open(results_file, encoding="utf-8") as f:
        data = json.load(f)

    examples = data.get("examples", [])

    if not examples:
        print("No semantic duplicate examples found in results")
        return

    print("Testing Enhanced Normalization on Semantic Duplicates")
    print("=" * 80)
    print(f"Total semantic duplicate pairs to test: {len(examples)}")
    print()

    # Track results
    baseline_catches = 0
    enhanced_catches = 0
    still_missed = []
    newly_caught = []

    # Test each example
    for i, example in enumerate(examples, 1):
        joke1 = example["joke1"]
        joke2 = example["joke2"]
        similarity = example["similarity"]

        # Test baseline normalization
        baseline_hash1 = get_hash(joke1, enhanced=False)
        baseline_hash2 = get_hash(joke2, enhanced=False)
        baseline_match = baseline_hash1 == baseline_hash2

        # Test enhanced normalization
        enhanced_hash1 = get_hash(joke1, enhanced=True)
        enhanced_hash2 = get_hash(joke2, enhanced=True)
        enhanced_match = enhanced_hash1 == enhanced_hash2

        if baseline_match:
            baseline_catches += 1

        if enhanced_match:
            enhanced_catches += 1

            if not baseline_match:
                # Enhanced caught something baseline missed
                newly_caught.append({"pair": i, "joke1": joke1, "joke2": joke2, "similarity": similarity})
        else:
            # Still missed by enhanced
            still_missed.append({"pair": i, "joke1": joke1, "joke2": joke2, "similarity": similarity})

    # Calculate statistics
    total = len(examples)
    baseline_rate = (baseline_catches / total) * 100
    enhanced_rate = (enhanced_catches / total) * 100
    improvement = enhanced_rate - baseline_rate

    print(f"{'=' * 80}")
    print("RESULTS")
    print(f"{'=' * 80}")
    print()
    print(f"Total pairs tested: {total}")
    print()
    print(f"Baseline normalization caught: {baseline_catches}/{total} ({baseline_rate:.1f}%)")
    print(f"Enhanced normalization caught: {enhanced_catches}/{total} ({enhanced_rate:.1f}%)")
    print()
    print(f"Improvement: +{enhanced_catches - baseline_catches} pairs (+{improvement:.1f}%)")
    print()

    # Show examples of newly caught duplicates
    if newly_caught:
        print(f"{'=' * 80}")
        print(f"NEWLY CAUGHT BY ENHANCED NORMALIZATION ({len(newly_caught)} pairs)")
        print(f"{'=' * 80}")

        for item in newly_caught[:10]:  # Show first 10
            print(f"\nPair {item['pair']} - Similarity: {item['similarity']:.1%}")
            print("-" * 80)

            j1 = item["joke1"]
            j2 = item["joke2"]

            # Truncate if too long
            if len(j1) > 150:
                j1 = j1[:150] + "..."
            if len(j2) > 150:
                j2 = j2[:150] + "..."

            print(f"Joke A: {j1}")
            print(f"Joke B: {j2}")

            # Show what changed in normalization
            baseline1 = normalize_for_dedup_baseline(item["joke1"])
            _baseline2 = normalize_for_dedup_baseline(item["joke2"])
            enhanced1 = normalize_for_dedup_enhanced(item["joke1"])
            _enhanced2 = normalize_for_dedup_enhanced(item["joke2"])

            if len(baseline1) > 100:
                baseline1 = baseline1[:100] + "..."
            if len(enhanced1) > 100:
                enhanced1 = enhanced1[:100] + "..."

            print(f"\nBaseline normalized A: {baseline1}")
            print(f"Enhanced normalized A: {enhanced1}")

    # Show examples still missed
    if still_missed:
        print(f"\n{'=' * 80}")
        print(f"STILL MISSED BY ENHANCED NORMALIZATION ({len(still_missed)} pairs)")
        print(f"{'=' * 80}")
        print()
        print("These are likely true retellings that need Levenshtein matching:")

        for item in still_missed[:5]:  # Show first 5
            print(f"\nPair {item['pair']} - Similarity: {item['similarity']:.1%}")
            print("-" * 80)

            j1 = item["joke1"]
            j2 = item["joke2"]

            # Truncate if too long
            if len(j1) > 150:
                j1 = j1[:150] + "..."
            if len(j2) > 150:
                j2 = j2[:150] + "..."

            print(f"Joke A: {j1}")
            print(f"Joke B: {j2}")

    # Recommendations
    print(f"\n{'=' * 80}")
    print("RECOMMENDATIONS")
    print(f"{'=' * 80}")
    print()

    if improvement > 5:
        print(f"SIGNIFICANT: Enhanced normalization provides significant improvement (+{improvement:.1f}%)")
        print("   RECOMMEND: Implement enhanced normalization for Sprint 3")
        print()
        print("   Changes to implement:")
        print("   1. Add article removal (a, an, the)")
        print("   2. Add stop word removal (just, really, very, etc.)")
    elif improvement > 0:
        print(f"MARGINAL: Enhanced normalization provides marginal improvement (+{improvement:.1f}%)")
        print("   RECOMMEND: Consider for Phase 2")
    else:
        print("NO IMPROVEMENT: Enhanced normalization provides no improvement")
        print("   RECOMMEND: Skip enhanced normalization")

    print()

    if still_missed:
        missed_rate = (len(still_missed) / total) * 100
        print(f"Remaining {len(still_missed)} pairs ({missed_rate:.1f}%) need Levenshtein matching")
        print("RECOMMEND: Implement fuzzy fallback in Phase 2")

    # Save detailed results
    output_file = Path("experiments/output/enhanced_normalization_test.json")
    results = {
        "total_pairs": total,
        "baseline_caught": baseline_catches,
        "enhanced_caught": enhanced_catches,
        "improvement_percentage": improvement,
        "newly_caught_examples": newly_caught[:20],
        "still_missed_examples": still_missed[:20],
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'=' * 80}")
    print(f"Detailed results saved to {output_file}")
    print(f"{'=' * 80}")


def test_specific_cases():
    """Test specific normalization improvements on known cases."""

    print("\n" + "=" * 80)
    print("TESTING SPECIFIC ENHANCEMENT CASES")
    print("=" * 80)

    test_cases = [
        # Article differences
        ("Why can't Helen Keller drive?", "Why can't Helen Keller drive a car?", "Article addition"),
        # Number variations (still won't match without number normalization)
        (
            "What's the difference between a wife and a girlfriend? About 45 pounds.",
            "What's the difference between a wife and a girlfriend? About 35 pounds",
            "Number difference",
        ),
        # Stop word differences
        (
            "You go back up there and give that bus driver a piece of your mind",
            "You go back up there and give him a piece of your mind",
            "Pronoun substitution",
        ),
        # Filler words
        (
            "I'm not saying I'm Batman but have you ever seen us together",
            "I'm not saying I'm Batman... but have you really ever seen us together",
            "Filler word 'really'",
        ),
        # Multiple enhancements
        ("A man walks into a bar", "The man walks into the bar", "Articles"),
    ]

    for joke1, joke2, description in test_cases:
        print(f"\nTest: {description}")
        print("-" * 80)

        baseline_match = get_hash(joke1, enhanced=False) == get_hash(joke2, enhanced=False)
        enhanced_match = get_hash(joke1, enhanced=True) == get_hash(joke2, enhanced=True)

        print(f"Joke A: {joke1}")
        print(f"Joke B: {joke2}")
        print()
        print(f"Baseline match: {'YES' if baseline_match else 'NO'}")
        print(f"Enhanced match: {'YES' if enhanced_match else 'NO'}")

        if not baseline_match and enhanced_match:
            print("-> Enhancement HELPS!")
        elif baseline_match and enhanced_match:
            print("-> Already caught by baseline")
        else:
            print("-> Still needs Levenshtein")


def main():
    """Run enhanced normalization validation."""

    print("Enhanced Normalization Validation")
    print("=" * 80)
    print()
    print("This script tests whether enhanced normalization (article removal,")
    print("stop words) can catch semantic duplicates found by embeddings.")
    print()

    # Test specific cases first
    test_specific_cases()

    # Then analyze all semantic duplicates
    print("\n\n")
    analyze_improvements()


if __name__ == "__main__":
    main()
