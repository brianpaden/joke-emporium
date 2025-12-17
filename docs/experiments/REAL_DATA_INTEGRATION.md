# Real Data Integration for Experiments

**Purpose:** Use actual taivop dataset for deduplication experiments instead of synthetic fixtures.

**Created:** 2025-12-16

---

## Overview

We have downloaded ~208k real jokes from the taivop dataset in `temp/imports/taivop_joke-dataset/`. This is perfect for testing deduplication approaches with realistic data.

## Available Data

```
temp/imports/taivop_joke-dataset/
├── reddit_jokes.json     (194,553 jokes)
├── stupidstuff.json      (3,773 jokes)
└── wocka.json            (10,019 jokes)
```

## Integration Strategy

### 1. Sample Real Jokes for Test Fixtures

Create realistic test fixtures by sampling from actual data:

```python
# tests/fixtures/create_real_samples.py
import json
import random
from pathlib import Path

def create_normalization_samples():
    """Extract real jokes for normalization testing."""

    # Load reddit jokes
    with open('temp/imports/taivop_joke-dataset/reddit_jokes.json') as f:
        reddit = json.load(f)

    # Sample jokes with different characteristics
    samples = {
        'short_jokes': [],
        'long_jokes': [],
        'punctuation_heavy': [],
        'with_numbers': [],
        'with_emoji': []
    }

    for joke in random.sample(reddit, 1000):
        text = f"{joke.get('title', '')} {joke.get('body', '')}".strip()

        if len(text) < 50:
            samples['short_jokes'].append(joke)
        elif len(text) > 300:
            samples['long_jokes'].append(joke)

        # Count punctuation
        punct_count = sum(1 for c in text if c in '.,!?;:—...')
        if punct_count > 10:
            samples['punctuation_heavy'].append(joke)

        if any(c.isdigit() for c in text):
            samples['with_numbers'].append(joke)

    # Save samples
    output = Path('tests/fixtures/real_joke_samples.json')
    output.write_text(json.dumps(samples, indent=2))
```

### 2. Identify Natural Duplicates

The taivop dataset likely contains natural duplicates across sources:

```python
# experiments/find_natural_duplicates.py
import json
from pathlib import Path
from collections import defaultdict

def find_natural_duplicates():
    """Find naturally occurring duplicates in taivop dataset."""

    # Load all sources
    data_dir = Path('temp/imports/taivop_joke-dataset')
    all_jokes = []

    for json_file in data_dir.glob('*.json'):
        with open(json_file) as f:
            jokes = json.load(f)
            for joke in jokes:
                joke['_source'] = json_file.stem
                all_jokes.append(joke)

    # Group by normalized text
    normalized_groups = defaultdict(list)
    for joke in all_jokes:
        text = f"{joke.get('title', '')} {joke.get('body', '')}".strip().lower()
        normalized_groups[text].append(joke)

    # Find duplicates (same normalized text, different sources)
    duplicates = {
        text: jokes
        for text, jokes in normalized_groups.items()
        if len(jokes) > 1
    }

    print(f"Found {len(duplicates)} natural duplicate groups")

    # Save examples
    examples = list(duplicates.items())[:100]
    output = Path('tests/fixtures/natural_duplicates.json')
    output.write_text(json.dumps(dict(examples), indent=2))

    return duplicates
```

### 3. Benchmark on Subsets

Test performance on increasingly large subsets:

```python
# experiments/benchmark_real_data.py
import json
import time
from pathlib import Path
from typing import Callable

def benchmark_similarity_metric(
    metric_fn: Callable,
    sample_sizes: list[int] = [1000, 5000, 10000, 50000]
):
    """Benchmark similarity metric on real data subsets."""

    # Load data
    with open('temp/imports/taivop_joke-dataset/reddit_jokes.json') as f:
        all_jokes = json.load(f)

    results = []

    for size in sample_sizes:
        sample = all_jokes[:size]

        start = time.time()

        # Run similarity detection
        duplicates_found = 0
        for i, joke1 in enumerate(sample):
            for joke2 in sample[i+1:]:
                if metric_fn(joke1, joke2):
                    duplicates_found += 1

        elapsed = time.time() - start

        results.append({
            'sample_size': size,
            'time_seconds': elapsed,
            'duplicates_found': duplicates_found,
            'jokes_per_second': size / elapsed
        })

        print(f"Size {size:,}: {elapsed:.2f}s, {duplicates_found} duplicates")

    return results
```

### 4. Edge Case Mining

Find real edge cases from the dataset:

```python
# experiments/mine_edge_cases.py
import json
from pathlib import Path

def mine_edge_cases():
    """Find interesting edge cases in real data."""

    with open('temp/imports/taivop_joke-dataset/reddit_jokes.json') as f:
        jokes = json.load(f)

    edge_cases = {
        'very_short': [],        # < 20 chars
        'very_long': [],         # > 500 chars
        'unicode_heavy': [],     # Emoji, special chars
        'number_heavy': [],      # Lots of numbers
        'punctuation_art': [],   # ASCII art, emoji patterns
        'empty_body': [],        # Title only
        'empty_title': []        # Body only
    }

    for joke in jokes:
        title = joke.get('title', '')
        body = joke.get('body', '')
        full_text = f"{title} {body}".strip()

        # Categorize
        if len(full_text) < 20:
            edge_cases['very_short'].append(joke)
        elif len(full_text) > 500:
            edge_cases['very_long'].append(joke)

        if not body:
            edge_cases['empty_body'].append(joke)
        if not title:
            edge_cases['empty_title'].append(joke)

        # Check for unicode
        if any(ord(c) > 127 for c in full_text):
            edge_cases['unicode_heavy'].append(joke)

        # Numbers
        digit_ratio = sum(1 for c in full_text if c.isdigit()) / max(len(full_text), 1)
        if digit_ratio > 0.1:
            edge_cases['number_heavy'].append(joke)

    # Save samples of each category
    output = {}
    for category, cases in edge_cases.items():
        output[category] = cases[:20]  # First 20 examples

    Path('tests/fixtures/edge_cases.json').write_text(json.dumps(output, indent=2))

    # Print summary
    for category, cases in edge_cases.items():
        print(f"{category}: {len(cases)} cases")
```

### 5. Inject Synthetic Variations

Create variations of real jokes for testing:

```python
# experiments/create_variations.py
import json
import random
import re

def create_variations(joke: dict) -> list[dict]:
    """Create variations of a real joke for testing."""

    original_text = f"{joke.get('title', '')} {joke.get('body', '')}".strip()

    variations = [
        ('original', original_text),
    ]

    # Case variation
    variations.append(('lowercase', original_text.lower()))
    variations.append(('uppercase', original_text.upper()))

    # Punctuation variations
    no_punct = re.sub(r'[^\w\s]', '', original_text)
    variations.append(('no_punctuation', no_punct))

    # Whitespace variations
    variations.append(('extra_spaces', '  '.join(original_text.split())))

    # Minor typos (swap 1-2 characters)
    if len(original_text) > 20:
        typo = list(original_text)
        idx = random.randint(0, len(typo) - 2)
        typo[idx], typo[idx + 1] = typo[idx + 1], typo[idx]
        variations.append(('typo', ''.join(typo)))

    # Number variations
    text_with_numbers = re.sub(r'\bthree\b', '3', original_text, flags=re.I)
    text_with_numbers = re.sub(r'\btwo\b', '2', text_with_numbers, flags=re.I)
    if text_with_numbers != original_text:
        variations.append(('number_substitution', text_with_numbers))

    return variations

def create_test_set():
    """Create test set with variations of real jokes."""

    # Load sample
    with open('temp/imports/taivop_joke-dataset/reddit_jokes.json') as f:
        jokes = json.load(f)

    # Pick 100 random jokes
    sample = random.sample(jokes, 100)

    test_set = []
    for joke in sample:
        variations = create_variations(joke)
        test_set.append({
            'original': joke,
            'variations': variations,
            'expected_duplicates': True  # All variations should match
        })

    Path('tests/fixtures/variation_test_set.json').write_text(
        json.dumps(test_set, indent=2)
    )
```

## Experiment Updates

### Update Experiment 7 (Real Data Testing)

Replace the placeholder test plan with:

```python
# experiments/exp7_real_data_testing.py

def run_experiment_7():
    """Test deduplication on real taivop dataset."""

    # Step 1: Load real data
    print("Loading taivop dataset...")
    jokes = load_taivop_jokes()
    print(f"Loaded {len(jokes):,} jokes")

    # Step 2: Find natural duplicates
    print("\nFinding natural duplicates...")
    natural_dups = find_natural_duplicates()
    print(f"Found {len(natural_dups)} duplicate groups")

    # Step 3: Create variation test set
    print("\nCreating variation test set...")
    test_set = create_test_set()
    print(f"Created {len(test_set)} test cases")

    # Step 4: Test each similarity metric
    metrics = [
        ('exact_match', exact_match),
        ('levenshtein_95', lambda t1, t2: levenshtein_similarity(t1, t2, 0.95)),
        ('ngram_90', lambda t1, t2: ngram_similarity(t1, t2, n=3, threshold=0.90)),
        ('jaccard_90', lambda t1, t2: jaccard_similarity(t1, t2, 0.90)),
    ]

    results = {}
    for name, metric_fn in metrics:
        print(f"\nTesting {name}...")
        results[name] = benchmark_metric(metric_fn, test_set, natural_dups)

    # Step 5: Generate report
    generate_report(results)
```

## Benefits of Real Data

1. **Realistic Performance Metrics**: Actual processing times on real data
2. **Natural Duplicates**: Find duplicates that actually exist in the wild
3. **Edge Cases**: Discover edge cases we wouldn't think to create
4. **Scale Testing**: Test on 200k+ jokes instead of 1k synthetic examples
5. **Validation**: Verify assumptions about joke structure and content

## Integration Checklist

- [ ] Create `experiments/` directory structure
- [ ] Write script to sample real jokes for fixtures
- [ ] Find natural duplicates in taivop dataset
- [ ] Mine edge cases from real data
- [ ] Create variation test set from real jokes
- [ ] Update Experiment 7 with real data tests
- [ ] Benchmark all similarity metrics on real data
- [ ] Document findings in experiment results

## Next Steps

1. Run `find_natural_duplicates.py` to discover real duplicates
2. Run `mine_edge_cases.py` to find interesting test cases
3. Create `tests/fixtures/real_samples.json` with actual jokes
4. Update unit tests to use real samples alongside synthetic ones
5. Benchmark deduplication approaches on full 200k dataset
