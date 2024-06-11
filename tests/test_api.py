import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import api.main
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
    pass


def test_get_movie_id_success(mock_recommender):
    response = client.get('/recommendations?user_id=1')

    assert response.json() == {'items': [{'id': 1}, {'id': 2}]}
