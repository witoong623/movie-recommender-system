import abc


class Recommender(abc.ABC):
    @abc.abstractmethod
    def get_recommended_movies(self, user_id: int, limit: int) -> list[int]:
        pass
