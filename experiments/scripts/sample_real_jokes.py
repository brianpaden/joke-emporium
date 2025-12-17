#!/usr/bin/env python3
"""Sample real jokes from taivop dataset for test fixtures.

Creates realistic test fixtures by sampling diverse jokes from the dataset.
"""

import json
import random
import sys
from pathlib import Path


def get_joke_text(joke: dict, source: str) -> str:
    """Extract text from joke based on source format."""
    if source == "reddit_jokes":
        title = joke.get("title", "")
        body = joke.get("body", "")
        return f"{title} {body}".strip()
    elif source == "wocka":
        return joke.get("body", "").strip()
    elif source == "stupidstuff":
        return joke.get("body", "").strip()
    else:
        return str(joke.get("body", "") or joke.get("title", "")).strip()


def sample_real_jokes():
    """Sample diverse jokes from taivop dataset."""

    print("Sampling real jokes from taivop dataset...")
    print("=" * 70)

    # Set up paths
    data_dir = Path("temp/imports/taivop_joke-dataset")
    output_dir = Path("tests/fixtures")
    output_dir.mkdir(parents=True, exist_ok=True)

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        print("Please run the taivop import first to download the data.")
        sys.exit(1)

    # Load all jokes
    all_jokes = {}

    for json_file in sorted(data_dir.glob("*.json")):
        source_name = json_file.stem
        print(f"Loading {json_file.name}...")

        try:
            with open(json_file, encoding="utf-8") as f:
                jokes = json.load(f)

            if not isinstance(jokes, list):
                continue

            all_jokes[source_name] = [j for j in jokes if isinstance(j, dict)]
            print(f"  Loaded {len(all_jokes[source_name]):,} jokes")

        except Exception as e:
            print(f"  Error: {e}")
            continue

    # Sample strategy: diverse jokes across different characteristics
    print(f"\n{'-' * 70}")
    print("Creating diverse sample sets...")

    samples = {
        "short_jokes": [],
        "medium_jokes": [],
        "long_jokes": [],
        "qa_jokes": [],
        "one_liners": [],
        "from_reddit": [],
        "from_stupidstuff": [],
        "from_wocka": [],
        "random_sample": [],
    }

    # Sample from each source
    for source_name, jokes in all_jokes.items():
        print(f"\nSampling from {source_name}...")

        # Take random samples
        sample_size = min(100, len(jokes))
        source_sample = random.sample(jokes, sample_size)

        for joke in source_sample:
            text = get_joke_text(joke, source_name)
            if not text:
                continue

            joke_data = {
                "source": source_name,
                "id": joke.get("id"),
                "text": text,
                "length": len(text),
                "title": joke.get("title", ""),
                "body": joke.get("body", ""),
                "category": joke.get("category", ""),
                "score": joke.get("score"),
                "rating": joke.get("rating"),
            }

            # Categorize by length
            if len(text) < 100:
                if len(samples["short_jokes"]) < 20:
                    samples["short_jokes"].append(joke_data)
            elif len(text) < 300:
                if len(samples["medium_jokes"]) < 20:
                    samples["medium_jokes"].append(joke_data)
            else:
                if len(samples["long_jokes"]) < 20:
                    samples["long_jokes"].append(joke_data)

            # Categorize by structure
            # Q&A: has both title and body (for reddit/wocka) or has double newline (wocka)
            if source_name == "reddit_jokes" and joke.get("title") and joke.get("body"):
                if len(samples["qa_jokes"]) < 20:
                    samples["qa_jokes"].append(joke_data)
            elif source_name == "wocka" and "\r\n\r\n" in joke.get("body", ""):
                if len(samples["qa_jokes"]) < 20:
                    samples["qa_jokes"].append(joke_data)
            elif source_name == "stupidstuff":
                if len(samples["one_liners"]) < 20:
                    samples["one_liners"].append(joke_data)

            # By source
            if source_name == "reddit_jokes" and len(samples["from_reddit"]) < 20:
                samples["from_reddit"].append(joke_data)
            elif source_name == "stupidstuff" and len(samples["from_stupidstuff"]) < 20:
                samples["from_stupidstuff"].append(joke_data)
            elif source_name == "wocka" and len(samples["from_wocka"]) < 20:
                samples["from_wocka"].append(joke_data)

            # Random overall sample
            if len(samples["random_sample"]) < 50:
                samples["random_sample"].append(joke_data)

    # Print summary
    print(f"\n{'-' * 70}")
    print("Sample summary:")
    for category, jokes in sorted(samples.items()):
        print(f"  {category:20} {len(jokes):>3} jokes")

    # Save samples
    output_file = output_dir / "real_joke_samples.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)

    print(f"\n{'-' * 70}")
    print(f"Saved samples to {output_file}")

    # Create a compact version for quick testing
    compact_samples = {
        "diverse_sample": (
            samples["short_jokes"][:5]
            + samples["medium_jokes"][:5]
            + samples["long_jokes"][:5]
            + samples["qa_jokes"][:5]
            + samples["one_liners"][:5]
        )
    }

    compact_file = output_dir / "real_jokes_compact.json"
    with open(compact_file, "w", encoding="utf-8") as f:
        json.dump(compact_samples, f, indent=2, ensure_ascii=False)

    print(f"Saved compact sample to {compact_file}")

    # Print some examples
    print(f"\n{'-' * 70}")
    print("Sample examples:")
    print(f"{'-' * 70}")

    for category in ["short_jokes", "qa_jokes", "one_liners"]:
        if samples[category]:
            example = samples[category][0]
            print(f"\n{category.replace('_', ' ').title()}:")
            print(f"  Source: {example['source']}")
            print(f"  Length: {example['length']} chars")
            text = example["text"]
            display = text if len(text) <= 150 else text[:150] + "..."
            print(f"  Text: {display}")

    print(f"\n{'-' * 70}")
    print("Sampling complete!")


if __name__ == "__main__":
    random.seed(42)  # Reproducible samples
    sample_real_jokes()
