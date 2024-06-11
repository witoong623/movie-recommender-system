import abc


class Recommender(abc.ABC):
    @abc.abstractmethod
    def get_recommended_movies(self, user_id: int, limit: int) -> list[int]:
        pass

    @abc.abstractmethod
    def build(self, **kwargs):
        ''' Build state of Recommender '''
        pass

    @abc.abstractmethod
    def save(self, **kwargs):
        ''' Save state of Recommender '''
        # TODO: decide if I should have a separate method for saving
        pass

    @abc.abstractmethod
    def load(self, **kwargs):
        ''' Load state of Recommender, so that it is ready to be used for inference '''
        pass
