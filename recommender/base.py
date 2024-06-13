import abc


class Recommender(abc.ABC):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__()

    @abc.abstractmethod
    def get_recommended_movies(self, user_id: int, limit: int) -> list[tuple[int, float]]:
        pass

    @abc.abstractmethod
    def build(self, **kwargs):
        ''' Build state of Recommender '''
        pass

    def save(self, **kwargs):
        ''' Save state of Recommender '''
        pass

    def load(self, **kwargs):
        ''' Load state of Recommender, so that it is ready to be used for inference '''
        pass

    def predict_rating(self, user_id: int, movie_id: int) -> float:
        ''' Predict rating of a movie for a user '''
        return 0.0


_registry = {}


def register_recommender(name, cls):
    _registry[name] = cls


def get_recommender_from_config(config):
    if config['name'] not in _registry:
        raise ValueError(f"Recommender {config['name']} not found")

    return _registry[config['name']](**config['params'])
