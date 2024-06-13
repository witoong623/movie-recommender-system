import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import recommender.item_based_cf
from common.models import Base, Movie, MovieSimilarity, Rating
from recommender.item_based_cf import ItemBasedCF


LIMIT = 20

@pytest.fixture
def mock_db(monkeypatch):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False})
    Base.metadata.create_all(bind=engine)

    create_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = create_session()

    session.add_all([
        Movie(id=1, title='Movie 1', genres='Action|Adventure'),
        Movie(id=2, title='Movie 2', genres='Comedy|Drama'),
        Movie(id=3, title='Movie 3', genres='Action|Drama'),

        Rating(user_id=1, movie_id=1, rating=5.0),
        Rating(user_id=1, movie_id=2, rating=3.0),
        Rating(user_id=2, movie_id=1, rating=4.0),
        Rating(user_id=2, movie_id=2, rating=2.0),

        MovieSimilarity(source_id=1, target_id=2, similarity=0.9),
        MovieSimilarity(source_id=1, target_id=3, similarity=0.5),
        MovieSimilarity(source_id=2, target_id=1, similarity=0.7),
        MovieSimilarity(source_id=2, target_id=3, similarity=0.3),
    ])
    session.commit()

    monkeypatch.setattr(recommender.item_based_cf, 'create_session', lambda: session)
    # this make sure that table exist in memory
    session.execute(select(Movie)).scalars().all()

    yield


def test_get_recommended_movies(mock_db):
    recommender = ItemBasedCF()
    recommender.build()

    recommended_movies = recommender.get_recommended_movies(1, LIMIT)

    assert recommended_movies == [(3, 4.25)]


def test_get_recommended_movies_no_user(mock_db):
    recommender = ItemBasedCF()
    recommender.build()

    recommended_movies = recommender.get_recommended_movies(3, LIMIT)

    assert recommended_movies == []
