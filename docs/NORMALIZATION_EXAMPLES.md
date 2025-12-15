# Rating Normalization Examples

## Why Normalize?

Different joke sources use different rating scales:
- **Reddit**: Upvote ratio (0.0-1.0)
- **IMDB-style sites**: 1-10 scale
- **Binary sites**: Like/dislike (0-1)
- **Manual annotation**: Usually 1-5
- **Amazon-style**: 1-5 stars
- **Rotten Tomatoes-style**: 0-100 percentage

To compare and aggregate ratings across sources, we normalize everything to **1.0-5.0 scale**.

---

## Normalization Formula

```
normalized = 1.0 + (raw - min) * (5.0 - 1.0) / (max - min)
```

Where:
- `raw` = the original rating value
- `min` = minimum possible rating in the original scale
- `max` = maximum possible rating in the original scale
- Result is always in 1.0-5.0 range

---

## Examples

### Reddit Upvote Ratio (0.0-1.0 scale)

**Original scale**: 0.0 (all downvotes) to 1.0 (all upvotes)

| Raw Score | Calculation | Normalized |
|-----------|-------------|------------|
| 0.0 | 1.0 + (0.0 - 0.0) * 4.0 / 1.0 | 1.0 |
| 0.25 | 1.0 + (0.25 - 0.0) * 4.0 / 1.0 | 2.0 |
| 0.50 | 1.0 + (0.50 - 0.0) * 4.0 / 1.0 | 3.0 |
| 0.75 | 1.0 + (0.75 - 0.0) * 4.0 / 1.0 | 4.0 |
| 0.936 | 1.0 + (0.936 - 0.0) * 4.0 / 1.0 | 4.74 |
| 1.0 | 1.0 + (1.0 - 0.0) * 4.0 / 1.0 | 5.0 |

**Example**: A joke with 1250 upvotes and 85 downvotes:
- Upvote ratio = 1250/(1250+85) = 0.936
- Normalized score = **4.74 out of 5**

---

### IMDB-Style (1.0-10.0 scale)

**Original scale**: 1.0 (worst) to 10.0 (best)

| Raw Score | Calculation | Normalized |
|-----------|-------------|------------|
| 1.0 | 1.0 + (1.0 - 1.0) * 4.0 / 9.0 | 1.0 |
| 3.25 | 1.0 + (3.25 - 1.0) * 4.0 / 9.0 | 2.0 |
| 5.5 | 1.0 + (5.5 - 1.0) * 4.0 / 9.0 | 3.0 |
| 7.75 | 1.0 + (7.75 - 1.0) * 4.0 / 9.0 | 4.0 |
| 7.8 | 1.0 + (7.8 - 1.0) * 4.0 / 9.0 | 4.02 |
| 10.0 | 1.0 + (10.0 - 1.0) * 4.0 / 9.0 | 5.0 |

**Example**: An IMDB-style rating of 7.8/10:
- Normalized score = **4.02 out of 5**

---

### Manual Annotation (1.0-5.0 scale)

**Original scale**: 1.0 (not funny) to 5.0 (hilarious)

| Raw Score | Calculation | Normalized |
|-----------|-------------|------------|
| 1.0 | 1.0 + (1.0 - 1.0) * 4.0 / 4.0 | 1.0 |
| 2.0 | 1.0 + (2.0 - 1.0) * 4.0 / 4.0 | 2.0 |
| 3.0 | 1.0 + (3.0 - 1.0) * 4.0 / 4.0 | 3.0 |
| 4.0 | 1.0 + (4.0 - 1.0) * 4.0 / 4.0 | 4.0 |
| 4.67 | 1.0 + (4.67 - 1.0) * 4.0 / 4.0 | 4.67 |
| 5.0 | 1.0 + (5.0 - 1.0) * 4.0 / 4.0 | 5.0 |

**Example**: Manual rating of 4.67/5:
- Normalized score = **4.67 out of 5** (no change)

---

### Binary Like/Dislike (0.0-1.0 scale)

**Original scale**: 0.0 (dislike) to 1.0 (like)

Same as Reddit upvote ratio.

| Raw Score | Calculation | Normalized |
|-----------|-------------|------------|
| 0.0 | 1.0 + (0.0 - 0.0) * 4.0 / 1.0 | 1.0 |
| 0.5 | 1.0 + (0.5 - 0.0) * 4.0 / 1.0 | 3.0 |
| 0.78 | 1.0 + (0.78 - 0.0) * 4.0 / 1.0 | 4.12 |
| 1.0 | 1.0 + (1.0 - 0.0) * 4.0 / 1.0 | 5.0 |

**Example**: 351 likes, 99 dislikes:
- Like ratio = 351/450 = 0.78
- Normalized score = **4.12 out of 5**

---

### Percentage (0-100 scale)

**Original scale**: 0 (worst) to 100 (best)

| Raw Score | Calculation | Normalized |
|-----------|-------------|------------|
| 0 | 1.0 + (0 - 0) * 4.0 / 100 | 1.0 |
| 25 | 1.0 + (25 - 0) * 4.0 / 100 | 2.0 |
| 50 | 1.0 + (50 - 0) * 4.0 / 100 | 3.0 |
| 75 | 1.0 + (75 - 0) * 4.0 / 100 | 4.0 |
| 87 | 1.0 + (87 - 0) * 4.0 / 100 | 4.48 |
| 100 | 1.0 + (100 - 0) * 4.0 / 100 | 5.0 |

**Example**: 87% "Fresh" rating:
- Normalized score = **4.48 out of 5**

---

### Kaggle Dataset (0-10 scale)

**Original scale**: 0 (worst) to 10 (best)

| Raw Score | Calculation | Normalized |
|-----------|-------------|------------|
| 0 | 1.0 + (0 - 0) * 4.0 / 10 | 1.0 |
| 2.5 | 1.0 + (2.5 - 0) * 4.0 / 10 | 2.0 |
| 5.0 | 1.0 + (5.0 - 0) * 4.0 / 10 | 3.0 |
| 7.5 | 1.0 + (7.5 - 0) * 4.0 / 10 | 4.0 |
| 7.0 | 1.0 + (7.0 - 0) * 4.0 / 10 | 3.8 |
| 10 | 1.0 + (10 - 0) * 4.0 / 10 | 5.0 |

**Example**: Kaggle score of 7/10:
- Normalized score = **3.8 out of 5**

---

## Weighted Average Example

Given a joke with ratings from multiple sources:

```json
{
  "ratings": [
    {
      "source": "manual_annotation",
      "total_ratings": 3,
      "normalized_avg_funniness": 4.67
    },
    {
      "source": "reddit",
      "total_ratings": 257,
      "normalized_avg_funniness": 4.81
    },
    {
      "source": "kaggle_dataset",
      "total_ratings": 1,
      "normalized_avg_funniness": 3.8
    }
  ]
}
```

**Weighted average calculation:**
```
total_weight = 3 + 257 + 1 = 261

weighted_sum = (4.67 * 3) + (4.81 * 257) + (3.8 * 1)
             = 14.01 + 1236.17 + 3.8
             = 1253.98

weighted_avg = 1253.98 / 261 = 4.804
```

**Result**: Weighted average funniness = **4.80 out of 5**

Note: The Reddit rating (with 257 votes) dominates the average due to its much higher weight.

---

## Implementation in Pydantic

The RatingSource model will auto-compute normalized scores:

```python
from pydantic import BaseModel, computed_field

class RatingSource(BaseModel):
    source: str
    min_rating: float = 1.0
    max_rating: float = 5.0
    avg_funniness: float
    avg_quality: float | None = None

    @computed_field
    @property
    def normalized_avg_funniness(self) -> float:
        """Auto-compute normalized funniness (1-5 scale)."""
        if self.max_rating == self.min_rating:
            return 3.0
        return 1.0 + (self.avg_funniness - self.min_rating) * 4.0 / (self.max_rating - self.min_rating)

    @computed_field
    @property
    def normalized_avg_quality(self) -> float | None:
        """Auto-compute normalized quality (1-5 scale)."""
        if self.avg_quality is None:
            return None
        if self.max_rating == self.min_rating:
            return 3.0
        return 1.0 + (self.avg_quality - self.min_rating) * 4.0 / (self.max_rating - self.min_rating)
```

---

## Benefits

✅ **Universal comparison**: Compare ratings from Reddit, IMDB, binary systems, etc.
✅ **Accurate aggregation**: Weighted averages use normalized scores
✅ **Preserve provenance**: Original ratings + scale stored for transparency
✅ **Flexible**: Support any rating system by specifying min/max
✅ **Automatic**: Pydantic computes normalized scores automatically

---

## Edge Cases

### Invalid Scale (min == max)
If min_rating equals max_rating (shouldn't happen, but just in case):
- Default to normalized score of 3.0 (middle of 1-5 range)

### Out of Range
If raw score is outside [min, max] range:
- Could clamp to range or raise validation error
- Recommend validation in Pydantic model

### Negative Scales
Works fine! For example, -1 to +1 scale:
- min_rating = -1.0
- max_rating = 1.0
- Raw score 0.5 → Normalized = 1.0 + (0.5 - (-1.0)) * 4.0 / 2.0 = 4.0
