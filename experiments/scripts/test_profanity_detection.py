#!/usr/bin/env python3
"""Test and compare profanity detection libraries.

This script evaluates different profanity detection libraries:
1. better-profanity - Fast, wordlist-based
2. profanity-check - ML-based (if installed)
3. Custom wordlist approach

NOTE: This script requires optional dependencies:
    uv pip install better-profanity
    uv pip install profanity-check (optional, requires alt-profanity-check fork)

Run without dependencies to test custom wordlist approach only.
"""

import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

# Track available libraries
LIBRARIES_AVAILABLE = {
    "better_profanity": False,
    "profanity_check": False,
}

# Try importing better-profanity
try:
    from better_profanity import profanity as better_profanity
    LIBRARIES_AVAILABLE["better_profanity"] = True
    print("✓ better-profanity available")
except ImportError:
    print("✗ better-profanity not available (install with: uv pip install better-profanity)")

# Try importing profanity-check
try:
    from profanity_check import predict as profanity_check_predict
    LIBRARIES_AVAILABLE["profanity_check"] = True
    print("✓ profanity-check available")
except ImportError:
    print("✗ profanity-check not available (optional)")

print()


def load_jokes_sample(max_jokes: int = 500) -> list[dict[str, Any]]:
    """Load a sample of jokes from taivop dataset."""
    data_dir = Path("temp/imports/taivop_joke-dataset")

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        print("Please run the taivop import first to download the data.")
        sys.exit(1)

    all_jokes = []

    # Load from reddit (most diverse)
    reddit_file = data_dir / "reddit_jokes.json"
    if reddit_file.exists():
        with open(reddit_file, encoding="utf-8") as f:
            jokes = json.load(f)
            all_jokes = jokes[:max_jokes]

    return all_jokes


def get_joke_text(joke: dict) -> str:
    """Extract full text from joke."""
    title = joke.get("title", "")
    body = joke.get("body", "")
    return f"{title} {body}".strip()


# Custom wordlist approach
CUSTOM_WORDLISTS = {
    "mild": ["damn", "hell", "crap", "ass", "piss", "bastard", "pissed"],
    "moderate": ["shit", "bitch", "dick", "cock", "pussy", "asshole", "bullshit", "dipshit"],
    "strong": [
        "fuck", "fucking", "fucked", "fucker", "motherfucker",
        "cunt", "fucks", "fuckin", "fuckers",
    ],
    "extreme": [
        # Extremely explicit sexual/violent terms
        # Not listing here to keep this file clean
    ],
}


def detect_profanity_custom(text: str) -> dict:
    """Custom wordlist-based profanity detection."""
    text_lower = text.lower()

    # Check each severity level
    severity = "none"
    matched_words = []

    for level in ["mild", "moderate", "strong", "extreme"]:
        for word in CUSTOM_WORDLISTS[level]:
            if word in text_lower:
                severity = level
                matched_words.append(word)

    return {
        "has_profanity": severity != "none",
        "severity": severity,
        "matched_words": list(set(matched_words)),
    }


def test_better_profanity(jokes: list[dict]) -> dict:
    """Test better-profanity library."""
    if not LIBRARIES_AVAILABLE["better_profanity"]:
        return {"available": False}

    print("Testing better-profanity...")

    # Initialize
    better_profanity.load_censor_words()

    results = {
        "available": True,
        "total_jokes": len(jokes),
        "profane_count": 0,
        "clean_count": 0,
        "examples": [],
        "performance": {},
    }

    start_time = time.time()

    for joke in jokes:
        text = get_joke_text(joke)

        # Check for profanity
        is_profane = better_profanity.contains_profanity(text)

        if is_profane:
            results["profane_count"] += 1

            # Get censored version to see what was flagged
            censored = better_profanity.censor(text)

            if len(results["examples"]) < 10:
                results["examples"].append({
                    "original": text[:150],
                    "censored": censored[:150],
                })
        else:
            results["clean_count"] += 1

    elapsed = time.time() - start_time

    results["performance"] = {
        "total_time_seconds": elapsed,
        "jokes_per_second": len(jokes) / elapsed,
    }

    results["profane_percentage"] = (results["profane_count"] / len(jokes)) * 100

    return results


def test_profanity_check(jokes: list[dict]) -> dict:
    """Test profanity-check library (ML-based)."""
    if not LIBRARIES_AVAILABLE["profanity_check"]:
        return {"available": False}

    print("Testing profanity-check (ML-based)...")

    results = {
        "available": True,
        "total_jokes": len(jokes),
        "profane_count": 0,
        "clean_count": 0,
        "examples": [],
        "performance": {},
    }

    start_time = time.time()

    # Extract texts
    texts = [get_joke_text(joke) for joke in jokes]

    # Batch prediction
    predictions = profanity_check_predict(texts)

    for i, (joke, is_profane) in enumerate(zip(jokes, predictions)):
        text = get_joke_text(joke)

        if is_profane:
            results["profane_count"] += 1

            if len(results["examples"]) < 10:
                results["examples"].append({
                    "text": text[:150],
                })
        else:
            results["clean_count"] += 1

    elapsed = time.time() - start_time

    results["performance"] = {
        "total_time_seconds": elapsed,
        "jokes_per_second": len(jokes) / elapsed,
    }

    results["profane_percentage"] = (results["profane_count"] / len(jokes)) * 100

    return results


def test_custom_wordlist(jokes: list[dict]) -> dict:
    """Test custom wordlist approach."""
    print("Testing custom wordlist approach...")

    results = {
        "available": True,
        "total_jokes": len(jokes),
        "severity_counts": defaultdict(int),
        "examples_by_severity": defaultdict(list),
        "performance": {},
    }

    start_time = time.time()

    for joke in jokes:
        text = get_joke_text(joke)

        # Detect profanity
        detection = detect_profanity_custom(text)
        severity = detection["severity"]

        results["severity_counts"][severity] += 1

        # Store examples
        if len(results["examples_by_severity"][severity]) < 5:
            results["examples_by_severity"][severity].append({
                "text": text[:150],
                "matched_words": detection["matched_words"],
            })

    elapsed = time.time() - start_time

    results["performance"] = {
        "total_time_seconds": elapsed,
        "jokes_per_second": len(jokes) / elapsed,
    }

    # Calculate percentages
    results["severity_percentages"] = {
        severity: (count / len(jokes)) * 100
        for severity, count in results["severity_counts"].items()
    }

    # Convert defaultdict to dict for JSON serialization
    results["severity_counts"] = dict(results["severity_counts"])
    results["examples_by_severity"] = dict(results["examples_by_severity"])

    return results


def compare_libraries(jokes: list[dict]) -> dict:
    """Compare detection between different libraries."""
    if not LIBRARIES_AVAILABLE["better_profanity"]:
        return {}

    print("\nComparing library agreement...")

    better_profanity.load_censor_words()

    agreement_counts = {
        "both_profane": 0,
        "both_clean": 0,
        "better_only": 0,
        "custom_only": 0,
    }

    for joke in jokes:
        text = get_joke_text(joke)

        # Test both
        better_result = better_profanity.contains_profanity(text)
        custom_result = detect_profanity_custom(text)["has_profanity"]

        if better_result and custom_result:
            agreement_counts["both_profane"] += 1
        elif not better_result and not custom_result:
            agreement_counts["both_clean"] += 1
        elif better_result:
            agreement_counts["better_only"] += 1
        else:
            agreement_counts["custom_only"] += 1

    total = len(jokes)
    agreement_rate = ((agreement_counts["both_profane"] + agreement_counts["both_clean"]) / total) * 100

    return {
        "counts": agreement_counts,
        "percentages": {
            key: (count / total) * 100
            for key, count in agreement_counts.items()
        },
        "agreement_rate": agreement_rate,
    }


def main():
    """Run profanity detection comparison."""
    print("Profanity Detection Library Comparison")
    print("=" * 70)

    # Load sample
    sample_size = 500
    print(f"\nLoading {sample_size:,} jokes from taivop dataset...")
    jokes = load_jokes_sample(sample_size)
    print(f"Loaded {len(jokes):,} jokes\n")

    # Test each library
    print("-" * 70)
    better_profanity_results = test_better_profanity(jokes)

    print("\n" + "-" * 70)
    profanity_check_results = test_profanity_check(jokes)

    print("\n" + "-" * 70)
    custom_results = test_custom_wordlist(jokes)

    # Compare if possible
    print("\n" + "-" * 70)
    comparison = compare_libraries(jokes)

    # Compile results
    results = {
        "metadata": {
            "sample_size": len(jokes),
            "libraries_tested": {
                lib: available
                for lib, available in LIBRARIES_AVAILABLE.items()
            },
        },
        "better_profanity": better_profanity_results,
        "profanity_check": profanity_check_results,
        "custom_wordlist": custom_results,
        "library_comparison": comparison,
    }

    # Save results
    output_dir = Path("experiments/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "profanity_detection_comparison.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to {output_file}")

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if better_profanity_results.get("available"):
        print("\nbetter-profanity:")
        print(f"  Profane: {better_profanity_results['profane_count']:,} ({better_profanity_results['profane_percentage']:.1f}%)")
        print(f"  Clean: {better_profanity_results['clean_count']:,}")
        print(f"  Performance: {better_profanity_results['performance']['jokes_per_second']:.0f} jokes/sec")

    if profanity_check_results.get("available"):
        print("\nprofanity-check (ML):")
        print(f"  Profane: {profanity_check_results['profane_count']:,} ({profanity_check_results['profane_percentage']:.1f}%)")
        print(f"  Clean: {profanity_check_results['clean_count']:,}")
        print(f"  Performance: {profanity_check_results['performance']['jokes_per_second']:.0f} jokes/sec")

    if custom_results.get("available"):
        print("\nCustom Wordlist:")
        for severity, count in sorted(custom_results["severity_counts"].items()):
            percentage = custom_results["severity_percentages"][severity]
            print(f"  {severity.capitalize()}: {count:,} ({percentage:.1f}%)")
        print(f"  Performance: {custom_results['performance']['jokes_per_second']:.0f} jokes/sec")

    if comparison:
        print(f"\nLibrary Agreement: {comparison['agreement_rate']:.1f}%")
        print(f"  Both detected profanity: {comparison['counts']['both_profane']:,}")
        print(f"  Both detected clean: {comparison['counts']['both_clean']:,}")
        print(f"  Disagreements: {comparison['counts']['better_only'] + comparison['counts']['custom_only']:,}")

    print("\n" + "=" * 70)
    print("Analysis complete!")
    print("\nRecommendations:")
    print("1. Install better-profanity for fast, accurate detection")
    print("2. Use custom wordlists for joke-specific profanity levels")
    print("3. Combine both approaches for best results")


if __name__ == "__main__":
    main()
