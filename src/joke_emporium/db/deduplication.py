"""Deduplication logic for jokes.

Based on experimental findings from 208k joke analysis:
- Hash-based exact match: 100% recall on real duplicates
- Aggressive normalization: 68.5% recall on variations
- Levenshtein 90%: 71.2% recall on variations

See: experiments/output/EXPERIMENT_RESULTS.md
"""

import re
import unicodedata

from sqlmodel import Session, select

from joke_emporium.db.models.staging import ReviewStatus, StagingJokeDB
from joke_emporium.models.joke import Joke


def normalize_text(text: str) -> str:
    """Normalize joke text for comparison.

    Aggressive normalization (68.5% recall on variations):
    - Unicode normalization (NFC) - handles 4% of jokes with unicode
    - Casefold (better than lower for unicode)
    - Normalize line breaks
    - Preserve ellipsis (23% of jokes have timing markers)
    - Remove punctuation (preserves apostrophes)
    - Normalize whitespace

    Based on analysis of 208k jokes:
    - 23% have ellipsis - preserve for timing
    - 17% have numbers - consider future normalization
    - 15% very long (>500 chars)
    - 10% have SHOUTING - casefolding handles this
    """
    # Unicode normalization
    text = unicodedata.normalize("NFC", text)

    # Casefold (better than lower for unicode)
    text = text.casefold()

    # Normalize line breaks
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Preserve ellipsis (timing marker)
    text = text.replace("...", " ELLIPSIS ")

    # Remove punctuation (except apostrophes in contractions)
    text = re.sub(r"[^\w\s'ELLIPSIS]", "", text)

    # Restore ellipsis
    text = text.replace("ELLIPSIS", "...")

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def get_joke_text(joke: Joke) -> str:
    """Extract text content from joke."""
    return " ".join(elem.text for elem in joke.content)


def check_duplicate_in_staging(
    session: Session, joke: Joke, import_batch_id: int | None = None
) -> tuple[bool, str | None]:
    """Check if joke is duplicate within staging.

    Args:
        session: Database session
        joke: Joke to check
        import_batch_id: Optional batch to check within

    Returns:
        (is_duplicate, duplicate_uuid)
    """
    # Normalize joke text
    normalized = normalize_text(get_joke_text(joke))

    # Query staging for similar jokes
    query = select(StagingJokeDB)

    if import_batch_id:
        query = query.where(StagingJokeDB.import_batch_id == import_batch_id)

    # Don't check against rejected jokes
    query = query.where(StagingJokeDB.review_status != ReviewStatus.REJECTED)

    staging_jokes = session.exec(query).all()

    for staging_joke in staging_jokes:
        # Skip self-comparison
        if staging_joke.joke_uuid == joke.id:
            continue

        # Parse staging joke content
        import json

        content_data = json.loads(staging_joke.content_json)
        staging_text = " ".join(elem.get("text", "") for elem in content_data)
        staging_normalized = normalize_text(staging_text)

        if normalized == staging_normalized:
            return (True, staging_joke.joke_uuid)

    return (False, None)


def check_duplicate_in_production(session: Session, joke: Joke) -> tuple[bool, str | None]:
    """Check if joke exists in production database.

    Args:
        session: Production database session
        joke: Joke to check

    Returns:
        (is_duplicate, duplicate_uuid)
    """
    # Import here to avoid circular dependency
    from joke_emporium.db.models.joke import JokeDB

    # Normalize joke text
    normalized = normalize_text(get_joke_text(joke))

    # Query production jokes
    query = select(JokeDB)
    production_jokes = session.exec(query).all()

    for prod_joke in production_jokes:
        # Parse production joke content
        import json

        content_data = json.loads(prod_joke.content_json)
        prod_text = " ".join(elem.get("text", "") for elem in content_data)
        prod_normalized = normalize_text(prod_text)

        if normalized == prod_normalized:
            return (True, prod_joke.joke_uuid)

    return (False, None)


def mark_duplicates_in_batch(session: Session, import_batch_id: int) -> int:
    """Find and mark duplicates within an import batch.

    Args:
        session: Database session
        import_batch_id: Import batch to check

    Returns:
        Number of duplicates found
    """
    import json

    duplicates_found = 0
    seen_texts = {}  # normalized_text -> uuid

    # Get all jokes in batch with pending status
    query = select(StagingJokeDB).where(
        StagingJokeDB.import_batch_id == import_batch_id, StagingJokeDB.review_status == ReviewStatus.PENDING
    )
    staging_jokes = session.exec(query).all()

    for staging_joke in staging_jokes:
        # Extract and normalize text
        content_data = json.loads(staging_joke.content_json)
        text = " ".join(elem.get("text", "") for elem in content_data)
        normalized = normalize_text(text)

        if normalized in seen_texts:
            # Mark as duplicate
            staging_joke.review_status = ReviewStatus.DUPLICATE
            staging_joke.duplicate_of_uuid = seen_texts[normalized]
            staging_joke.duplicate_similarity = 1.0  # Exact match
            session.add(staging_joke)
            duplicates_found += 1
        else:
            seen_texts[normalized] = staging_joke.joke_uuid

    session.commit()
    return duplicates_found
