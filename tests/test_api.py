import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import api.main
from common.models import Base, Movie, Rating
from recommender.base import Recommender


client = TestClient(api.main.app)

class MockRecommender(Recommender):
    def get_recommended_movies(self, user_id: int, limit: int):
        # (movie id, predicted rating)
        return [(1, 0.9), (2, 0.5)]

    def build(self):
        pass

    def save(self):
        pass

    def load(self):
        pass

@pytest.fixture
def mock_recommender(monkeypatch):
    mock_recommender =  MockRecommender()
    monkeypatch.setattr(api.main, 'recommend_engine', mock_recommender)


@pytest.fixture
def mock_db(monkeypatch):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False})
    Base.metadata.create_all(bind=engine)

    create_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = create_session()

    session.add_all([
        Movie(id=1, title='Movie 1', genres='Action|Adventure'),
        Movie(id=2, title='Movie 2', genres='Comedy|Drama'),

        Rating(user_id=1, movie_id=1, rating=5.0),
        Rating(user_id=1, movie_id=2, rating=3.0),
        Rating(user_id=2, movie_id=1, rating=4.0),
        Rating(user_id=2, movie_id=2, rating=2.0),
    ])
    session.commit()

    monkeypatch.setattr(api.main, 'create_session', lambda: session)
    # this make sure that table exist in memory
    session.execute(select(Movie)).scalars().all()

    yield


def test_get_movie_id_success(mock_recommender, mock_db):
    response = client.get('/recommendations?user_id=1')

    expected_json = {'items': [{'id': 1}, {'id': 2}]}
    assert response.json() == expected_json


def test_get_movie_with_metadata_success(mock_recommender, mock_db):
    response = client.get('/recommendations?user_id=1&returnMetadata=true')

    expected_json = {
        'items': [
            {'id': 1, 'title': 'Movie 1', 'genres': ['Action', 'Adventure']},
            {'id': 2, 'title': 'Movie 2', 'genres': ['Comedy', 'Drama']},
        ]
    }
    assert response.json() == expected_json


def test_get_movie_not_exist_user(mock_recommender, mock_db):
    response = client.get('/recommendations?user_id=3&returnMetadata=true')

    assert response.status_code == 404


def test_get_user_feature_success(mock_db):
    response = client.get('/features?user_id=1')

    expected_json = {'features': [{'histories': [1, 2]}]}
    assert response.json() == expected_json


def test_get_user_feature_not_exist_user(mock_db):
    response = client.get('/features?user_id=3')

    assert response.status_code == 404
