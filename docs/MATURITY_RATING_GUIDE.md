# Maturity Rating Guide

**Purpose:** Guidelines for assigning maturity ratings and content flags to jokes in the Joke Emporium dataset.

**Last Updated:** 2025-12-17

---

## Overview

The Joke Emporium uses a maturity rating system similar to MPAA film ratings to classify jokes by appropriate audience. This guide provides standardized definitions and examples to ensure consistent rating across the dataset.

## Rating Levels

### G (General Audiences - All Ages)

**Definition:** Content appropriate for all ages with no elements requiring parental guidance.

**Allowed Content:**
- Clean humor without profanity
- Wordplay, puns, riddles
- Observational humor
- Kid-friendly topics

**Examples:**
- "Why did the scarecrow win an award? Because he was outstanding in his field!"
- "What do you call a bear with no teeth? A gummy bear!"

**Not Allowed:**
- Any profanity (even mild)
- Sexual references or innuendo
- Violence or dark themes
- Religious or political satire

---

### PG (Parental Guidance Suggested)

**Definition:** May reference adult themes mildly. Some material may not be suitable for young children.

**Allowed Content:**
- Mild profanity: "damn", "hell", "crap", "ass" (infrequent)
- Mild adult themes (work, dating, relationships)
- Gentle satire
- Brief references to alcohol (not abuse)

**Examples:**
- Jokes about work frustrations with mild language
- Dating humor without sexual content
- Marriage jokes (non-explicit)

**Content Flags:**
- May set `profanity: true` if mild language present
- May set `requires_context: true` for cultural references

**Thresholds:**
- 1-2 instances of mild profanity
- No sexual references
- No violence or dark themes

---

### PG-13 (Parents Strongly Cautioned)

**Definition:** Some material may be inappropriate for children under 13. More intense themes or language than PG.

**Allowed Content:**
- Moderate profanity: "shit", "bitch", "dick" (limited use)
- One use of strong profanity acceptable (e.g., single "f-word")
- Sexual innuendo and double entendres
- References to drugs/alcohol (not glorifying abuse)
- Mild violence (not graphic)

**Examples:**
- Jokes with sexual innuendo or "that's what she said" format
- Bar jokes with moderate language
- Political/religious satire (not offensive)

**Content Flags:**
- `profanity: true` for moderate language
- `sexual: true` for innuendo
- `political: true` or `religious: true` as appropriate

**Thresholds (based on MPAA guidelines):**
- 1-3 instances of moderate profanity
- Single use of strong profanity (f-word) acceptable
- Multiple uses of strong profanity → R rating
- Sexual innuendo without explicit terminology

---

### R (Restricted - Mature Audiences)

**Definition:** Contains adult content including strong profanity, explicit themes, or intense violence. Not appropriate for children.

**Allowed Content:**
- Strong profanity: "fuck", "motherfucker", "cunt" (multiple uses)
- Sexually-oriented content (not pornographic)
- Adult themes: drug use, excessive drinking
- Intense violence or dark humor
- Offensive stereotypes (when part of satire)

**Examples:**
- Jokes with multiple strong expletives
- Sexual situations (not graphic pornography)
- Dark humor about death, tragedy
- Edgy political/religious content

**Content Flags:**
- `profanity: true` (strong language)
- `sexual: true` for sexual content
- `dark_humor: true` for morbid themes
- `offensive: true` for potentially offensive content
- `stereotypical: true` if using stereotypes

**Thresholds:**
- 2+ uses of strong profanity (f-word)
- Explicit sexual terminology (not pornographic)
- Graphic violence descriptions
- Intense dark humor

---

### X (Adults Only - Extremely Explicit)

**Definition:** Extremely explicit sexual content, extreme violence, or content that would be off-limits for viewing by children.

**Allowed Content:**
- Pornographic or sexually explicit content
- Extremely graphic violence
- Aberrational behavior
- Content most parents would consider too strong for children

**Examples:**
- Jokes with graphic sexual descriptions
- Extreme violence or gore
- Highly offensive content

**Content Flags:**
- `sexual: true` (explicit)
- `violent: true` (extreme)
- `offensive: true` (likely)
- Multiple flags often set

**Note:** This rating is rare in the joke dataset. Most "adult" jokes fall into R category.

---

## Content Flags

In addition to maturity ratings, jokes can have content flags to help with filtering and warnings:

### Profanity Flag
**When to set:** Joke contains any profane language (mild to extreme)

**Severity indicated by rating:**
- PG: Mild profanity (damn, hell, crap)
- PG-13: Moderate profanity (shit, bitch)
- R/X: Strong profanity (fuck, cunt)

### Sexual Flag
**When to set:** Joke contains sexual content or innuendo

**Examples:**
- Double entendres with sexual meaning
- References to sex, sexual acts, or body parts in sexual context
- Adult-oriented sexual humor

### Dark Humor Flag
**When to set:** Joke involves death, tragedy, or morbid themes

**Examples:**
- Death jokes, gallows humor
- Jokes about terminal illness, suicide
- Tragedy-based humor

### Offensive Flag
**When to set:** Joke may offend some audiences beyond just profanity

**Examples:**
- Potentially insensitive topics (disability, tragedy)
- Controversial subject matter
- Content that pushes boundaries

### Stereotypical Flag
**When to set:** Joke relies on stereotypes

**Examples:**
- Blonde jokes
- Ethnic/racial stereotypes
- Gender stereotypes
- Professional stereotypes (lawyer jokes, etc.)

**Note:** Not all stereotype-based jokes are offensive. Context matters.

### Political / Religious Flags
**When to set:** Joke contains political or religious content/satire

**Purpose:** Allow users to filter political/religious content if desired

### Violent Flag
**When to set:** Joke contains violent content or graphic descriptions

### Requires Context Flag
**When to set:** Joke requires specific cultural, historical, or contextual knowledge

**Examples:**
- Pop culture references
- Historical events
- Language-specific wordplay

---

## Rating Decision Process

When rating a joke, evaluate in this order:

### 1. Profanity Check
- Scan for profane words
- Categorize severity (mild, moderate, strong)
- Count instances

### 2. Sexual Content Check
- Look for sexual terms
- Identify innuendo patterns
- Assess explicitness level

### 3. Dark/Violent Content Check
- Check for death, violence themes
- Assess intensity

### 4. Other Factors
- Stereotypes
- Political/religious content
- Offensive potential

### 5. Assign Rating
Use the **highest severity** factor:
- Any strong profanity (2+ uses) → R minimum
- Explicit sexual content → R or X
- Extreme violence → R or X
- Otherwise use profanity/innuendo levels to determine G/PG/PG-13

### 6. Set Content Flags
Flag all applicable content types regardless of rating.

---

## Standardized References

Our rating system is based on established standards:

### MPAA Film Rating System

Official film industry standards used in the United States:

- **Language threshold (PG-13):** One use of harsher sexually-derived expletive; more than one requires R
- **Violence threshold (PG-13):** Not both realistic AND extreme/persistent
- **Sexual content (R):** Sexually-oriented nudity, adult themes

### TV Parental Guidelines

Content descriptors that may apply:
- **D** (Suggestive Dialogue): Sexual references
- **L** (Language): Coarse/offensive language
- **S** (Sexual Content): Visual innuendo or intercourse
- **V** (Violence): Violent content

---

## Automated Rating Support

The `ContentAnalyzer` module (future implementation) will:
1. Automatically detect profanity levels
2. Flag sexual content patterns
3. Identify dark humor themes
4. Suggest maturity ratings

**Human review still required for:**
- Context-dependent content
- Innuendo detection (AI struggles with subtlety)
- Cultural sensitivity
- Edge cases

---

## Edge Cases & Guidelines

### Euphemisms
- "Freaking", "dang", "heck" → Considered clean (G/PG)
- Creative spelling ("f*ck", "sh!t") → Rate as full profanity

### Context-Dependent Words
- "Ass" in "donkey" → Clean
- "Ass" in "kick your ass" → Mild profanity (PG)
- "Asshole" → Moderate profanity (PG-13)

### Medical/Scientific Terms
- Anatomically correct terms in educational context → May be G/PG
- Same terms in sexual joke → PG-13/R depending on usage

### Cultural Variations
- Current system uses US standards (MPAA/TV guidelines)
- Future: May need region-specific ratings

### Wordplay Edge Cases
- Joke relies on profanity for punchline → Rate for profanity
- Censored profanity ("f***") → Rate as if uncensored
- Implied profanity ("What the...") → Rate conservatively

---

## Review Process

During import staging review:

1. **Auto-rating runs** on import
2. **Reviewer checks** suggested rating
3. **Flags review** for low-confidence ratings
4. **Manual override** if auto-rating incorrect
5. **Documentation** of edge cases improves future auto-rating

---

## Future Enhancements

Planned improvements:

1. **ML-based classifier** for ambiguous content
2. **Region-specific ratings** (US, UK, international)
3. **User-contributed rating votes** (similar to IMDB)
4. **Confidence scores** for auto-ratings
5. **Custom wordlists** for joke-specific profanity
6. **Innuendo pattern detection** (ML-based)

---

## References

### External Standards
- [MPAA Film Rating System](https://www.filmratings.com/)
- [TV Parental Guidelines](https://www.tvguidelines.org/)
- [Common Sense Media Rating System](https://www.commonsensemedia.org/)

### Internal Documentation
- [Maturity Rating Experiments](experiments/MATURITY_RATING_EXPERIMENTS.md)
- [Schema Documentation](SCHEMA_OUTLINE.md)
- [Content Flags Model](../src/joke_emporium/models/flags.py)

---

## Quick Reference Table

| Rating | Profanity | Sexual | Violence | Dark Humor | Typical Audience |
|--------|-----------|--------|----------|------------|------------------|
| G | None | None | None | None | All ages |
| PG | Mild (1-2x) | Mild references | None | Minimal | 8+ with guidance |
| PG-13 | Moderate or 1x strong | Innuendo | Mild | Moderate | 13+ |
| R | Strong (2+x) | Explicit themes | Intense | Intense | 17+ |
| X | Extreme | Pornographic | Extreme | Extreme | Adults only |

---

**For questions or rating disputes, consult the experiment results in `experiments/output/maturity_rating_analysis.json` for data-driven examples.**
