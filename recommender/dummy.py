from recommender.base import Recommender


class DummyRecommender(Recommender):
    def get_recommended_movies(self, user_id, limit=10):
        return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
