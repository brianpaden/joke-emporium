# Text Normalization Strategies for Joke Comparison

**Purpose:** Detailed exploration of text normalization techniques for joke deduplication.

**Status:** Experimental / Research
**Last Updated:** 2025-12-16

---

## Overview

Text normalization is the process of transforming text into a canonical form for comparison. For jokes, this is particularly challenging because:

1. **Punctuation can be critical** - Timing markers like "..." affect delivery
2. **Word order matters** - "Man bites dog" ≠ "Dog bites man"
3. **Numbers have meaning** - "3 guys" vs "300 guys" are different jokes
4. **Unicode variations exist** - Different ways to represent same character
5. **Contractions can be jokes** - "You're" vs "Your" might be the punchline

This document explores normalization strategies with real examples and edge cases.

---

## Unicode Normalization

### Problem: Multiple Representations of Same Character

Unicode allows multiple ways to represent characters, especially with accents:

```python
# é can be represented two ways:
s1 = "café"  # é as single character (U+00E9)
s2 = "café"  # e + combining acute accent (U+0065 + U+0301)

assert s1 == s2  # False! Different bytes
```

### Solution: Unicode Normalization Forms

```python
import unicodedata

def normalize_unicode(text: str, form: str = 'NFC') -> str:
    """Normalize unicode representation.

    Forms:
    - NFC: Canonical composition (preferred for most text)
    - NFD: Canonical decomposition
    - NFKC: Compatibility composition (aggressive)
    - NFKD: Compatibility decomposition
    """
    return unicodedata.normalize(form, text)

# Examples
text = "café"
print(normalize_unicode(text, 'NFC'))   # Single character é
print(normalize_unicode(text, 'NFD'))   # e + combining accent
```

### Recommendation for Jokes

Use **NFC** (Canonical Composition):
- Most compact form
- Matches user expectations
- Compatible with most systems
- Handles accents, diacritics correctly

```python
def normalize_joke_unicode(text: str) -> str:
    """Normalize unicode for joke text."""
    return unicodedata.normalize('NFC', text)
```

---

## Case Normalization

### Options

#### 1. `lower()` - Simple Lowercase
```python
text = "Why Did The CHICKEN Cross The Road?"
print(text.lower())
# "why did the chicken cross the road?"
```

**Issues:**
- Doesn't handle special characters correctly
- Language-specific issues (Turkish: I → ı not i)

#### 2. `casefold()` - Aggressive Case Normalization
```python
text = "GROSS"  # German word for "large"
print(text.lower())     # "gross"
print(text.casefold())  # "gross"

# Better example with ß (German)
text = "Straße"  # "Street" in German
print(text.lower())     # "straße"
print(text.casefold())  # "strasse" (ß → ss)
```

**Benefits:**
- More aggressive matching
- Handles special characters better
- Language-aware transformations

### Recommendation for Jokes

Use **`casefold()`** for English jokes:
```python
def normalize_case(text: str) -> str:
    """Case normalization for jokes."""
    return text.casefold()
```

**Why:**
- Works with unicode
- Better international support (future-proof)
- More robust than `lower()`

---

## Whitespace Normalization

### Common Issues

```python
# Various whitespace problems
texts = [
    "Why  did  the  chicken",           # Multiple spaces
    "Why\tdid\tthe\tchicken",           # Tabs
    "Why\ndid\nthe\nchicken",           # Newlines
    "Why \u00A0 did the chicken",       # Non-breaking space (U+00A0)
    "  Why did the chicken  ",          # Leading/trailing
]
```

### Solution: Regex-Based Normalization

```python
import re

def normalize_whitespace(text: str) -> str:
    """Normalize all whitespace to single spaces."""
    # Replace all whitespace (including tabs, newlines, nbsp) with space
    text = re.sub(r'\s+', ' ', text)

    # Strip leading/trailing
    text = text.strip()

    return text

# Examples
print(normalize_whitespace("Why  did\tthe\nchicken"))
# "Why did the chicken"
```

### Special Case: Newlines in Jokes

Some jokes use newlines for structure:

```python
joke = """Why did the chicken cross the road?

To get to the other side!"""
```

**Decision Points:**
1. **Preserve structure?** Keep newlines between setup/punchline
2. **Flatten all?** Treat as single text blob
3. **Context-aware?** Different normalization for different joke types

### Recommendation for Jokes

**Preserve paragraph breaks, normalize other whitespace:**

```python
def normalize_whitespace_jokes(text: str) -> str:
    """Normalize whitespace while preserving paragraph structure."""
    # Split by double newlines (paragraph breaks)
    paragraphs = re.split(r'\n\s*\n', text)

    # Normalize whitespace within each paragraph
    normalized_paragraphs = []
    for para in paragraphs:
        # Replace all whitespace with single space
        normalized = re.sub(r'\s+', ' ', para)
        normalized = normalized.strip()
        if normalized:  # Skip empty paragraphs
            normalized_paragraphs.append(normalized)

    # Rejoin with single newline
    return '\n'.join(normalized_paragraphs)

# Example
joke = """Why did the chicken  cross\tthe   road?


To get to the other side!"""

print(normalize_whitespace_jokes(joke))
# "Why did the chicken cross the road?\nTo get to the other side!"
```

---

## Punctuation Normalization

### Challenge: Comedy-Critical vs Formatting Punctuation

Some punctuation is critical to jokes:

```python
# Critical punctuation (timing, emphasis)
joke1 = "I'm not saying I'm Batman... but have you ever seen us together?"
joke2 = "I'm not saying I'm Batman but have you ever seen us together"
# ^^^ Different timing, different delivery

# Formatting punctuation (doesn't affect joke)
joke1 = "Why did the chicken cross the road?"
joke2 = "Why did the chicken cross the road"
# ^^^ Same joke, just formatting difference
```

### Categorizing Punctuation

#### Keep (Comedy-Critical)
- `...` (ellipsis) - Timing, suspense
- `!` (exclamation) - Emphasis, surprise
- `—` (em-dash) - Pause, interruption
- `?` (question mark) - Identifies question/answer structure

#### Maybe Keep
- `,` (comma) - Can affect parsing, but often formatting
- `:` (colon) - Introduces lists, but often formatting
- `;` (semicolon) - Rare in jokes
- `"` (quotes) - Can indicate dialogue vs narration

#### Remove (Formatting)
- `.` (period) - Usually just sentence ending
- `'` (apostrophe in contractions) - Keep for word identity
- `-` (hyphen) - Usually just formatting

### Strategies

#### Strategy 1: Remove All Punctuation
```python
import re

def remove_all_punctuation(text: str) -> str:
    """Remove all punctuation."""
    return re.sub(r'[^\w\s]', '', text)

# Example
text = "I'm not saying I'm Batman... but have you ever seen us together?"
print(remove_all_punctuation(text))
# "Im not saying Im Batman but have you ever seen us together"
```

**Pros:** Simple, consistent
**Cons:** Loses critical timing, loses contractions

#### Strategy 2: Keep Critical Punctuation
```python
def normalize_punctuation_preserve_timing(text: str) -> str:
    """Remove formatting punctuation, keep comedy-critical."""
    # Replace ellipsis with placeholder
    text = text.replace('...', ' ELLIPSIS ')
    text = text.replace('…', ' ELLIPSIS ')  # Unicode ellipsis

    # Replace em-dash
    text = text.replace('—', ' EMDASH ')
    text = text.replace('--', ' EMDASH ')

    # Keep exclamation and question marks, but normalize
    text = re.sub(r'!+', '!', text)  # Multiple ! → single !
    text = re.sub(r'\?+', '?', text)  # Multiple ? → single ?

    # Keep apostrophes for contractions
    # Remove other punctuation
    text = re.sub(r"[^\w\s'!?]", ' ', text)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    # Restore timing markers
    text = text.replace('ELLIPSIS', '...')
    text = text.replace('EMDASH', '—')

    return text.strip()

# Example
text = "I'm not saying I'm Batman... but have you ever seen us together???"
print(normalize_punctuation_preserve_timing(text))
# "I'm not saying I'm Batman... but have you ever seen us together?"
```

#### Strategy 3: Contextual (Different for Setup vs Punchline)
```python
from joke_emporium.models.enums import ElementType

def normalize_punctuation_contextual(text: str, element_type: ElementType) -> str:
    """Different normalization based on joke element."""
    if element_type == ElementType.PUNCHLINE:
        # Preserve emphasis in punchlines
        return normalize_punctuation_preserve_timing(text)
    else:
        # More aggressive for setup
        return remove_all_punctuation(text)
```

### Recommendation for Jokes

**Start with Strategy 2 (preserve timing), adjust based on data:**

```python
def normalize_joke_punctuation(text: str) -> str:
    """Normalize punctuation for joke comparison.

    Preserves:
    - ... (ellipsis) for timing
    - ! (exclamation) for emphasis
    - ? (question) for structure
    - ' (apostrophe) for contractions

    Removes:
    - . , ; : " and other formatting marks
    """
    # Normalize ellipsis
    text = text.replace('…', '...')  # Unicode → ASCII
    text = re.sub(r'\.\.\.+', '...', text)  # Multiple . → ...

    # Normalize emphasis
    text = re.sub(r'!+', '!', text)
    text = re.sub(r'\?+', '?', text)

    # Remove other punctuation except apostrophes
    text = re.sub(r"[^\w\s'!?.]+", ' ', text)

    # Clean up spacing
    text = re.sub(r'\s+', ' ', text)

    return text.strip()
```

---

## Number Normalization

### Challenge: When Do Numbers Matter?

```python
# Same joke, different representation
joke1 = "3 guys walk into a bar"
joke2 = "Three guys walk into a bar"
joke3 = "three guys walk into a bar"
# Should all match

# Different jokes
joke1 = "3 guys walk into a bar"
joke2 = "300 guys walk into a bar"
# Should NOT match - different joke
```

### Strategy: Normalize Word-to-Digit

```python
import inflect

def normalize_numbers(text: str) -> str:
    """Normalize number words to digits.

    "three" → "3"
    "twenty-one" → "21"
    """
    p = inflect.engine()

    words = text.split()
    normalized_words = []

    for word in words:
        # Try to parse as number word
        try:
            # inflect can't parse number words, use word2number instead
            from word2number import w2n
            number = w2n.word_to_num(word.lower())
            normalized_words.append(str(number))
        except ValueError:
            # Not a number word
            normalized_words.append(word)

    return ' '.join(normalized_words)

# Example
text = "Three guys walk into a bar"
print(normalize_numbers(text))
# "3 guys walk into a bar"
```

### Simpler Approach: Manual Mapping

```python
NUMBER_WORDS = {
    'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
    'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
    'ten': '10', 'eleven': '11', 'twelve': '12', 'thirteen': '13',
    'fourteen': '14', 'fifteen': '15', 'sixteen': '16', 'seventeen': '17',
    'eighteen': '18', 'nineteen': '19', 'twenty': '20', 'thirty': '30',
    'forty': '40', 'fifty': '50', 'sixty': '60', 'seventy': '70',
    'eighty': '80', 'ninety': '90', 'hundred': '100', 'thousand': '1000',
}

def normalize_numbers_simple(text: str) -> str:
    """Simple number word normalization."""
    text_lower = text.lower()
    for word, digit in NUMBER_WORDS.items():
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + word + r'\b'
        text_lower = re.sub(pattern, digit, text_lower)
    return text_lower

# Example
text = "Three guys walk into a bar. Ten more followed."
print(normalize_numbers_simple(text))
# "3 guys walk into a bar. 10 more followed."
```

### Recommendation for Jokes

**Use simple mapping for common numbers (0-20, tens, hundred, thousand):**

```python
def normalize_joke_numbers(text: str) -> str:
    """Normalize common number words to digits."""
    # Only normalize small numbers (these are most common in jokes)
    number_map = {
        'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
        'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
        'ten': '10', 'eleven': '11', 'twelve': '12',
    }

    text_lower = text.lower()
    for word, digit in number_map.items():
        pattern = r'\b' + word + r'\b'
        text_lower = re.sub(pattern, digit, text_lower, flags=re.IGNORECASE)

    return text_lower
```

**Why limited scope:**
- Most jokes use small numbers
- Complex number words rare in jokes
- Avoids false matches ("won" → "1", "for" → "4")

---

## Contraction Handling

### Challenge: When Contractions Matter

```python
# Usually equivalent
joke1 = "You're going to love this"
joke2 = "You are going to love this"
# Same joke

# Sometimes critical (the joke IS the contraction)
joke1 = "Your gonna love this"  # Incorrect grammar is the joke
joke2 = "You are going to love this"  # Correct grammar
# Different meaning
```

### Strategy: Expand Common Contractions

```python
CONTRACTIONS = {
    "aren't": "are not",
    "can't": "cannot",
    "couldn't": "could not",
    "didn't": "did not",
    "doesn't": "does not",
    "don't": "do not",
    "hadn't": "had not",
    "hasn't": "has not",
    "haven't": "have not",
    "he'd": "he would",
    "he'll": "he will",
    "he's": "he is",
    "i'd": "i would",
    "i'll": "i will",
    "i'm": "i am",
    "i've": "i have",
    "isn't": "is not",
    "it's": "it is",
    "let's": "let us",
    "shouldn't": "should not",
    "that's": "that is",
    "there's": "there is",
    "they'd": "they would",
    "they'll": "they will",
    "they're": "they are",
    "they've": "they have",
    "wasn't": "was not",
    "we'd": "we would",
    "we'll": "we will",
    "we're": "we are",
    "we've": "we have",
    "weren't": "were not",
    "what's": "what is",
    "won't": "will not",
    "wouldn't": "would not",
    "you'd": "you would",
    "you'll": "you will",
    "you're": "you are",
    "you've": "you have",
}

def expand_contractions(text: str) -> str:
    """Expand common English contractions."""
    text_lower = text.lower()
    for contraction, expansion in CONTRACTIONS.items():
        # Word boundary to avoid partial matches
        pattern = r'\b' + re.escape(contraction) + r'\b'
        text_lower = re.sub(pattern, expansion, text_lower)
    return text_lower

# Example
text = "I'm not saying you're wrong, but you can't be right"
print(expand_contractions(text))
# "i am not saying you are wrong, but you cannot be right"
```

### Recommendation for Jokes

**DON'T expand contractions initially:**

Why:
- Contractions are natural in jokes
- Some jokes play on contractions
- Easier to keep than to decide when to expand

```python
def normalize_joke_contractions(text: str) -> str:
    """Keep contractions, just normalize apostrophe style."""
    # Normalize smart quotes to straight apostrophes
    text = text.replace("'", "'")  # U+2019 → U+0027
    text = text.replace("'", "'")  # U+2018 → U+0027
    return text
```

**Future enhancement:** Expand only for fuzzy matching, keep original for exact matching.

---

## Combined Normalization Pipeline

### Putting It All Together

```python
import re
import unicodedata
import hashlib

class JokeNormalizer:
    """Comprehensive joke text normalization."""

    def __init__(self, level: str = 'standard'):
        """Initialize normalizer with level.

        Levels:
        - minimal: Just unicode and case
        - standard: + whitespace, punctuation, numbers (recommended)
        - aggressive: + expand contractions, remove all punctuation
        """
        self.level = level

    def normalize(self, text: str) -> str:
        """Normalize joke text based on level."""
        if self.level == 'minimal':
            return self._normalize_minimal(text)
        elif self.level == 'standard':
            return self._normalize_standard(text)
        elif self.level == 'aggressive':
            return self._normalize_aggressive(text)
        else:
            raise ValueError(f"Unknown level: {self.level}")

    def _normalize_minimal(self, text: str) -> str:
        """Minimal normalization: unicode + case + trim."""
        text = unicodedata.normalize('NFC', text)
        text = text.casefold()
        text = text.strip()
        return text

    def _normalize_standard(self, text: str) -> str:
        """Standard normalization (recommended)."""
        # Unicode normalization
        text = unicodedata.normalize('NFC', text)

        # Case normalization
        text = text.casefold()

        # Normalize apostrophes
        text = text.replace("'", "'").replace("'", "'")

        # Normalize ellipsis
        text = text.replace('…', '...')
        text = re.sub(r'\.\.\.+', '...', text)

        # Normalize emphasis
        text = re.sub(r'!+', '!', text)
        text = re.sub(r'\?+', '?', text)

        # Normalize numbers (simple)
        number_map = {
            'zero': '0', 'one': '1', 'two': '2', 'three': '3',
            'four': '4', 'five': '5', 'six': '6', 'seven': '7',
            'eight': '8', 'nine': '9', 'ten': '10',
        }
        for word, digit in number_map.items():
            text = re.sub(r'\b' + word + r'\b', digit, text)

        # Remove formatting punctuation (keep !, ?, ', ...)
        text = re.sub(r"[^\w\s'!?.]+", ' ', text)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _normalize_aggressive(self, text: str) -> str:
        """Aggressive normalization."""
        # Start with standard
        text = self._normalize_standard(text)

        # Expand contractions
        text = self._expand_contractions(text)

        # Remove ALL punctuation
        text = re.sub(r'[^\w\s]', ' ', text)

        # Normalize whitespace again
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def get_hash(self, text: str) -> str:
        """Get hash of normalized text."""
        normalized = self.normalize(text)
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

# Usage
normalizer = JokeNormalizer(level='standard')

joke1 = "Why did the chicken cross the road?"
joke2 = "Why did the chicken  cross   the   road"
joke3 = "why did the chicken cross the road?"

print(normalizer.normalize(joke1))
print(normalizer.normalize(joke2))
print(normalizer.normalize(joke3))
# All produce: "why did the chicken cross the road?"

# For duplicate detection
hash1 = normalizer.get_hash(joke1)
hash2 = normalizer.get_hash(joke2)
print(hash1 == hash2)  # True - same joke
```

---

## Emoji Handling

### Challenge: Emoji in Jokes

```python
# Emoji as decoration (should match)
joke1 = "I'm not saying I'm old... but my birth certificate is in Roman numerals 😂"
joke2 = "I'm not saying I'm old but my birth certificate is in Roman numerals"
# Same joke, emoji is just decoration

# Emoji as part of joke (should NOT match)
joke1 = "What do you call a sad coffee? Depresso ☕"
joke2 = "What do you call a sad coffee? Depresso 🍕"
# Different emoji = different joke (if emoji is meaningful)
```

### Strategy: Remove Emoji (Start Simple)

```python
import re

def remove_emoji(text: str) -> str:
    """Remove all emoji from text."""
    # Emoji regex pattern
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)

# Example
text = "This joke is fire 🔥🔥🔥"
print(remove_emoji(text))
# "This joke is fire "
```

### Recommendation for Jokes

**Remove emoji for normalization:**

```python
def normalize_emoji(text: str) -> str:
    """Normalize emoji in jokes.

    For now, just remove them. Future: could normalize
    emoji variations (😂 → 🤣 → "haha").
    """
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
    return emoji_pattern.sub(' ', text)
```

---

## Testing & Validation

### Test Suite Structure

```python
# tests/test_normalization.py

import unittest
from joke_emporium.db.normalization import JokeNormalizer

class TestNormalization(unittest.TestCase):
    """Test joke normalization strategies."""

    def setUp(self):
        self.normalizer = JokeNormalizer(level='standard')

    def test_unicode_normalization(self):
        """Test unicode normalization."""
        # Different unicode representations should match
        text1 = "café"  # é as single character
        text2 = "café"  # e + combining accent
        self.assertEqual(
            self.normalizer.normalize(text1),
            self.normalizer.normalize(text2)
        )

    def test_case_normalization(self):
        """Test case normalization."""
        jokes = [
            "Why Did The Chicken Cross The Road?",
            "why did the chicken cross the road?",
            "WHY DID THE CHICKEN CROSS THE ROAD?",
        ]
        normalized = [self.normalizer.normalize(j) for j in jokes]
        self.assertEqual(len(set(normalized)), 1)  # All same

    def test_whitespace_normalization(self):
        """Test whitespace normalization."""
        jokes = [
            "Why  did  the  chicken",
            "Why\tdid\tthe\tchicken",
            "  Why did the chicken  ",
        ]
        normalized = [self.normalizer.normalize(j) for j in jokes]
        self.assertEqual(len(set(normalized)), 1)

    def test_number_normalization(self):
        """Test number word normalization."""
        joke1 = "Three guys walk into a bar"
        joke2 = "3 guys walk into a bar"
        self.assertEqual(
            self.normalizer.normalize(joke1),
            self.normalizer.normalize(joke2)
        )

    def test_different_jokes_dont_match(self):
        """Test that different jokes don't normalize to same text."""
        joke1 = "Why did the chicken cross the road?"
        joke2 = "Why did the turkey cross the road?"
        self.assertNotEqual(
            self.normalizer.normalize(joke1),
            self.normalizer.normalize(joke2)
        )
```

---

## Recommendations Summary

### For Sprint 3 (MVP)

Use **standard normalization level:**

```python
normalizer = JokeNormalizer(level='standard')
normalized = normalizer.normalize(joke_text)
text_hash = normalizer.get_hash(joke_text)
```

**Includes:**
- ✅ Unicode NFC normalization
- ✅ Case folding
- ✅ Whitespace normalization
- ✅ Basic number word normalization (0-10)
- ✅ Punctuation normalization (preserve timing)
- ✅ Emoji removal
- ❌ Contraction expansion (keep contractions)

### Future Enhancements

1. **Adaptive normalization:** Different levels for different similarity checks
2. **Language-aware:** Handle non-English jokes
3. **Structural normalization:** Normalize joke structure separately from text
4. **ML-based:** Learn optimal normalization from labeled duplicates

---

## References

- [Unicode Normalization Forms](https://unicode.org/reports/tr15/)
- [Python unicodedata module](https://docs.python.org/3/library/unicodedata.html)
- [Text Processing Best Practices](https://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html)

---

**Next Steps:**
1. Implement `JokeNormalizer` class in `src/joke_emporium/db/normalization.py`
2. Create comprehensive test suite with real joke examples
3. Measure normalization quality on taivop dataset
4. Adjust strategy based on false positive/negative rates
