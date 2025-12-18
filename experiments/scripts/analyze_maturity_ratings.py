#!/usr/bin/env python3
"""Analyze maturity ratings in the taivop dataset.

This script examines jokes from the taivop dataset to understand:
1. Distribution of content types (profanity, sexual, violent, etc.)
2. Natural maturity rating distribution
3. Common patterns requiring different rating levels
4. Edge cases and ambiguous content

This provides baseline understanding before implementing auto-rating.
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def load_jokes_sample(max_jokes: int = 1000) -> list[dict[str, Any]]:
    """Load a sample of jokes from taivop dataset."""
    data_dir = Path("temp/imports/taivop_joke-dataset")

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        print("Please run the taivop import first to download the data.")
        sys.exit(1)

    all_jokes = []

    # Load from each source
    for json_file in sorted(data_dir.glob("*.json")):
        source_name = json_file.stem
        print(f"Loading {json_file.name}...")

        with open(json_file, encoding="utf-8") as f:
            jokes = json.load(f)

        # Add source metadata
        for joke in jokes[:max_jokes]:
            if isinstance(joke, dict):
                joke["_source"] = source_name
                all_jokes.append(joke)

        if len(all_jokes) >= max_jokes:
            break

    return all_jokes[:max_jokes]


def get_joke_text(joke: dict, source: str) -> str:
    """Extract full text from joke."""
    if source == "reddit_jokes":
        title = joke.get("title", "")
        body = joke.get("body", "")
        return f"{title} {body}".strip()
    else:
        return joke.get("body", "").strip()


def analyze_profanity_patterns(jokes: list[dict]) -> dict:
    """Analyze profanity patterns in jokes."""

    # Common profanity words by severity
    # These are for detection, not for display
    mild_words = ["damn", "hell", "crap", "ass", "piss", "bastard"]
    moderate_words = ["shit", "bitch", "dick", "cock", "pussy"]
    strong_words = ["fuck", "fucking", "fucked", "motherfucker", "cunt"]

    # Track occurrences
    profanity_counts = {
        "mild": 0,
        "moderate": 0,
        "strong": 0,
        "none": 0,
    }

    examples = defaultdict(list)

    for joke in jokes:
        source = joke.get("_source", "unknown")
        text = get_joke_text(joke, source).lower()

        has_mild = any(word in text for word in mild_words)
        has_moderate = any(word in text for word in moderate_words)
        has_strong = any(word in text for word in strong_words)

        if has_strong:
            profanity_counts["strong"] += 1
            examples["strong"].append(text[:100])
        elif has_moderate:
            profanity_counts["moderate"] += 1
            examples["moderate"].append(text[:100])
        elif has_mild:
            profanity_counts["mild"] += 1
            examples["mild"].append(text[:100])
        else:
            profanity_counts["none"] += 1

    # Limit examples
    for severity in examples:
        examples[severity] = examples[severity][:5]

    return {
        "counts": profanity_counts,
        "percentages": {
            severity: (count / len(jokes) * 100)
            for severity, count in profanity_counts.items()
        },
        "examples": dict(examples),
    }


def analyze_sexual_content(jokes: list[dict]) -> dict:
    """Analyze sexual content patterns."""

    # Sexual content indicators
    sexual_terms = [
        "sex", "sexual", "nude", "naked", "strip",
        "orgasm", "erection", "viagra", "condom",
        "penis", "vagina", "breast", "boobs",
    ]

    innuendo_patterns = [
        r"\bthat's what she said\b",
        r"\bin bed\b",  # Fortune cookie jokes
        r"\bhard\b.*\bon\b",  # Double meaning
        r"\bcome\b.*\binside\b",  # Double meaning
    ]

    sexual_count = 0
    innuendo_count = 0
    examples = []

    for joke in jokes:
        source = joke.get("_source", "unknown")
        text = get_joke_text(joke, source).lower()

        has_sexual = any(term in text for term in sexual_terms)
        has_innuendo = any(re.search(pattern, text, re.IGNORECASE) for pattern in innuendo_patterns)

        if has_sexual or has_innuendo:
            if has_sexual:
                sexual_count += 1
            if has_innuendo:
                innuendo_count += 1

            if len(examples) < 10:
                examples.append({
                    "text": text[:150],
                    "sexual": has_sexual,
                    "innuendo": has_innuendo,
                })

    return {
        "sexual_count": sexual_count,
        "innuendo_count": innuendo_count,
        "sexual_percentage": (sexual_count / len(jokes) * 100),
        "innuendo_percentage": (innuendo_count / len(jokes) * 100),
        "examples": examples,
    }


def analyze_dark_humor(jokes: list[dict]) -> dict:
    """Analyze dark humor patterns."""

    dark_themes = [
        "death", "die", "died", "dead", "kill", "murder",
        "suicide", "cancer", "funeral", "grave", "coffin",
        "hitler", "nazi", "holocaust",
    ]

    dark_count = 0
    theme_counter = Counter()
    examples = []

    for joke in jokes:
        source = joke.get("_source", "unknown")
        text = get_joke_text(joke, source).lower()

        found_themes = [theme for theme in dark_themes if theme in text]

        if found_themes:
            dark_count += 1
            theme_counter.update(found_themes)

            if len(examples) < 10:
                examples.append({
                    "text": text[:150],
                    "themes": found_themes,
                })

    return {
        "dark_count": dark_count,
        "dark_percentage": (dark_count / len(jokes) * 100),
        "common_themes": dict(theme_counter.most_common(10)),
        "examples": examples,
    }


def analyze_violence(jokes: list[dict]) -> dict:
    """Analyze violent content."""

    violence_terms = [
        "blood", "bleeding", "stab", "shoot", "shot",
        "gun", "knife", "weapon", "attack", "fight",
        "punch", "kick", "beat", "torture",
    ]

    violence_count = 0
    examples = []

    for joke in jokes:
        source = joke.get("_source", "unknown")
        text = get_joke_text(joke, source).lower()

        has_violence = any(term in text for term in violence_terms)

        if has_violence:
            violence_count += 1

            if len(examples) < 10:
                examples.append(text[:150])

    return {
        "violence_count": violence_count,
        "violence_percentage": (violence_count / len(jokes) * 100),
        "examples": examples,
    }


def suggest_ratings_distribution(jokes: list[dict]) -> dict:
    """Suggest maturity rating distribution based on simple heuristics."""

    # Simple rating suggestions based on profanity analysis
    ratings = Counter()

    mild_words = ["damn", "hell", "crap", "ass"]
    moderate_words = ["shit", "bitch", "dick"]
    strong_words = ["fuck", "cunt"]

    for joke in jokes:
        source = joke.get("_source", "unknown")
        text = get_joke_text(joke, source).lower()

        # Count profanity by severity
        mild_count = sum(1 for word in mild_words if word in text)
        moderate_count = sum(1 for word in moderate_words if word in text)
        strong_count = sum(1 for word in strong_words if word in text)

        # Simple rating logic
        if strong_count > 0:
            ratings["R"] += 1
        elif moderate_count > 1:
            ratings["R"] += 1
        elif moderate_count == 1:
            ratings["PG13"] += 1
        elif mild_count > 0:
            ratings["PG"] += 1
        else:
            ratings["G"] += 1

    return {
        "distribution": dict(ratings),
        "percentages": {
            rating: (count / len(jokes) * 100)
            for rating, count in ratings.items()
        },
    }


def analyze_edge_cases(jokes: list[dict]) -> dict:
    """Find interesting edge cases."""

    edge_cases = {
        "very_short": [],  # < 20 chars
        "very_long": [],  # > 500 chars
        "has_emoji": [],
        "all_caps": [],
        "multiple_questions": [],  # Multiple '?' - could be Q&A format
    }

    for joke in jokes:
        source = joke.get("_source", "unknown")
        text = get_joke_text(joke, source)

        if len(text) < 20:
            edge_cases["very_short"].append(text)

        if len(text) > 500:
            edge_cases["very_long"].append(text[:200] + "...")

        # Check for emoji (unicode > 0x1F000)
        if any(ord(c) > 0x1F000 for c in text):
            edge_cases["has_emoji"].append(text[:150])

        # All caps (at least 50% uppercase)
        alpha_chars = [c for c in text if c.isalpha()]
        if alpha_chars and sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars) > 0.5:
            edge_cases["all_caps"].append(text[:150])

        # Multiple questions
        if text.count("?") >= 2:
            edge_cases["multiple_questions"].append(text[:150])

    # Limit examples
    for category in edge_cases:
        edge_cases[category] = edge_cases[category][:10]

    return {
        category: {
            "count": len(cases),
            "examples": cases,
        }
        for category, cases in edge_cases.items()
    }


def main():
    """Run maturity rating analysis."""
    print("Maturity Rating Analysis")
    print("=" * 70)

    # Load sample
    sample_size = 1000
    print(f"\nLoading {sample_size:,} jokes from taivop dataset...")
    jokes = load_jokes_sample(sample_size)
    print(f"Loaded {len(jokes):,} jokes")

    # Run analyses
    print("\n" + "-" * 70)
    print("Analyzing profanity patterns...")
    profanity_results = analyze_profanity_patterns(jokes)

    print("\n" + "-" * 70)
    print("Analyzing sexual content...")
    sexual_results = analyze_sexual_content(jokes)

    print("\n" + "-" * 70)
    print("Analyzing dark humor...")
    dark_results = analyze_dark_humor(jokes)

    print("\n" + "-" * 70)
    print("Analyzing violence...")
    violence_results = analyze_violence(jokes)

    print("\n" + "-" * 70)
    print("Suggesting rating distribution...")
    rating_distribution = suggest_ratings_distribution(jokes)

    print("\n" + "-" * 70)
    print("Finding edge cases...")
    edge_cases = analyze_edge_cases(jokes)

    # Compile results
    results = {
        "metadata": {
            "sample_size": len(jokes),
            "sources": list({j.get("_source") for j in jokes}),
        },
        "profanity_analysis": profanity_results,
        "sexual_content_analysis": sexual_results,
        "dark_humor_analysis": dark_results,
        "violence_analysis": violence_results,
        "rating_distribution": rating_distribution,
        "edge_cases": edge_cases,
    }

    # Save results
    output_dir = Path("experiments/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "maturity_rating_analysis.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to {output_file}")

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print("\nProfanity Distribution:")
    for severity, percentage in profanity_results["percentages"].items():
        count = profanity_results["counts"][severity]
        print(f"  {severity.capitalize()}: {count:,} ({percentage:.1f}%)")

    print("\nSexual Content:")
    print(f"  Explicit terms: {sexual_results['sexual_count']:,} ({sexual_results['sexual_percentage']:.1f}%)")
    print(f"  Innuendo: {sexual_results['innuendo_count']:,} ({sexual_results['innuendo_percentage']:.1f}%)")

    print("\nDark Humor:")
    print(f"  Dark themes: {dark_results['dark_count']:,} ({dark_results['dark_percentage']:.1f}%)")

    print("\nViolence:")
    print(f"  Violent content: {violence_results['violence_count']:,} ({violence_results['violence_percentage']:.1f}%)")

    print("\nSuggested Rating Distribution:")
    for rating, percentage in sorted(rating_distribution["percentages"].items()):
        count = rating_distribution["distribution"][rating]
        print(f"  {rating}: {count:,} ({percentage:.1f}%)")

    print("\n" + "=" * 70)
    print("Analysis complete!")


if __name__ == "__main__":
    main()
