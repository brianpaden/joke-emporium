#!/usr/bin/env python3
"""Find naturally occurring duplicates in the taivop dataset.

This script identifies jokes that appear in multiple source files
(reddit, stupidstuff, wocka) with identical or very similar text.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    return text.strip().lower()


def get_joke_text(joke: dict, source: str) -> str:
    """Extract text from joke based on source format."""
    if source == "reddit_jokes":
        title = joke.get("title", "")
        body = joke.get("body", "")
        return f"{title} {body}".strip()
    elif source == "wocka":
        # Wocka stores full joke in body
        return joke.get("body", "").strip()
    elif source == "stupidstuff":
        return joke.get("body", "").strip()
    else:
        # Fallback
        return str(joke.get("body", "") or joke.get("title", "")).strip()


def find_natural_duplicates():
    """Find duplicates across taivop dataset sources."""

    print("Finding natural duplicates in taivop dataset...")
    print("=" * 70)

    # Set up paths
    data_dir = Path("temp/imports/taivop_joke-dataset")
    output_dir = Path("experiments/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        print("Please run the taivop import first to download the data.")
        sys.exit(1)

    # Load all jokes
    all_jokes = []
    source_counts = {}

    for json_file in sorted(data_dir.glob("*.json")):
        source_name = json_file.stem
        print(f"\nLoading {json_file.name}...")

        try:
            with open(json_file, encoding="utf-8") as f:
                jokes = json.load(f)

            if not isinstance(jokes, list):
                print(f"  Warning: {json_file.name} is not a list, skipping")
                continue

            # Add source metadata to each joke
            for joke in jokes:
                if isinstance(joke, dict):
                    joke["_source"] = source_name
                    joke["_source_file"] = json_file.name
                    all_jokes.append(joke)

            source_counts[source_name] = len(jokes)
            print(f"  Loaded {len(jokes):,} jokes")

        except Exception as e:
            print(f"  Error loading {json_file.name}: {e}")
            continue

    print(f"\n{'-' * 70}")
    print(f"Total jokes loaded: {len(all_jokes):,}")
    print(f"\nBreakdown by source:")
    for source, count in sorted(source_counts.items()):
        print(f"  {source}: {count:,}")

    # Group by normalized text
    print(f"\n{'-' * 70}")
    print("Grouping jokes by normalized text...")

    normalized_groups = defaultdict(list)

    for joke in all_jokes:
        source = joke.get("_source", "unknown")
        text = get_joke_text(joke, source)

        if not text:
            continue

        normalized = normalize_text(text)

        # Store original joke data
        normalized_groups[normalized].append({
            "source": source,
            "source_file": joke.get("_source_file", "unknown"),
            "id": joke.get("id"),
            "text": text,
            "original": joke
        })

    # Find duplicates (groups with 2+ entries)
    duplicates = {
        text: jokes
        for text, jokes in normalized_groups.items()
        if len(jokes) > 1
    }

    print(f"Found {len(duplicates):,} duplicate groups")

    # Analyze duplicates
    print(f"\n{'-' * 70}")
    print("Analyzing duplicates...")

    cross_source_dups = 0
    same_source_dups = 0

    for text, jokes in duplicates.items():
        sources = {j["source"] for j in jokes}
        if len(sources) > 1:
            cross_source_dups += 1
        else:
            same_source_dups += 1

    print(f"\nDuplicate breakdown:")
    print(f"  Cross-source duplicates: {cross_source_dups:,}")
    print(f"  Same-source duplicates: {same_source_dups:,}")
    print(f"  Total duplicate groups: {len(duplicates):,}")

    # Save results
    print(f"\n{'-' * 70}")
    print("Saving results...")

    # Save top 100 duplicate groups as examples
    examples = []
    for i, (text, jokes) in enumerate(sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)[:100]):
        examples.append({
            "normalized_text": text,
            "count": len(jokes),
            "sources": list({j["source"] for j in jokes}),
            "instances": [
                {
                    "source": j["source"],
                    "id": j["id"],
                    "text": j["text"][:200]  # Truncate for readability
                }
                for j in jokes
            ]
        })

    output_file = output_dir / "natural_duplicates.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "summary": {
                "total_jokes": len(all_jokes),
                "unique_jokes": len(normalized_groups) - len(duplicates),
                "duplicate_groups": len(duplicates),
                "cross_source_duplicates": cross_source_dups,
                "same_source_duplicates": same_source_dups,
                "source_counts": source_counts
            },
            "examples": examples
        }, f, indent=2, ensure_ascii=False)

    print(f"Saved results to {output_file}")

    # Save full duplicate data
    full_output = output_dir / "natural_duplicates_full.json"
    full_data = {
        normalized: [
            {
                "source": j["source"],
                "id": j["id"],
                "text": j["text"]
            }
            for j in jokes
        ]
        for normalized, jokes in duplicates.items()
    }

    with open(full_output, "w", encoding="utf-8") as f:
        json.dump(full_data, f, indent=2, ensure_ascii=False)

    print(f"Saved full duplicate data to {full_output}")

    # Print some interesting examples
    print(f"\n{'-' * 70}")
    print("Top 10 most duplicated jokes:")
    print(f"{'-' * 70}")

    for i, (text, jokes) in enumerate(sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)[:10], 1):
        print(f"\n{i}. Found in {len(jokes)} places:")
        sources = ", ".join(sorted({j["source"] for j in jokes}))
        print(f"   Sources: {sources}")
        print(f"   Text: {jokes[0]['text'][:100]}{'...' if len(jokes[0]['text']) > 100 else ''}")

    print(f"\n{'-' * 70}")
    print("Analysis complete!")


if __name__ == "__main__":
    find_natural_duplicates()
