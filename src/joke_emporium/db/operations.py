"""Database operations for jokes."""

from sqlmodel import Session, select

from joke_emporium.db.models import (
    AuthorDB,
    JokeAuthorLink,
    JokeCategoryLink,
    JokeDB,
    JokeLinguisticMechanismLink,
    RatingSourceDB,
    VoteDB,
)
from joke_emporium.models.joke import Joke


def save_joke(session: Session, joke: Joke) -> JokeDB:
    """Save a Pydantic Joke to the database.

    This handles:
    - Creating/updating the joke record
    - Creating/linking authors
    - Creating category links
    - Creating mechanism links
    - Creating rating sources and votes
    - Computing cached fields

    Args:
        session: Database session
        joke: Pydantic Joke model

    Returns:
        Created/updated JokeDB instance
    """
    # Check if joke already exists by UUID
    statement = select(JokeDB).where(JokeDB.joke_uuid == joke.id)
    existing_joke = session.exec(statement).first()

    if existing_joke:
        joke_db = existing_joke
        # Update fields from pydantic model
        updated = JokeDB.from_pydantic(joke)
        for field, value in updated.model_dump(exclude={"id"}).items():
            setattr(joke_db, field, value)
    else:
        joke_db = JokeDB.from_pydantic(joke)
        session.add(joke_db)

    # Flush to get the ID
    session.flush()

    # Clear existing links if updating
    if existing_joke:
        # Clear category links
        for link in joke_db.category_links:
            session.delete(link)
        # Clear mechanism links
        for link in joke_db.mechanism_links:
            session.delete(link)
        # Clear author links
        for link in joke_db.author_links:
            session.delete(link)
        # Clear rating sources (cascade will delete votes)
        for rating in joke_db.rating_sources:
            session.delete(rating)
        session.flush()

    # Add authors
    if joke.metadata.authors:
        for author in joke.metadata.authors:
            # Get or create author
            author_statement = select(AuthorDB).where(AuthorDB.author_id == author.id)
            author_db = session.exec(author_statement).first()

            if not author_db:
                author_db = AuthorDB.from_pydantic(author)
                session.add(author_db)
                session.flush()

            # Create link
            link = JokeAuthorLink(joke_id=joke_db.id, author_id=author_db.id)
            session.add(link)

    # Add category links
    for category in joke.categories:
        link = JokeCategoryLink(joke_id=joke_db.id, category=category.value)
        session.add(link)

    # Add mechanism links
    for mechanism in joke.mechanisms:
        link = JokeLinguisticMechanismLink(joke_id=joke_db.id, mechanism=mechanism.value)
        session.add(link)

    # Add rating sources
    for rating in joke.ratings:
        rating_db = RatingSourceDB.from_pydantic(rating, joke_id=joke_db.id)
        session.add(rating_db)
        session.flush()

        # Add votes if present
        if rating.votes:
            for vote in rating.votes:
                vote_db = VoteDB.from_pydantic(vote, rating_source_id=rating_db.id)
                session.add(vote_db)

    # Update cached computed fields
    session.flush()
    joke_db.update_computed_fields()

    session.commit()
    session.refresh(joke_db)

    return joke_db


def get_joke_by_uuid(session: Session, joke_uuid: str) -> Joke | None:
    """Get a joke by its UUID.

    Args:
        session: Database session
        joke_uuid: Joke UUID

    Returns:
        Pydantic Joke model or None if not found
    """
    statement = select(JokeDB).where(JokeDB.joke_uuid == joke_uuid)
    joke_db = session.exec(statement).first()

    if joke_db:
        return joke_db.to_pydantic()

    return None


def get_all_jokes(session: Session, limit: int | None = None, offset: int = 0) -> list[Joke]:
    """Get all jokes from the database.

    Args:
        session: Database session
        limit: Maximum number of jokes to return
        offset: Number of jokes to skip

    Returns:
        List of Pydantic Joke models
    """
    statement = select(JokeDB).offset(offset)

    if limit:
        statement = statement.limit(limit)

    jokes_db = session.exec(statement).all()

    return [joke_db.to_pydantic() for joke_db in jokes_db]


def get_jokes_by_category(session: Session, category: str, limit: int | None = None) -> list[Joke]:
    """Get jokes by category.

    Args:
        session: Database session
        category: Category value
        limit: Maximum number of jokes to return

    Returns:
        List of Pydantic Joke models
    """
    statement = select(JokeDB).join(JokeCategoryLink).where(JokeCategoryLink.category == category)

    if limit:
        statement = statement.limit(limit)

    jokes_db = session.exec(statement).all()

    return [joke_db.to_pydantic() for joke_db in jokes_db]


def get_jokes_by_author(session: Session, author_id: str, limit: int | None = None) -> list[Joke]:
    """Get jokes by author ID.

    Args:
        session: Database session
        author_id: Author identifier
        limit: Maximum number of jokes to return

    Returns:
        List of Pydantic Joke models
    """
    statement = select(JokeDB).join(JokeAuthorLink).join(AuthorDB).where(AuthorDB.author_id == author_id)

    if limit:
        statement = statement.limit(limit)

    jokes_db = session.exec(statement).all()

    return [joke_db.to_pydantic() for joke_db in jokes_db]


def delete_joke(session: Session, joke_uuid: str) -> bool:
    """Delete a joke by UUID.

    Args:
        session: Database session
        joke_uuid: Joke UUID

    Returns:
        True if joke was deleted, False if not found
    """
    statement = select(JokeDB).where(JokeDB.joke_uuid == joke_uuid)
    joke_db = session.exec(statement).first()

    if joke_db:
        session.delete(joke_db)
        session.commit()
        return True

    return False
