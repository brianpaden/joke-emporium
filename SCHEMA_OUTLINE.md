# Joke Dataset Schema Outline

## Design Philosophy

- **Multi-label classification**: Jokes can belong to multiple categories
- **Preserve granularity**: Keep individual ratings, don't just aggregate
- **Balance research & practicality**: Support both academic analysis and everyday use
- **Extensible**: Easy to add new fields without breaking existing data
- **Type-safe**: Pydantic models with strict validation
- **JSON-first**: Primary format is JSON, optimized for both human reading and API consumption

---

## Schema Structure Overview

### File Organization (DECIDED)

**Primary approach**: Single file per major category/variant

```
jokes_dataset/
├── jokes_en_clean.json           # English, family-friendly
├── jokes_en_nsfw.json            # English, adult content
├── jokes_es_clean.json           # Spanish, family-friendly
├── jokes_es_nsfw.json            # Spanish, adult content
├── collections/
│   ├── dad_jokes.json            # References to joke UUIDs
│   ├── tech_humor.json
│   └── ...
└── metadata/
    ├── schema.json               # Schema version & docs
    ├── categories.json           # Category definitions
    └── tags_taxonomy.json        # Tag guidelines
```

Each file contains an array of joke objects. Split by:
- **Language** (en, es, fr, etc.)
- **Maturity** (clean vs nsfw)

---

## Core Models

### 1. Joke (Primary Model)

```yaml
Joke:
  # Identity
  id: UUID (auto-generated, unique identifier)
  version: int (schema version, default: 1)

  # Content (SIMPLIFIED)
  content: list[JokeElement]
    # Each element has:
    # - type: ElementType (setup, punchline, text, build, callback, tag, title)
    # - text: str
    # Examples:
    # - One-liner: [{"type": "text", "text": "..."}]
    # - Q&A: [{"type": "setup", "text": "Why..."}, {"type": "punchline", "text": "Because..."}]
    # - Multi-part: [{"type": "setup", ...}, {"type": "build", ...}, {"type": "punchline", ...}]

  # Classification
  categories: list[Category] (primary topic categories, 1-5 labels)
  tags: list[str] (flexible tagging, unlimited)
  structure: StructureType (narrative form)
  linguistic_mechanisms: list[LinguisticMechanism] (0-3 typical)

  # Ratings & Quality (UPDATED)
  ratings: list[RatingSource]
    # Each rating source contains:
    # - source: str (e.g., "reddit", "https://example.com", "manual_annotation")
    # - total_ratings: int
    # - avg_funniness: float
    # - avg_quality: float | null
    # Can compute weighted averages across all sources

  # Metadata
  metadata: JokeMetadata
    - source: Source
    - author: str | null
    - date_created: datetime | null
    - date_added: datetime (when added to dataset)
    - language: str (ISO 639-1, default: "en")
    - culture_context: str | null (e.g., "US, 2020s")
    - keywords: list[str] (for search)

  # Content Moderation
  maturity: MaturityRating (G, PG, PG13, R, X)
  content_flags: ContentFlags
    - has_profanity: bool
    - is_dark_humor: bool
    - is_offensive: bool
    - is_political: bool
    - is_sexual: bool
    - is_violent: bool
    - toxicity_score: float | null (0.0-1.0)

  # Advanced (Optional - for research)
  gtvh: GTVHAnnotation | null
    - script_opposition: ScriptOpposition | null
    - logical_mechanism: LogicalMechanism | null
    - situation: str | null
    - target: Target | null
    - narrative_strategy: NarrativeStrategy | null
    - language_features: list[LanguageFeature]

  cognitive_type: CognitiveType | null (Chalmers taxonomy)

  # Relationships
  related_jokes: list[UUID] (similar jokes, variations)
  parent_joke: UUID | null (if this is a variant)
  collection_ids: list[str] (which collections include this)
```

---

## Supporting Models

### 2. JokeElement (SIMPLIFIED)

```yaml
JokeElement:
  type: ElementType (setup, punchline, text, build, callback, tag, title)
  text: str

# This unified approach handles all joke types:
# - One-liner: [{"type": "text", "text": "I told my wife..."}]
# - Q&A: [{"type": "setup", "text": "Why?"}, {"type": "punchline", "text": "Because!"}]
# - Multi-part: [{"type": "setup"}, {"type": "build"}, {"type": "punchline"}]
# - With title: [{"type": "title", "text": "..."}, {"type": "text", "text": "..."}]
```

### 3. RatingSource (UPDATED)

```yaml
RatingSource:
  source: str (e.g., "reddit", "https://jokesapi.com", "manual_annotation", "kaggle_dataset")

  # Rating scale information
  min_rating: float (minimum possible rating, default: 1.0)
  max_rating: float (maximum possible rating, default: 5.0)

  # Raw ratings (in original scale)
  total_ratings: int (computed from votes if present, otherwise stored directly)
  avg_funniness: float (in original scale: min_rating to max_rating)
  avg_quality: float | null (in original scale, optional)

  # Normalized ratings (always 1.0-5.0 scale)
  normalized_avg_funniness: float (auto-computed, 1.0-5.0)
  normalized_avg_quality: float | null (auto-computed, 1.0-5.0, optional)

  # Individual votes
  votes: list[Vote] | null (optional - individual votes for granularity)

  # Additional context
  metadata: dict | null (optional extra data, e.g., {"upvotes": 150, "downvotes": 10})

# Normalization formula:
# normalized = 1.0 + (raw - min_rating) * (5.0 - 1.0) / (max_rating - min_rating)
#
# Examples:
# - Reddit: 0-1 scale (upvote ratio) -> normalize to 1-5
# - IMDB: 1-10 scale -> normalize to 1-5
# - Manual: 1-5 scale -> already normalized
# - Binary: 0-1 (liked/not liked) -> normalize to 1-5

# Benefits:
# - Handle any rating scale (binary, 1-10, 0-100, etc.)
# - Preserve original ratings for provenance
# - Always have comparable normalized scores across sources
# - Enable accurate weighted averages
```

### 3a. Vote (Individual Rating)

```yaml
Vote:
  funniness: float (1.0-5.0)
  quality: float | null (1.0-5.0, optional)
  timestamp: datetime

# When votes are stored, total_ratings and avg_* can be computed automatically
# This preserves maximum granularity for:
# - Statistical analysis (variance, distribution)
# - Temporal analysis (ratings over time)
# - Re-computation with different normalization
```

### 4. JokeMetadata

```yaml
JokeMetadata:
  source: Source
    - platform: SourcePlatform (reddit, website, book, api, original, etc.)
    - url: str | null
    - source_id: str | null (e.g., Reddit post ID)
    - retrieved_date: datetime | null

  author: str | null
  comedian: str | null (if from professional)

  date_created: datetime | null
  date_added: datetime (when added to dataset)
  last_modified: datetime (when last updated)

  language: str (ISO 639-1 code, default: "en")
  culture_context: str | null

  keywords: list[str] (searchable terms)

  original_text: str | null (if edited/cleaned)

  # Engagement (if from social media)
  engagement: Engagement | null
    - upvotes: int | null
    - downvotes: int | null
    - comments: int | null
    - shares: int | null
    - awards: int | null
```

### 5. ContentFlags

```yaml
ContentFlags:
  has_profanity: bool (default: false)
  is_dark_humor: bool (default: false)
  is_offensive: bool (default: false)
  is_political: bool (default: false)
  is_sexual: bool (default: false)
  is_violent: bool (default: false)
  is_stereotypical: bool (default: false)

  toxicity_score: float | null (0.0-1.0, from analysis tool)

  notes: str | null (context about flags)
```

### 6. GTVHAnnotation (Advanced - OPTIONAL)

```yaml
GTVHAnnotation:
  script_opposition: ScriptOpposition | null
    - script_a: str
    - script_b: str
    - opposition_type: OppositionType

  logical_mechanism: LogicalMechanism | null

  situation: str | null (description of setting)

  target: Target | null
    - target_type: TargetType (person, group, profession, concept, self)
    - target_name: str | null

  narrative_strategy: NarrativeStrategy (riddle, dialogue, narrative, etc.)

  language_features: list[LanguageFeature]
```

---

## Enumerations

### Category (Primary Topics)

```python
Category (Enum):
  # People & Relationships
  RELATIONSHIPS = "relationships"
  MARRIAGE = "marriage"
  DATING = "dating"
  FAMILY = "family"
  PARENTING = "parenting"
  FRIENDSHIP = "friendship"

  # Professions
  WORK = "work"
  DOCTOR = "doctor"
  LAWYER = "lawyer"
  TEACHER = "teacher"
  ENGINEER = "engineer"
  PROGRAMMER = "programmer"

  # Topics
  TECHNOLOGY = "technology"
  COMPUTERS = "computers"
  SCIENCE = "science"
  MATHEMATICS = "math"
  ANIMALS = "animals"
  FOOD = "food"
  SPORTS = "sports"
  MUSIC = "music"
  POLITICS = "politics"
  RELIGION = "religion"

  # Situations
  TRAVEL = "travel"
  SCHOOL = "school"
  MEDICAL = "medical"
  SHOPPING = "shopping"
  DRIVING = "driving"

  # Meta
  META = "meta"  # Jokes about jokes
  OBSERVATIONAL = "observational"
  ABSURD = "absurd"
  WORDPLAY = "wordplay"

  # Demographics
  KIDS = "kids"
  ELDERLY = "elderly"

  # Miscellaneous
  MISCELLANEOUS = "miscellaneous"
```

### StructureType

```python
StructureType (Enum):
  ONE_LINER = "one_liner"
  QA = "qa"  # Question & answer
  RIDDLE = "riddle"
  STORY = "story"
  DIALOGUE = "dialogue"
  LIST = "list"  # Top 10, etc.
  OBSERVATION = "observation"
  KNOCK_KNOCK = "knock_knock"
  ANTI_JOKE = "anti_joke"
  MISDIRECTION = "misdirection"
  CALLBACK = "callback"  # References earlier setup
```

### LinguisticMechanism

```python
LinguisticMechanism (Enum):
  # Wordplay
  PUN_HOMOPHONIC = "pun_homophonic"  # prophet/profit
  PUN_HOMOGRAPHIC = "pun_homographic"  # read (present) vs read (past)
  PUN_HOMONYMIC = "pun_homonymic"  # bank (river) vs bank (money)
  PUN_COMPOUND = "pun_compound"

  DOUBLE_ENTENDRE = "double_entendre"
  MALAPROPISM = "malapropism"
  SPOONERISM = "spoonerism"

  # Rhetorical
  IRONY = "irony"
  SARCASM = "sarcasm"
  EXAGGERATION = "exaggeration"
  UNDERSTATEMENT = "understatement"
  HYPERBOLE = "hyperbole"

  # Logic
  PARAPROSDOKIAN = "paraprosdokian"  # Unexpected ending
  NON_SEQUITUR = "non_sequitur"
  ABSURDISM = "absurdism"
  REVERSAL = "reversal"

  # Reference
  ALLUSION = "allusion"
  PARODY = "parody"

  # Sound
  ALLITERATION = "alliteration"
  RHYME = "rhyme"

  # Other
  ANTHROPOMORPHISM = "anthropomorphism"
  JUXTAPOSITION = "juxtaposition"
```

### MaturityRating

```python
MaturityRating (Enum):
  G = "g"           # General - all ages
  PG = "pg"         # Parental guidance - may reference adult themes mildly
  PG13 = "pg13"     # Parents strongly cautioned - mild profanity, innuendo
  R = "r"           # Restricted - strong profanity, explicit themes
  X = "x"           # Adults only - extremely explicit
```

### ElementType (SIMPLIFIED - replaces ContentType and PartRole)

```python
ElementType (Enum):
  TITLE = "title"          # Optional title
  TEXT = "text"            # Generic text (for one-liners, stories)
  SETUP = "setup"          # Question, premise
  BUILD = "build"          # Additional setup/context
  PUNCHLINE = "punchline"  # The payoff
  CALLBACK = "callback"    # References earlier setup
  TAG = "tag"              # Additional punchline/kicker
```

### CognitiveType (Chalmers Taxonomy)

```python
CognitiveType (Enum):
  # Main types
  ALLUSIVE = "allusive"
  PARADOXICAL = "paradoxical"
  INFERENTIAL = "inferential"

  # Interpretational subtypes
  INTERPRETATIONAL_SDS = "interpretational_sds"
  INTERPRETATIONAL_DSS = "interpretational_dss"
  INTERPRETATIONAL_SDD = "interpretational_sdd"
  INTERPRETATIONAL_SD = "interpretational_sd"
  INTERPRETATIONAL_DS = "interpretational_ds"
```

### SourcePlatform

```python
SourcePlatform (Enum):
  REDDIT = "reddit"
  TWITTER = "twitter"
  WEBSITE = "website"
  BOOK = "book"
  API = "api"
  ORIGINAL = "original"
  MANUAL_ENTRY = "manual_entry"
  SCRAPED = "scraped"
  CROWDSOURCED = "crowdsourced"
  COMEDY_SPECIAL = "comedy_special"
  UNKNOWN = "unknown"
```

### OppositionType (GTVH)

```python
OppositionType (Enum):
  ACTUAL_NON_ACTUAL = "actual_non_actual"
  NORMAL_ABNORMAL = "normal_abnormal"
  POSSIBLE_IMPOSSIBLE = "possible_impossible"
  GOOD_BAD = "good_bad"
  LIFE_DEATH = "life_death"
  OBSCENE_NON_OBSCENE = "obscene_non_obscene"
  MONEY_NO_MONEY = "money_no_money"
  HIGH_LOW_STATURE = "high_low_stature"
  EXPECTED_UNEXPECTED = "expected_unexpected"
```

### LogicalMechanism (GTVH)

```python
LogicalMechanism (Enum):
  FIGURE_GROUND_REVERSAL = "figure_ground_reversal"
  FALSE_ANALOGY = "false_analogy"
  ROLE_REVERSAL = "role_reversal"
  IGNORANCE_OF_OBVIOUS = "ignorance_of_obvious"
  JUXTAPOSITION = "juxtaposition"
  CHIASMUS = "chiasmus"
  EXAGGERATION = "exaggeration"
  GARDEN_PATH = "garden_path"
```

### NarrativeStrategy (GTVH)

```python
NarrativeStrategy (Enum):
  SIMPLE_NARRATIVE = "simple_narrative"
  DIALOGUE = "dialogue"
  RIDDLE = "riddle"
  BEFORE_AFTER = "before_after"
  META_HUMOR = "meta_humor"
  FRAME_STORY = "frame_story"
```

### TargetType

```python
TargetType (Enum):
  SELF = "self"
  PERSON = "person"
  PROFESSION = "profession"
  GROUP_NATIONALITY = "group_nationality"
  GROUP_GENDER = "group_gender"
  GROUP_AGE = "group_age"
  GROUP_RELIGION = "group_religion"
  GROUP_POLITICAL = "group_political"
  CONCEPT = "concept"
  INSTITUTION = "institution"
  UNIVERSAL = "universal"  # No specific target
```

### AgeRange

```python
AgeRange (Enum):
  UNDER_18 = "under_18"
  AGE_18_24 = "18_24"
  AGE_25_34 = "25_34"
  AGE_35_44 = "35_44"
  AGE_45_54 = "45_54"
  AGE_55_64 = "55_64"
  AGE_65_PLUS = "65_plus"
```

---

## Collections

### Collection Model

```yaml
Collection:
  id: str (unique identifier, slug format)
  name: str
  description: str
  tags: list[str]
  joke_ids: list[UUID]
  created_date: datetime
  last_modified: datetime
  curator: str | null
  is_public: bool
```

---

## Index File Structure

The `index.json` provides quick access without loading all jokes:

```json
{
  "version": "1.0.0",
  "total_jokes": 10000,
  "last_updated": "2024-01-15T10:30:00Z",
  "statistics": {
    "by_category": {
      "technology": 450,
      "animals": 320,
      ...
    },
    "by_maturity": {
      "g": 3000,
      "pg": 4000,
      ...
    },
    "by_structure": {
      "one_liner": 5000,
      "qa": 3000,
      ...
    },
    "avg_funniness": 3.2,
    "total_ratings": 50000
  },
  "jokes": [
    {
      "id": "uuid-here",
      "preview": "First 100 chars of joke...",
      "categories": ["technology", "work"],
      "maturity": "g",
      "avg_funniness": 4.2,
      "file_path": "jokes/uuid-here.json"
    },
    ...
  ]
}
```

---

## Validation Rules

### Required Fields (Minimum Viable Joke)
- `id` (auto-generated UUID)
- `version` (default: 1)
- `content` (list with at least 1 JokeElement)
- At least 1 `categories` entry
- `maturity` rating
- `metadata.date_added`
- `metadata.language`

### Optional But Recommended
- `tags` (improves searchability)
- `structure` (helps with filtering)
- At least 1 funniness rating
- `metadata.source`

### Validation Constraints
- `content`: min 1 element, each element max 2000 characters
- `categories`: min 1, max 5
- `tags`: max 20
- `linguistic_mechanisms`: max 3 (0 is fine for simple jokes)
- `funniness_scores[].score`: 1-5 inclusive
- `maturity`: required, must be valid enum value
- `language`: must be valid ISO 639-1 code (en, es, fr, etc.)

---

## Example JSON Structure

### Minimal Joke (UPDATED)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "version": 1,
  "content": [
    {
      "type": "setup",
      "text": "Why do programmers prefer dark mode?"
    },
    {
      "type": "punchline",
      "text": "Because light attracts bugs!"
    }
  ],
  "categories": ["programmer", "technology"],
  "tags": ["programming", "dark mode", "bugs", "light"],
  "structure": "qa",
  "linguistic_mechanisms": ["pun_homonymic"],
  "maturity": "g",
  "content_flags": {
    "has_profanity": false,
    "is_dark_humor": false,
    "is_offensive": false,
    "is_political": false,
    "is_sexual": false,
    "is_violent": false
  },
  "ratings": [
    {
      "source": "reddit",
      "min_rating": 0.0,
      "max_rating": 1.0,
      "total_ratings": 45,
      "avg_funniness": 0.933,
      "avg_quality": null,
      "normalized_avg_funniness": 4.73,
      "normalized_avg_quality": null,
      "votes": null,
      "metadata": {
        "upvotes": 42,
        "downvotes": 3,
        "upvote_ratio": 0.933,
        "post_id": "abc123"
      }
    }
  ],
  "metadata": {
    "source": {
      "platform": "reddit",
      "url": "https://reddit.com/r/ProgrammerHumor/example",
      "source_id": "abc123"
    },
    "date_added": "2024-01-15T10:00:00Z",
    "language": "en",
    "keywords": ["programming", "bugs", "IDE"]
  }
}
```

### Full-Featured Joke (UPDATED)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "version": 1,
  "content": [
    {
      "type": "title",
      "text": "The Doctor's Advice"
    },
    {
      "type": "text",
      "text": "A man goes to the doctor and says, 'Doctor, I keep thinking I'm a moth.' The doctor replies, 'Well, you need a psychiatrist, not a doctor.' The man says, 'I know.' The doctor asks, 'So why did you come here?' The man replies, 'Your light was on.'"
    }
  ],
  "categories": ["doctor", "absurd", "animals"],
  "tags": ["psychiatrist", "moth", "light", "classic"],
  "structure": "story",
  "linguistic_mechanisms": ["absurdism", "misdirection"],
  "maturity": "g",
  "content_flags": {
    "has_profanity": false,
    "is_dark_humor": false,
    "is_offensive": false,
    "is_political": false,
    "is_sexual": false,
    "is_violent": false
  },
  "ratings": [
    {
      "source": "manual_annotation",
      "min_rating": 1.0,
      "max_rating": 5.0,
      "total_ratings": 3,
      "avg_funniness": 4.67,
      "avg_quality": 4.5,
      "normalized_avg_funniness": 4.67,
      "normalized_avg_quality": 4.5,
      "votes": [
        {"funniness": 5.0, "quality": 5.0, "timestamp": "2024-01-15T10:00:00Z"},
        {"funniness": 4.0, "quality": 4.0, "timestamp": "2024-01-15T11:00:00Z"},
        {"funniness": 5.0, "quality": 4.5, "timestamp": "2024-01-15T12:00:00Z"}
      ],
      "metadata": {
        "annotation_date": "2024-01-15"
      }
    },
    {
      "source": "reddit",
      "min_rating": 0.0,
      "max_rating": 1.0,
      "total_ratings": 257,
      "avg_funniness": 0.953,
      "avg_quality": null,
      "normalized_avg_funniness": 4.81,
      "normalized_avg_quality": null,
      "votes": null,
      "metadata": {
        "upvotes": 245,
        "downvotes": 12,
        "upvote_ratio": 0.953,
        "post_id": "xyz789"
      }
    }
  ],
  "metadata": {
    "source": {
      "platform": "book",
      "source_id": "1001_jokes_book_p42"
    },
    "author": "Unknown",
    "date_created": null,
    "date_added": "2024-01-15T10:00:00Z",
    "last_modified": "2024-01-15T15:00:00Z",
    "language": "en",
    "culture_context": "English-speaking, general",
    "keywords": ["doctor", "moth", "light", "psychiatrist", "absurd"]
  },
  "gtvh": {
    "script_opposition": {
      "script_a": "seeking medical help",
      "script_b": "moth attracted to light",
      "opposition_type": "normal_abnormal"
    },
    "logical_mechanism": "juxtaposition",
    "situation": "doctor's office visit",
    "target": null,
    "narrative_strategy": "dialogue",
    "language_features": ["literal_interpretation"]
  },
  "cognitive_type": "interpretational_sdd",
  "related_jokes": [],
  "collection_ids": ["classic_jokes", "absurd_humor"]
}
```

---

## File Organization Strategy

### Selected Approach: Single File per Language/Maturity Split

```
data/
  jokes_en_clean.json       # English, G/PG/PG13 jokes
  jokes_en_nsfw.json        # English, R/X jokes
  jokes_es_clean.json       # Spanish, G/PG/PG13 jokes
  jokes_es_nsfw.json        # Spanish, R/X jokes
  collections/
    dad_jokes.json          # Array of UUIDs
    tech_humor.json         # Array of UUIDs
    dark_humor.json         # Array of UUIDs
  metadata/
    schema.json             # Schema version & documentation
    categories.json         # Category definitions & descriptions
    tags_taxonomy.json      # Suggested tags & guidelines
```

**Format within each file:**
```json
[
  {joke object 1},
  {joke object 2},
  ...
]
```

**Collections reference jokes by UUID:**
```json
{
  "id": "dad_jokes",
  "name": "Dad Jokes Collection",
  "description": "Classic groan-worthy dad jokes",
  "joke_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001",
    ...
  ]
}
```

---

## Python Package Structure

```
src/
└── joke_emporium/
    ├── __init__.py
    ├── models/
    │   ├── __init__.py
    │   ├── joke.py              # Main Joke model
    │   ├── author.py            # Author model
    │   ├── content.py           # JokeElement
    │   ├── ratings.py           # RatingSource, Vote
    │   ├── metadata.py          # JokeMetadata, Source, Engagement
    │   ├── flags.py             # ContentFlags
    │   ├── gtvh.py              # GTVHAnnotation (optional/advanced)
    │   ├── collection.py        # Collection model
    │   └── enums.py             # All enumerations
    ├── validators/
    │   ├── __init__.py
    │   ├── joke_validator.py
    │   └── collection_validator.py
    ├── utils/
    │   ├── __init__.py
    │   ├── id_generator.py
    │   ├── text_analysis.py     # Character/word counting
    │   └── rating_calculator.py # Weighted averages, normalization
    ├── io/
    │   ├── __init__.py
    │   ├── loader.py            # Load jokes from JSON
    │   ├── saver.py             # Save jokes to JSON
    │   └── index_builder.py     # Build index/statistics
    └── tools/
        ├── __init__.py
        ├── scraper.py           # Scraping utilities
        ├── annotator.py         # Annotation tool
        └── validator_cli.py     # CLI for validation
```

---

## Next Steps

1. **Review & Approve Schema**: Confirm this structure meets requirements
2. **Create Pydantic Models**: Implement the schema in Python
3. **Build Validators**: Ensure data integrity
4. **Create Sample Data**: 10-20 example jokes covering all types
5. **Build Tools**: JSON loader, validator, rating calculator
6. **Documentation**: Usage guide, annotation guidelines
7. **Testing**: Unit tests for models and validators

---

## Design Decisions (RESOLVED)

1. ✅ **File Structure**: Single file per language/maturity combination
2. ✅ **Content Schema**: Simplified to list of JokeElement (type + text)
3. ✅ **Ratings Schema**: RatingSource with optional Vote list for granularity
4. ✅ **Rating Normalization**: Store original scale (min/max) + normalized 1-5 scores
5. ✅ **GTVH Fields**: Optional, for research use cases
6. ✅ **Multi-language**: Separate files by language, link via UUID for translations
7. ✅ **Duplicate Detection**: Will implement in scraping/util tools later
8. ✅ **Annotator IDs**: Not needed in data model (can track in annotation tooling if needed)

## Open Questions (Still To Decide)

1. **Versioning**: How to handle schema evolution? (version field per joke is a start)
2. **API Considerations**: Any fields needed for API serving?
3. **Search Optimization**: Additional fields for Elasticsearch/similar?
4. **Licensing**: Include license field per joke or dataset-wide?
5. **Computed fields**: Should we store character_count, word_count in the JSON or compute on-the-fly?
   - *Suggestion*: Compute on-the-fly via Pydantic computed fields - keeps data lean

## Rating Source Examples

### Reddit Post (0-1 upvote ratio scale)
```json
{
  "source": "reddit",
  "min_rating": 0.0,
  "max_rating": 1.0,
  "total_ratings": 1335,
  "avg_funniness": 0.936,
  "avg_quality": null,
  "normalized_avg_funniness": 4.74,
  "normalized_avg_quality": null,
  "votes": null,
  "metadata": {
    "upvotes": 1250,
    "downvotes": 85,
    "upvote_ratio": 0.936,
    "subreddit": "r/ProgrammerHumor",
    "post_id": "xyz123"
  }
}
```

### Manual Annotation Session (1-5 scale, with individual votes)
```json
{
  "source": "manual_annotation",
  "min_rating": 1.0,
  "max_rating": 5.0,
  "total_ratings": 5,
  "avg_funniness": 3.8,
  "avg_quality": 4.0,
  "normalized_avg_funniness": 3.8,
  "normalized_avg_quality": 4.0,
  "votes": [
    {"funniness": 4.0, "quality": 4.0, "timestamp": "2024-01-15T10:00:00Z"},
    {"funniness": 3.0, "quality": 4.0, "timestamp": "2024-01-15T10:05:00Z"},
    {"funniness": 4.0, "quality": 5.0, "timestamp": "2024-01-15T10:10:00Z"},
    {"funniness": 4.0, "quality": 4.0, "timestamp": "2024-01-15T10:15:00Z"},
    {"funniness": 4.0, "quality": 3.0, "timestamp": "2024-01-15T10:20:00Z"}
  ],
  "metadata": {
    "session_id": "session_2024_01_15"
  }
}
```

### IMDB-style Rating (1-10 scale)
```json
{
  "source": "https://jokes.imdb-style-site.com",
  "min_rating": 1.0,
  "max_rating": 10.0,
  "total_ratings": 847,
  "avg_funniness": 7.8,
  "avg_quality": null,
  "normalized_avg_funniness": 4.02,
  "normalized_avg_quality": null,
  "votes": null,
  "metadata": {
    "joke_id": "12345",
    "fetched_date": "2024-01-15"
  }
}
```

### External API/Dataset
```json
{
  "source": "https://api.icanhazdadjoke.com",
  "total_ratings": 42,
  "avg_funniness": 3.2,
  "avg_quality": null,
  "metadata": {
    "api_joke_id": "R7UfaahVfFd",
    "fetched_date": "2024-01-15"
  }
}
```

### Kaggle Dataset (custom 0-10 scale)
```json
{
  "source": "kaggle_short_jokes_dataset",
  "min_rating": 0.0,
  "max_rating": 10.0,
  "total_ratings": 1,
  "avg_funniness": 7.0,
  "avg_quality": null,
  "normalized_avg_funniness": 3.8,
  "normalized_avg_quality": null,
  "votes": null,
  "metadata": {
    "original_score": 7,
    "dataset_version": "v2.1"
  }
}
```

### Binary Like/Dislike (0-1 scale)
```json
{
  "source": "https://jokes.binary-site.com",
  "min_rating": 0.0,
  "max_rating": 1.0,
  "total_ratings": 450,
  "avg_funniness": 0.78,
  "avg_quality": null,
  "normalized_avg_funniness": 4.12,
  "normalized_avg_quality": null,
  "votes": null,
  "metadata": {
    "likes": 351,
    "dislikes": 99,
    "like_ratio": 0.78
  }
}
```

## Normalization and Weighted Averages

### Normalization Formula

To convert any rating scale to the standard 1-5 scale:

```python
def normalize_rating(raw_score: float, min_rating: float, max_rating: float) -> float:
    """
    Normalize a rating from any scale to 1-5 scale.

    Formula: 1.0 + (raw - min) * (5.0 - 1.0) / (max - min)

    Examples:
    - Reddit upvote ratio 0.936 (0-1) -> 4.74 (1-5)
    - IMDB score 7.8 (1-10) -> 4.02 (1-5)
    - Manual rating 4.0 (1-5) -> 4.0 (1-5) [no change]
    - Binary like 0.78 (0-1) -> 4.12 (1-5)
    """
    if max_rating == min_rating:
        return 3.0  # Default to middle if scale is invalid

    return 1.0 + (raw_score - min_rating) * (5.0 - 1.0) / (max_rating - min_rating)


def denormalize_rating(normalized: float, min_rating: float, max_rating: float) -> float:
    """Convert from 1-5 scale back to original scale."""
    return min_rating + (normalized - 1.0) * (max_rating - min_rating) / (5.0 - 1.0)
```

### Computing Weighted Averages

Always use **normalized** scores for weighted averages:

```python
def compute_weighted_funniness(joke: Joke) -> float:
    """
    Compute weighted average funniness across all sources.

    IMPORTANT: Uses normalized_avg_funniness to ensure fair comparison
    across different rating scales.

    Weight strategies could include:
    - Equal weight: all sources treated the same
    - By total_ratings: sources with more ratings weighted higher
    - By source type: manual > reddit > automated
    - By recency: newer ratings weighted higher
    """
    if not joke.ratings:
        return None

    # Use NORMALIZED scores for accurate weighted average
    total_weight = sum(r.total_ratings for r in joke.ratings)
    weighted_sum = sum(r.normalized_avg_funniness * r.total_ratings for r in joke.ratings)
    return weighted_sum / total_weight if total_weight > 0 else None

def compute_statistics(rating_source: RatingSource) -> dict:
    """
    Compute statistics from individual votes if available.

    Returns median, variance, std deviation, etc.
    Useful when votes are stored for detailed analysis.
    """
    if not rating_source.votes:
        return None

    funniness_scores = [v.funniness for v in rating_source.votes]
    return {
        "median": statistics.median(funniness_scores),
        "variance": statistics.variance(funniness_scores) if len(funniness_scores) > 1 else 0,
        "std_dev": statistics.stdev(funniness_scores) if len(funniness_scores) > 1 else 0,
        "min": min(funniness_scores),
        "max": max(funniness_scores),
    }
```

---

## Design Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Primary Format** | JSON | Human-readable, widely supported, easy to version control |
| **ID Strategy** | UUID | Globally unique, no collisions, portable |
| **Rating Approach** | Individual scores preserved | Research best practice, enables analysis |
| **Categorization** | Multi-label | Jokes fit multiple categories |
| **Schema Version** | Included in each joke | Enables migration, handles evolution |
| **Computed Fields** | Included in model | Easier querying, can recompute if needed |
| **Validation** | Pydantic | Type safety, great dev experience, automatic docs |
| **Extensibility** | Optional fields + version number | Can add features without breaking old data |
| **Research Fields** | Optional but structured | Supports academic use without complexity for casual use |
