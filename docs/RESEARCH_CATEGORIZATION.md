# Scientific Research on Joke Categorization and Classification

## Overview

This document compiles academic research on joke categorization, taxonomies, annotation schemas, and classification frameworks to inform the design of our joke dataset.

---

## 1. Major Humor Theories

### Three Foundational Theories

1. **Humor as Release** - Psychological tension and its relief
2. **Humor as Aggression** - Superiority and targeting
3. **Humor as Incongruity** - The most predominant in current research

**Key Insight**: These theories are complementary and describe different aspects of humor. Most modern computational approaches focus on incongruity theory.

---

## 2. General Theory of Verbal Humor (GTVH)

### Six Knowledge Resources (KRs)

The GTVH (Attardo & Raskin, 1991) proposes six dimensions for analyzing and classifying jokes:

| Knowledge Resource | Abbreviation | Description |
|-------------------|--------------|-------------|
| **Script Opposition** | SO | The semantic scripts being contrasted (from SSTH) |
| **Logical Mechanism** | LM | How the incongruity is resolved |
| **Situation** | SI | The setting/context of the joke |
| **Target** | TA | The entity being made fun of (person, group, concept) |
| **Narrative Strategy** | NS | How the text is organized (riddle, dialogue, narrative) |
| **Language** | LA | Linguistic features (phonemic, morphemic, syntactic) |

### Applications for Dataset Design

- **Joke Similarity Metrics**: GTVH enables measuring how similar jokes are by comparing KRs
- **Multi-dimensional Classification**: Jokes can be tagged along all six dimensions
- **Translation & Adaptation**: Useful for understanding joke variants

### Script Opposition Types

Common oppositions include:
- Actual vs. Non-actual
- Normal vs. Abnormal
- Possible vs. Impossible
- Good vs. Bad
- Life vs. Death
- Obscene vs. Non-obscene
- Money vs. No-money
- High vs. Low stature

---

## 3. Cognitive Joke Taxonomy (Chalmers)

### Four Primary Classes

1. **Allusive** - Recognition of common human experiences
2. **Interpretational** - Multiple valid interpretations (largest category)
3. **Paradoxical** - Self-defeating statements and contradictions
4. **Inferential** - Requiring mental inference to reach conclusions

### Interpretational Subtypes

The interpretational category divides into five types based on Situation (S) and Description (D) relationships:

| Type | Structure | Mechanism | Examples |
|------|-----------|-----------|----------|
| **SDS** | Situation → Description → Situation | False analogy; unexpected implementation | Copycat jokes, lion-tamer joke |
| **DSS** | Description → Two Situations | Surprising vs. expected outcomes | Light bulb jokes, "How many X to..." |
| **SDD** | Situation → Two Descriptions | Mistaken or facetious reinterpretation | "Is the doctor home?" jokes |
| **SD** | Situation → Description | Weird but fitting explanation | Superman at Empire State Building |
| **DS** | Description → Situation | Difficult description satisfied unexpectedly | Riddles |

### Key Distinguishing Features

- **Reversal relations** vs. **parallel slippage** vs. **neither**
- **Goal-directed** vs. **quirk-of-fate** outcomes
- **Inference difficulty** level

---

## 4. Linguistic Analysis Dimensions

### Phonological Jokes

- **Homophones**: Same sound, different meaning/spelling
- **Alliteration**: Repetition of sounds
- **Phonological ambiguity**: Exploiting sound similarities between languages

### Semantic Categories

Based on lexical ambiguity:
- **Homophonic puns**: Sound alike (prophet/profit)
- **Homographic puns**: Spelled alike, different meanings/sounds
- **Homonymic puns**: Identical spelling AND sound
- **Compound puns**: Multiple puns combined
- **Paronyms**: Similar sounding words

### Structural Features

From Script-Based Semantic Theory (SSTH):
- **Script overlap**: Two semantic scripts that can apply to the same text
- **Ambiguity types**: Lexical, structural, pragmatic
- **Resolution patterns**: How the incongruity is resolved

---

## 5. Computational Humor Classification

### Key Components (from Systematic Literature Review)

Three essential components for computational humor:
1. **Datasets**: Humorous and non-humorous instances
2. **Features**: Measurable representations
3. **Algorithms**: Classification methods

### Feature Categories for ML

Common features used in computational humor detection:

**Content Features:**
- Word embeddings
- N-grams
- TF-IDF scores
- Sentiment polarity
- Incongruity markers

**Structural Features:**
- Setup/punchline structure
- Sentence length
- Readability scores
- Syntactic complexity

**Contextual Features:**
- Target identification
- Topic modeling
- Cultural references
- Temporal context

### Fine-Grained Categorization

Research suggests humor has different manifestations:
- Irony
- Sarcasm
- Creativity
- Insult
- Wordplay
- Dark humor
- Observational

---

## 6. Annotation Schemas from Real Datasets

### HAHA (Humor Analysis based on Human Annotation)

**Binary Classification:**
- Humorous vs. Non-humorous

**Funniness Rating:**
- Scale: 1 (not funny) to 5 (excellent)
- Voting scheme with multiple annotators

**Content Classification:**
- Racist jokes
- Sexist jokes
- Dark humor
- Dirty jokes
- Political humor
- Celebrity humor
- Sports humor

### CleanComedy Dataset (2024)

**Annotation Approach:**
- Each joke rated by 5 different annotators
- Scale: 1-5 (funniness)
- Individual scores preserved (not aggregated)
- Collected via crowdsourcing (Telegram bot)
- Toxicity filtering applied

**Categories:**
- Clean jokes
- Dark jokes
- Dirty jokes

### Chinese Humor Corpus

**Multi-dimensional Labeling:**
1. **Funniness**: Five levels
2. **Skill Sets**: Eight types of humor techniques
3. **Intent**: Six dimensions of purpose

### Humor Genome Framework

**Annotation Dimensions:**
- **Humor type**: Specific comedic devices
- **Structure**: Setup → punch pattern
- **Devices**: Irony, misdirection, call-back, etc.
- **Format**: Stand-up, sketch, one-liner, etc.
- **Tone**: Sarcastic, absurd, dark, wholesome
- **Social context**: Cultural references, current events
- **Audience reaction**: Timing and intensity

---

## 7. Practical Categorization Dimensions

### By Structure
- One-liner
- Setup/punchline (Q&A, riddle)
- Story/narrative
- Dialogue
- List
- Observational

### By Linguistic Mechanism
- Pun (homophonic, homographic, homonymic)
- Wordplay
- Malapropism
- Spoonerism
- Double entendre
- Irony/sarcasm
- Exaggeration/hyperbole
- Understatement
- Absurdism

### By Content/Topic
- Animals
- Technology/computers
- Relationships/marriage
- Work/office
- Food/drink
- Sports
- Politics
- Science
- Medical/doctor
- Lawyer
- Religion
- School/education
- Regional/nationality

### By Target (GTVH-TA)
- Self-deprecating
- Profession-targeted
- Group-targeted (nationality, gender, etc.)
- Situation-targeted
- Universal/no specific target

### By Maturity/Appropriateness
- G (General audiences)
- PG (Parental guidance)
- PG-13 (Teen appropriate)
- R (Adult)
- Dark/offensive
- Clean/family-friendly

### By Cognitive Demand
- Surface-level (physical comedy, simple puns)
- Medium (cultural references, wordplay)
- High (complex logic, obscure references)

### By Social Function
- Icebreaker
- Self-deprecating
- Bonding/in-group
- Teasing/playful
- Satirical/critical

---

## 8. Metadata Dimensions

Beyond categorization, consider tracking:

### Quality Metrics
- User ratings (1-5 scale)
- Vote count
- Upvote/downvote ratio
- Annotator agreement level

### Source Information
- Origin (Reddit, website, book, etc.)
- Author/comedian
- Date posted/published
- Cultural context
- Language/translation

### Engagement Metrics
- Comments/replies
- Shares
- Awards received
- View count

### Processing Metadata
- Toxicity score
- Sentiment polarity
- Reading level
- Character/word count
- Has profanity (boolean)

---

## 9. Recommended Multi-Label Approach

Based on research, jokes should support **multi-label classification**:

### Core Labels (Required)
1. **Primary Category** (topic/theme)
2. **Structure Type** (one-liner, Q&A, story, etc.)
3. **Maturity Rating** (G, PG, PG-13, R)

### Optional Labels
4. **Linguistic Mechanism** (pun, wordplay, irony, etc.)
5. **Target** (if applicable)
6. **Cognitive Type** (from Chalmers taxonomy)
7. **GTVH Dimensions** (for research/advanced filtering)
8. **Content Warnings** (dark, offensive, sexual, etc.)

### Ratings
- **Funniness**: 1-5 scale (multiple annotators)
- **Quality**: Aggregate score

---

## 10. Implementation Recommendations

### For Pydantic Models

```
Joke
├── content (text)
├── structure (enum: one_liner, qa, story, etc.)
├── categories (list[CategoryEnum])
├── linguistic_mechanisms (list[MechanismEnum])
├── maturity_rating (enum: G, PG, PG13, R)
├── target (optional)
├── tags (list[str]) - flexible tagging
├── ratings
│   ├── funniness_scores (list[int])
│   ├── avg_funniness (float)
│   └── quality_score (float)
├── metadata
│   ├── source
│   ├── author
│   ├── date
│   ├── language
│   └── cultural_context
└── flags
    ├── has_profanity
    ├── is_offensive
    └── toxicity_score
```

### Annotation Guidelines

1. **Multiple annotators**: Minimum 3-5 per joke
2. **Inter-annotator agreement**: Calculate and report
3. **Preserve individual scores**: Don't aggregate immediately
4. **Clear definitions**: Document what each category means
5. **Examples**: Provide prototypical examples for each category
6. **Edge cases**: Document how to handle ambiguous jokes

---

## References

### Academic Papers & Books
- Attardo, S., & Raskin, V. (1991). Script theory revis(it)ed: Joke similarity and joke representation model. Humor, 4(3-4), 293-347.
- Chalmers, D. (n.d.). A Taxonomy of Cognitive Jokes. [Link](https://consc.net/notes/humor.html)
- Ritchie, G. D. (2004). The Linguistic Analysis of Jokes. Routledge.
- Various LREC, EMNLP, ACL papers on computational humor (2019-2024)

### Datasets & Corpora
- HAHA corpus (Spanish, 2021)
- CleanComedy (English/Russian, 2024)
- r/Jokes dataset (550k+ jokes)
- Chinese Humor Corpus (3,365 jokes)

### Frameworks
- General Theory of Verbal Humor (GTVH)
- Script-based Semantic Theory of Humor (SSTH)
- Humor Genome Framework
- Incongruity-Resolution Theory

---

## Key Takeaways for Our Dataset

1. **Use multi-dimensional classification** - Jokes are complex and fit multiple categories
2. **Preserve granularity** - Keep individual ratings, don't just aggregate
3. **Balance theory and practice** - Academic frameworks (GTVH) + practical tags (dad joke, pun)
4. **Plan for subjectivity** - Humor is subjective; capture multiple perspectives
5. **Enable filtering** - Design schema to support various filtering needs
6. **Document thoroughly** - Clear guidelines for annotators and users
7. **Start simple, expand** - Begin with core categories, add advanced features iteratively
8. **Consider cultural context** - Some jokes are culture/time-specific
9. **Track quality** - Not all jokes are equally funny or well-constructed
10. **Support research** - Include fields that enable computational humor research

---

## Next Steps

1. Design Pydantic models based on this research
2. Create enums for categories, structures, mechanisms
3. Define validation rules
4. Establish annotation guidelines
5. Build tools for dataset creation and validation
6. Plan for inter-annotator agreement measurement
