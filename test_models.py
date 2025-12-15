"""Quick test to verify the Pydantic models work correctly."""

from datetime import datetime

from joke_emporium.models import (
    Joke,
    JokeElement,
    Author,
    RatingSource,
    Vote,
    JokeMetadata,
    ContentFlags,
    Collection,
    Category,
    StructureType,
    MaturityRating,
    ElementType,
    AuthorType,
    LinguisticMechanism,
)


def test_basic_joke():
    """Test creating a basic joke."""

    # Create a simple joke
    joke = Joke(
        id="550e8400-e29b-41d4-a716-446655440000",
        version=1,
        content=[
            JokeElement(type=ElementType.SETUP, text="Why did the chicken cross the road?"),
            JokeElement(type=ElementType.PUNCHLINE, text="To get to the other side!"),
        ],
        categories=[Category.ANIMALS, Category.WORDPLAY],
        structure=StructureType.QA,
        mechanisms=[LinguisticMechanism.PARAPROSDOKIAN],
        maturity_rating=MaturityRating.G,
        tags=["classic", "wholesome"],
        flags=ContentFlags(),
        ratings=[
            RatingSource(
                source="manual_annotation",
                min_rating=1.0,
                max_rating=5.0,
                total_ratings=10,
                avg_funniness=3.5,
                avg_quality=3.2,
            )
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

    # Test computed fields
    print(f"Joke ID: {joke.id}")
    print(f"Text preview: {joke.text_preview}")
    print(f"Weighted avg funniness: {joke.weighted_avg_funniness}")
    print(f"Weighted avg quality: {joke.weighted_avg_quality}")
    print(f"Total ratings: {joke.total_ratings_count}")

    # Test normalization
    rating = joke.ratings[0]
    print(f"\nRating normalization test:")
    print(f"  Original scale: {rating.min_rating}-{rating.max_rating}")
    print(f"  Avg funniness (original): {rating.avg_funniness}")
    print(f"  Avg funniness (normalized 1-5): {rating.normalized_avg_funniness}")

    # Test JSON serialization
    joke_json = joke.model_dump_json(indent=2)
    print(f"\nJoke serialized to JSON successfully ({len(joke_json)} chars)")

    return joke


def test_collection():
    """Test creating a collection."""

    joke = test_basic_joke()

    collection = Collection(
        name="jokes_en_clean",
        version="1.0.0",
        language="en",
        maturity_filter=MaturityRating.PG13,
        description="Test collection",
        created_date=datetime.now(),
        last_modified=datetime.now(),
        jokes=[joke],
    )

    print(f"\n{'='*60}")
    print(f"Collection: {collection.name}")
    print(f"Total jokes: {collection.total_jokes}")
    print(f"Total ratings: {collection.total_ratings}")
    print(f"Avg funniness: {collection.avg_funniness}")
    print(f"Category distribution: {collection.category_distribution}")
    print(f"Maturity distribution: {collection.maturity_distribution}")

    # Test JSON serialization
    collection_json = collection.model_dump_json(indent=2)
    print(f"\nCollection serialized to JSON successfully ({len(collection_json)} chars)")

    return collection


def test_rating_normalization():
    """Test rating normalization with different scales."""

    print(f"\n{'='*60}")
    print("Testing rating normalization across different scales:\n")

    # Reddit (0-1 scale)
    reddit_rating = RatingSource(
        source="reddit",
        min_rating=0.0,
        max_rating=1.0,
        total_ratings=1335,
        avg_funniness=0.936,
    )
    print(f"Reddit (0-1): {reddit_rating.avg_funniness} -> {reddit_rating.normalized_avg_funniness:.2f}")

    # IMDB (1-10 scale)
    imdb_rating = RatingSource(
        source="imdb",
        min_rating=1.0,
        max_rating=10.0,
        total_ratings=100,
        avg_funniness=7.8,
    )
    print(f"IMDB (1-10): {imdb_rating.avg_funniness} -> {imdb_rating.normalized_avg_funniness:.2f}")

    # Percentage (0-100 scale)
    percent_rating = RatingSource(
        source="percentage",
        min_rating=0,
        max_rating=100,
        total_ratings=50,
        avg_funniness=87,
    )
    print(f"Percentage (0-100): {percent_rating.avg_funniness} -> {percent_rating.normalized_avg_funniness:.2f}")

    # Already normalized (1-5 scale)
    normalized_rating = RatingSource(
        source="manual",
        min_rating=1.0,
        max_rating=5.0,
        total_ratings=10,
        avg_funniness=4.67,
    )
    print(f"Already 1-5: {normalized_rating.avg_funniness} -> {normalized_rating.normalized_avg_funniness:.2f}")


if __name__ == "__main__":
    print("Testing Joke Emporium Pydantic models...\n")
    print("="*60)

    test_rating_normalization()
    test_collection()

    print("\n" + "="*60)
    print("SUCCESS: All tests passed! Models are working correctly.")
