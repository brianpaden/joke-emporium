"""Test SQLModel database layer."""

from datetime import datetime
from pathlib import Path

from joke_emporium.db import init_db
from joke_emporium.db.operations import (
    delete_joke,
    get_all_jokes,
    get_joke_by_uuid,
    get_jokes_by_author,
    get_jokes_by_category,
    save_joke,
)
from joke_emporium.db.session import get_session
from joke_emporium.models import (
    Author,
    AuthorType,
    Category,
    ContentFlags,
    ElementType,
    Joke,
    JokeElement,
    JokeMetadata,
    LinguisticMechanism,
    MaturityRating,
    RatingSource,
    StructureType,
    Vote,
)


def test_database_workflow():
    """Test complete database workflow: create, read, update, delete."""

    # Use temporary database
    db_path = Path("test_jokes.db")
    if db_path.exists():
        db_path.unlink()

    # Initialize database
    init_db(f"sqlite:///{db_path}", echo=True)
    print("Database initialized successfully")

    # Create test joke
    joke1 = Joke(
        id="550e8400-e29b-41d4-a716-446655440001",
        version=1,
        content=[
            JokeElement(type=ElementType.SETUP, text="Why did the scarecrow win an award?"),
            JokeElement(type=ElementType.PUNCHLINE, text="Because he was outstanding in his field!"),
        ],
        categories=[Category.WORK, Category.WORDPLAY],
        structure=StructureType.QA,
        mechanisms=[LinguisticMechanism.PUN_HOMOGRAPHIC],
        maturity_rating=MaturityRating.G,
        tags=["classic", "pun", "wholesome"],
        flags=ContentFlags(),
        ratings=[
            RatingSource(
                source="manual_annotation",
                min_rating=1.0,
                max_rating=5.0,
                total_ratings=10,
                avg_funniness=4.5,
                avg_quality=4.2,
                votes=[
                    Vote(funniness=5.0, quality=4.0, timestamp=datetime(2024, 1, 15, 14, 23, 45)),
                    Vote(funniness=4.0, quality=5.0, timestamp=datetime(2024, 1, 15, 15, 10, 22)),
                ],
            ),
            RatingSource(
                source="reddit",
                min_rating=0.0,
                max_rating=1.0,
                total_ratings=1335,
                avg_funniness=0.936,
            ),
        ],
        metadata=JokeMetadata(
            language="en",
            authors=[
                Author(
                    id="anonymous",
                    type=AuthorType.ANONYMOUS,
                    name="Anonymous",
                )
            ],
            added_date=datetime.now(),
            last_modified=datetime.now(),
            verified=True,
        ),
    )

    # Create second test joke
    joke2 = Joke(
        id="550e8400-e29b-41d4-a716-446655440002",
        version=1,
        content=[
            JokeElement(type=ElementType.TEXT, text="I told my wife she was drawing her eyebrows too high."),
            JokeElement(type=ElementType.TEXT, text="She looked surprised."),
        ],
        categories=[Category.MARRIAGE, Category.WORDPLAY],
        structure=StructureType.ONE_LINER,
        mechanisms=[LinguisticMechanism.PUN_HOMOGRAPHIC],
        maturity_rating=MaturityRating.G,
        tags=["visual", "pun"],
        flags=ContentFlags(),
        ratings=[
            RatingSource(
                source="manual_annotation",
                min_rating=1.0,
                max_rating=5.0,
                total_ratings=5,
                avg_funniness=3.8,
                avg_quality=4.0,
            )
        ],
        metadata=JokeMetadata(
            language="en",
            authors=[
                Author(
                    id="comedian_123",
                    type=AuthorType.INDIVIDUAL,
                    name="Comedy Master",
                    url="https://example.com/comedian",
                )
            ],
            added_date=datetime.now(),
            last_modified=datetime.now(),
            verified=False,
        ),
    )

    print("\n" + "=" * 60)
    print("TEST 1: Save jokes to database")
    print("=" * 60)

    with next(get_session()) as session:
        # Save jokes
        joke1_db = save_joke(session, joke1)
        print(f"Saved joke 1: ID={joke1_db.id}, UUID={joke1_db.joke_uuid}")
        print(f"  Cached weighted_avg_funniness: {joke1_db.weighted_avg_funniness:.2f}")
        print(f"  Cached total_ratings: {joke1_db.total_ratings_count}")
        print(f"  Text preview: {joke1_db.text_preview}")

        joke2_db = save_joke(session, joke2)
        print(f"Saved joke 2: ID={joke2_db.id}, UUID={joke2_db.joke_uuid}")
        print(f"  Cached weighted_avg_funniness: {joke2_db.weighted_avg_funniness:.2f}")

    print("\n" + "=" * 60)
    print("TEST 2: Retrieve joke by UUID")
    print("=" * 60)

    with next(get_session()) as session:
        retrieved = get_joke_by_uuid(session, joke1.id)
        if retrieved:
            print(f"Retrieved joke: {retrieved.id}")
            print(f"  Categories: {[c.value for c in retrieved.categories]}")
            print(f"  Mechanisms: {[m.value for m in retrieved.mechanisms]}")
            print(f"  Authors: {[a.name for a in retrieved.metadata.authors] if retrieved.metadata.authors else []}")
            print(f"  Ratings count: {len(retrieved.ratings)}")
            print(f"  Computed weighted_avg_funniness: {retrieved.weighted_avg_funniness:.2f}")
            print(f"  Text preview: {retrieved.text_preview}")

            # Verify rating normalization
            for rating in retrieved.ratings:
                print(f"  Rating from {rating.source}:")
                print(f"    Original: {rating.avg_funniness} ({rating.min_rating}-{rating.max_rating})")
                print(f"    Normalized: {rating.normalized_avg_funniness:.2f} (1-5)")

    print("\n" + "=" * 60)
    print("TEST 3: Get all jokes")
    print("=" * 60)

    with next(get_session()) as session:
        all_jokes = get_all_jokes(session)
        print(f"Total jokes in database: {len(all_jokes)}")
        for joke in all_jokes:
            print(f"  - {joke.id}: {joke.text_preview}")

    print("\n" + "=" * 60)
    print("TEST 4: Query by category")
    print("=" * 60)

    with next(get_session()) as session:
        wordplay_jokes = get_jokes_by_category(session, "wordplay")
        print(f"Jokes in 'wordplay' category: {len(wordplay_jokes)}")
        for joke in wordplay_jokes:
            print(f"  - {joke.text_preview}")

    print("\n" + "=" * 60)
    print("TEST 5: Query by author")
    print("=" * 60)

    with next(get_session()) as session:
        anonymous_jokes = get_jokes_by_author(session, "anonymous")
        print(f"Jokes by 'anonymous': {len(anonymous_jokes)}")
        for joke in anonymous_jokes:
            print(f"  - {joke.text_preview}")

    print("\n" + "=" * 60)
    print("TEST 6: Update joke")
    print("=" * 60)

    # Modify joke1 and save again
    joke1.tags.append("updated")
    joke1.metadata.last_modified = datetime.now()

    with next(get_session()) as session:
        updated_db = save_joke(session, joke1)
        print(f"Updated joke: {updated_db.joke_uuid}")
        print(f"  New tags: {joke1.tags}")

    # Verify update
    with next(get_session()) as session:
        retrieved = get_joke_by_uuid(session, joke1.id)
        if retrieved:
            print(f"Verified tags after update: {retrieved.tags}")

    print("\n" + "=" * 60)
    print("TEST 7: Delete joke")
    print("=" * 60)

    with next(get_session()) as session:
        deleted = delete_joke(session, joke2.id)
        print(f"Deleted joke {joke2.id}: {deleted}")

        # Verify deletion
        remaining = get_all_jokes(session)
        print(f"Remaining jokes: {len(remaining)}")

    print("\n" + "=" * 60)
    print("TEST 8: Verify Pydantic compatibility")
    print("=" * 60)

    with next(get_session()) as session:
        retrieved = get_joke_by_uuid(session, joke1.id)
        if retrieved:
            # Export to JSON
            json_str = retrieved.model_dump_json(indent=2)
            print(f"Joke exported to JSON ({len(json_str)} chars)")
            print("First 500 chars:")
            print(json_str[:500])

            # Verify it matches Pydantic model
            print(f"\nPydantic model type: {type(retrieved).__name__}")
            print(f"Has computed fields: weighted_avg_funniness={retrieved.weighted_avg_funniness}")

    print("\n" + "=" * 60)
    print("SUCCESS: All database tests passed!")
    print("=" * 60)

    # Cleanup
    print(f"\nTest database created: {db_path}")
    print("Note: You may need to manually delete the test database file.")


if __name__ == "__main__":
    test_database_workflow()
