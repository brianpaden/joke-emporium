#!/usr/bin/env python3
"""Mine edge cases from the taivop dataset.

This script identifies interesting edge cases like very short/long jokes,
unicode-heavy content, number-heavy content, etc.
"""

import json
import re
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


def categorize_joke(joke: dict, source: str) -> list[str]:
    """Categorize a joke based on its characteristics."""
    categories = []

    title = joke.get("title", "")
    body = joke.get("body", "")
    full_text = get_joke_text(joke, source)

    if not full_text:
        categories.append("empty")
        return categories

    # Length-based categories
    length = len(full_text)
    if length < 20:
        categories.append("very_short")
    elif length < 50:
        categories.append("short")
    elif length > 500:
        categories.append("very_long")
    elif length > 300:
        categories.append("long")

    # Structure categories
    if not body:
        categories.append("empty_body")
    if not title and source == "reddit_jokes":
        categories.append("empty_title")

    # Unicode and special characters
    non_ascii_count = sum(1 for c in full_text if ord(c) > 127)
    if non_ascii_count > 0:
        categories.append("unicode")
    if non_ascii_count > len(full_text) * 0.1:
        categories.append("unicode_heavy")

    # Emoji detection
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    if emoji_pattern.search(full_text):
        categories.append("emoji")

    # Number analysis
    digit_count = sum(1 for c in full_text if c.isdigit())
    if digit_count > 0:
        categories.append("has_numbers")
    if digit_count > len(full_text) * 0.1:
        categories.append("number_heavy")

    # Punctuation analysis
    punct_chars = set('.,!?;:—..."\'-')
    punct_count = sum(1 for c in full_text if c in punct_chars)
    if punct_count > len(full_text) * 0.15:
        categories.append("punctuation_heavy")

    # Special patterns
    if "..." in full_text or "…" in full_text:
        categories.append("ellipsis")
    if full_text.count("\n") > 5:
        categories.append("multiline")
    if re.search(r'[A-Z]{3,}', full_text):
        categories.append("shouting")

    # Code or technical content
    if any(pattern in full_text for pattern in ["```", "def ", "class ", "function", "import "]):
        categories.append("code_like")

    # URLs or links
    if re.search(r'https?://', full_text):
        categories.append("contains_url")

    return categories


def mine_edge_cases():
    """Mine edge cases from taivop dataset."""

    print("Mining edge cases from taivop dataset...")
    print("=" * 70)

    # Set up paths
    data_dir = Path("temp/imports/taivop_joke-dataset")
    output_dir = Path("experiments/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        print("Please run the taivop import first to download the data.")
        sys.exit(1)

    # Track edge cases by category
    edge_cases = {}
    category_counts = {}

    # Process each source
    for json_file in sorted(data_dir.glob("*.json")):
        source_name = json_file.stem
        print(f"\nProcessing {json_file.name}...")

        try:
            with open(json_file, encoding="utf-8") as f:
                jokes = json.load(f)

            if not isinstance(jokes, list):
                print(f"  Warning: {json_file.name} is not a list, skipping")
                continue

            for joke in jokes:
                if not isinstance(joke, dict):
                    continue

                categories = categorize_joke(joke, source_name)

                for category in categories:
                    # Track count
                    category_counts[category] = category_counts.get(category, 0) + 1

                    # Store example (limit to first 20 per category)
                    if category not in edge_cases:
                        edge_cases[category] = []

                    if len(edge_cases[category]) < 20:
                        text = get_joke_text(joke, source_name)
                        edge_cases[category].append({
                            "source": source_name,
                            "id": joke.get("id"),
                            "text": text,
                            "length": len(text),
                            "title": joke.get("title", ""),
                            "body": joke.get("body", "")[:200] if joke.get("body") else ""
                        })

            print(f"  Processed {len(jokes):,} jokes")

        except Exception as e:
            print(f"  Error processing {json_file.name}: {e}")
            continue

    # Summary
    print(f"\n{'-' * 70}")
    print("Edge case summary:")
    print(f"{'-' * 70}")

    for category in sorted(category_counts.keys()):
        count = category_counts[category]
        print(f"  {category:20} {count:>10,} cases")

    # Save results
    print(f"\n{'-' * 70}")
    print("Saving results...")

    output_file = output_dir / "edge_cases.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "summary": {
                "total_categories": len(category_counts),
                "category_counts": category_counts
            },
            "examples": edge_cases
        }, f, indent=2, ensure_ascii=False)

    print(f"Saved edge cases to {output_file}")

    # Create filtered test fixtures
    test_fixtures = {}
    for category in ["very_short", "very_long", "unicode_heavy", "number_heavy", "emoji"]:
        if category in edge_cases:
            test_fixtures[category] = edge_cases[category][:5]  # Top 5 examples

    fixture_file = Path("tests/fixtures/edge_case_samples.json")
    fixture_file.parent.mkdir(parents=True, exist_ok=True)

    with open(fixture_file, "w", encoding="utf-8") as f:
        json.dump(test_fixtures, f, indent=2, ensure_ascii=False)

    print(f"Saved test fixtures to {fixture_file}")

    # Print interesting examples
    print(f"\n{'-' * 70}")
    print("Interesting examples:")
    print(f"{'-' * 70}")

    for category in ["very_short", "very_long", "unicode_heavy", "emoji"]:
        if category in edge_cases and edge_cases[category]:
            print(f"\n{category.upper().replace('_', ' ')}:")
            example = edge_cases[category][0]
            text = example["text"]
            display_text = text if len(text) <= 100 else text[:100] + "..."
            print(f"  Source: {example['source']}")
            print(f"  Length: {example['length']} chars")
            # Encode unicode safely for Windows console
            try:
                print(f"  Text: {display_text}")
            except UnicodeEncodeError:
                # Fallback: replace non-ASCII with ?
                safe_text = display_text.encode('ascii', errors='replace').decode('ascii')
                print(f"  Text: {safe_text}")

    print(f"\n{'-' * 70}")
    print("Mining complete!")


if __name__ == "__main__":
    mine_edge_cases()
