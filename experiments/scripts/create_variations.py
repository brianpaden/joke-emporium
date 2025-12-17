#!/usr/bin/env python3
"""Create controlled variations of real jokes for testing similarity metrics.

This script generates different variations of jokes (typos, punctuation changes,
case changes, etc.) to test how well similarity metrics can detect near-duplicates.
"""

import json
import random
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


def create_variations(joke: dict, source: str) -> list[dict]:
    """Create variations of a joke for testing.

    Returns list of (variation_type, text) tuples.
    """
    original_text = get_joke_text(joke, source)

    if not original_text or len(original_text) < 20:
        return []

    variations = [{"type": "original", "text": original_text}]

    # 1. Case variations
    variations.append({"type": "lowercase", "text": original_text.lower(), "expected_match": True})

    variations.append({"type": "uppercase", "text": original_text.upper(), "expected_match": True})

    variations.append({"type": "title_case", "text": original_text.title(), "expected_match": True})

    # 2. Punctuation variations
    no_punct = re.sub(r"[.,!?;:]", "", original_text)
    if no_punct != original_text:
        variations.append({"type": "no_punctuation", "text": no_punct, "expected_match": True})

    extra_punct = original_text.replace(" ", " . ").replace("!", "!!").replace("?", "??")
    variations.append(
        {
            "type": "extra_punctuation",
            "text": extra_punct,
            "expected_match": "maybe",  # Depends on normalization
        }
    )

    # 3. Whitespace variations
    variations.append({"type": "extra_spaces", "text": "  ".join(original_text.split()), "expected_match": True})

    variations.append(
        {
            "type": "tabs_and_newlines",
            "text": original_text.replace(" ", "\t").replace(".", ".\n"),
            "expected_match": True,
        }
    )

    # 4. Typos (character-level)
    if len(original_text) > 30:
        # Swap adjacent characters
        chars = list(original_text)
        swap_idx = random.randint(5, len(chars) - 5)
        chars[swap_idx], chars[swap_idx + 1] = chars[swap_idx + 1], chars[swap_idx]
        variations.append(
            {
                "type": "typo_swap",
                "text": "".join(chars),
                "expected_match": "fuzzy",  # Needs Levenshtein
            }
        )

        # Delete a character
        chars = list(original_text)
        del_idx = random.randint(5, len(chars) - 5)
        del chars[del_idx]
        variations.append({"type": "typo_deletion", "text": "".join(chars), "expected_match": "fuzzy"})

        # Insert a character
        chars = list(original_text)
        ins_idx = random.randint(5, len(chars) - 5)
        chars.insert(ins_idx, random.choice("abcdefghijklmnopqrstuvwxyz"))
        variations.append({"type": "typo_insertion", "text": "".join(chars), "expected_match": "fuzzy"})

    # 5. Number variations
    # "three" -> "3"
    text_with_numbers = original_text
    replacements = {r"\bone\b": "1", r"\btwo\b": "2", r"\bthree\b": "3", r"\bfour\b": "4", r"\bfive\b": "5"}

    for pattern, replacement in replacements.items():
        text_with_numbers = re.sub(pattern, replacement, text_with_numbers, flags=re.IGNORECASE)

    if text_with_numbers != original_text:
        variations.append(
            {
                "type": "number_substitution",
                "text": text_with_numbers,
                "expected_match": "maybe",  # Depends on normalization
            }
        )

    # 6. Contraction variations
    contractions = {
        r"you're": "you are",
        r"don't": "do not",
        r"can't": "cannot",
        r"won't": "will not",
        r"I'm": "I am",
        r"it's": "it is",
    }

    expanded = original_text
    for contraction, expansion in contractions.items():
        expanded = re.sub(contraction, expansion, expanded, flags=re.IGNORECASE)

    if expanded != original_text:
        variations.append({"type": "expanded_contractions", "text": expanded, "expected_match": "maybe"})

    # 7. Minor word changes (paraphrase simulation)
    # Only for very specific patterns we can reliably change
    paraphrase = original_text
    simple_substitutions = {
        r"\bvery\s+": "really ",
        r"\bsaid\b": "told",
        r"\basked\b": "said",
    }

    for pattern, replacement in simple_substitutions.items():
        paraphrase = re.sub(pattern, replacement, paraphrase, flags=re.IGNORECASE)

    if paraphrase != original_text:
        variations.append(
            {
                "type": "minor_paraphrase",
                "text": paraphrase,
                "expected_match": "semantic",  # Needs semantic similarity
            }
        )

    return variations


def create_variation_test_set():
    """Create test set with variations of real jokes."""

    print("Creating variation test set from real jokes...")
    print("=" * 70)

    # Set up paths
    data_dir = Path("temp/imports/taivop_joke-dataset")
    output_dir = Path("tests/fixtures")
    output_dir.mkdir(parents=True, exist_ok=True)

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        print("Please run the taivop import first to download the data.")
        sys.exit(1)

    # Load a sample of jokes from each source
    all_samples = []

    for json_file in sorted(data_dir.glob("*.json")):
        source_name = json_file.stem
        print(f"Loading {json_file.name}...")

        try:
            with open(json_file, encoding="utf-8") as f:
                jokes = json.load(f)

            if not isinstance(jokes, list):
                continue

            # Sample 50 jokes from each source
            sample_size = min(50, len(jokes))
            sample = random.sample([j for j in jokes if isinstance(j, dict)], sample_size)

            for joke in sample:
                all_samples.append((joke, source_name))

            print(f"  Sampled {len(sample)} jokes")

        except Exception as e:
            print(f"  Error: {e}")
            continue

    # Create variations for sampled jokes
    print(f"\n{'-' * 70}")
    print("Creating variations...")

    test_set = []
    variation_counts = {}

    for joke, source in all_samples:
        variations = create_variations(joke, source)

        if not variations:
            continue

        original_text = variations[0]["text"]

        # Count variation types
        for var in variations[1:]:  # Skip original
            var_type = var["type"]
            variation_counts[var_type] = variation_counts.get(var_type, 0) + 1

        test_set.append(
            {
                "source": source,
                "original_id": joke.get("id"),
                "original_text": original_text,
                "variations": variations[1:],  # Exclude original from variations list
                "total_variations": len(variations) - 1,
            }
        )

    print(f"Created variations for {len(test_set)} jokes")
    print("\nVariation type counts:")
    for var_type in sorted(variation_counts.keys()):
        print(f"  {var_type:25} {variation_counts[var_type]:>5}")

    # Save test set
    output_file = output_dir / "variation_test_set.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(test_set, f, indent=2, ensure_ascii=False)

    print(f"\n{'-' * 70}")
    print(f"Saved variation test set to {output_file}")

    # Create compact version with just 10 examples
    compact = test_set[:10]
    compact_file = output_dir / "variation_test_set_compact.json"
    with open(compact_file, "w", encoding="utf-8") as f:
        json.dump(compact, f, indent=2, ensure_ascii=False)

    print(f"Saved compact version to {compact_file}")

    # Print example
    print(f"\n{'-' * 70}")
    print("Example test case:")
    print(f"{'-' * 70}")

    if test_set:
        example = test_set[0]
        print(f"\nSource: {example['source']}")
        print(f"Original: {example['original_text'][:100]}...")
        print(f"\nVariations ({example['total_variations']} total):")
        for var in example["variations"][:5]:
            text = var["text"][:80] + "..." if len(var["text"]) > 80 else var["text"]
            match = var.get("expected_match", "unknown")
            print(f"  [{var['type']:20}] {match:8} - {text}")

    print(f"\n{'-' * 70}")
    print("Variation test set created!")


if __name__ == "__main__":
    random.seed(42)  # Reproducible variations
    create_variation_test_set()
