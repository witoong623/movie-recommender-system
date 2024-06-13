import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix, csr_matrix
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select, delete, func

from common.models import create_session, MovieSimilarity, Rating
from recommender.base import Recommender


def normalize(x):
    x = x.astype(float)
    x_sum = x.sum()
    x_num = x.astype(bool).sum()
    x_mean = x_sum / x_num

    if x_num == 1 or x.std() == 0:
        return 0.0
    return (x - x_mean) / (x.max() - x.min())


def save_to_db(item_to_add):
    with create_session() as session:
        session.add_all(item_to_add)
        session.commit()


class ItemBasedCF(Recommender):
    def __init__(self):
        self._min_overlap = 15
        self._min_sim = 0.2

        self._rating_df: pd.DataFrame | None = None
        self._movie_sim_csr: csr_matrix | None = None
        self._max_candidates = 500

    def get_recommended_movies(self, user_id: int, limit: int) -> list[int]:
        with create_session() as session:
            ret = session.execute(select(Rating).where(Rating.user_id == user_id))
            rated_movies = {rating.movie_id:rating.rating for rating in ret.scalars()}
            rating_mean = sum(rated_movies.values()) / len(rated_movies)

            stmt = (select(MovieSimilarity)
                    .where(MovieSimilarity.source_id.in_(rated_movies.keys()),
                           ~MovieSimilarity.target_id.in_(rated_movies.keys()),
                           MovieSimilarity.similarity > self._min_sim)
                    .order_by(MovieSimilarity.similarity.desc())
                    .limit(self._max_candidates))
            ret = session.execute(stmt)

            movie_similarities = ret.scalars().all()
        candidate_movies = {}

        for movie_sim in movie_similarities:
            target_id = movie_sim.target_id

            rated_sim_sum = 0
            sim_sum = 0

            # movie that user watch that are similar to a target movie
            sim_to_targets = [sim for sim in movie_similarities if sim.target_id == target_id]

            if len(sim_to_targets) > 1:
                for sim_to_target in sim_to_targets:
                    normed_rating = rated_movies[sim_to_target.source_id] - rating_mean
                    rated_sim_sum += sim_to_target.similarity * normed_rating
                    sim_sum += sim_to_target.similarity

                if sim_sum > 0:
                    candidate_movies[target_id] = rating_mean + (rated_sim_sum / sim_sum)

        sorted_candidates = sorted(candidate_movies.items(), key=lambda x: x[1], reverse=True)[:limit]

        return sorted_candidates

    def build(self, **kwargs):
        with create_session() as session:
            rating_df = pd.read_sql(select(Rating), session.bind)

        rating_df.drop(columns=["id"], inplace=True)
        rating_df.dropna(inplace=True)

        rating_df['movie_id'] = rating_df['movie_id'].astype(float)

        # For each user, normalize rating for that user by mean and (max - min) of ratings of that user
        rating_df['avg'] = rating_df.groupby('user_id')['rating'].transform(lambda x: normalize(x))

        rating_df['user_id'] = rating_df['user_id'].astype('category')
        rating_df['movie_id'] = rating_df['movie_id'].astype('category')

        coo = coo_matrix((rating_df['avg'].astype(float),
                 (rating_df['movie_id'].cat.codes.copy(),
                  rating_df['user_id'].cat.codes.copy())))

        overlap_matrix = coo.astype(bool).astype(int).dot(coo.transpose().astype(bool).astype(int))

        number_of_overlaps = (overlap_matrix > self._min_overlap).count_nonzero()
        print(f'Overlap matrix leaves {number_of_overlaps} out of '
              f'{overlap_matrix.count_nonzero()} with {self._min_overlap}')

        print(f'Rating matrix (size {coo.shape[0]}x{coo.shape[1]}) finished')

        movie_sim_csr = cosine_similarity(coo, dense_output=False)

        movie_sim_csr = movie_sim_csr.multiply(movie_sim_csr > self._min_sim)
        movie_sim_csr = movie_sim_csr.multiply(overlap_matrix > self._min_overlap)

        self._movie_sim_csr = movie_sim_csr
        self._rating_df = rating_df

    def save(self, **kwargs):
        if self._movie_sim_csr is None:
            raise Exception('Cannot save before movie similarity is not built yet')

        with create_session() as session:
            session.execute(delete(MovieSimilarity))

            sim_count_stmt = select(func.count()).select_from(MovieSimilarity)
            sim_count = session.execute(sim_count_stmt).scalar()

            print(f'There are {sim_count} similarities in the database after delete')

        movie_indexes = dict(enumerate(self._rating_df['movie_id'].cat.categories))

        add_count = 0
        sim_to_add = []
        coo = coo_matrix(self._movie_sim_csr)
        csr = coo.tocsr()

        xs, ys = coo.nonzero()
        for x, y in zip(xs, ys):
            if x == y:
                continue

            sim = csr[x, y]

            if sim < self._min_sim:
                continue

            sim_to_add.append(MovieSimilarity(
                source_id=int(movie_indexes[x]),
                target_id=int(movie_indexes[y]),
                similarity=sim
            ))

            if len(sim_to_add) == 1000:
                save_to_db(sim_to_add)
                sim_to_add.clear()

            add_count += 1

        save_to_db(sim_to_add)
        sim_to_add.clear()

        print(f'Added {add_count} similarities to DB')

    def load(self, **kwargs):
        pass

    def predict_rating(self, user_id: int, movie_id: int) -> float:
        ''' Predict rating of a movie for a user '''
        with create_session() as session:
            stmt = (select(Rating)
                    .where(Rating.user_id == user_id, Rating.movie_id != movie_id)
                    .order_by(Rating.rating.desc()))
            ret = session.execute(stmt)

            rated_movies = {rating.movie_id:rating.rating for rating in ret.scalars()}

            stmt = (select(MovieSimilarity)
                    .where(MovieSimilarity.source_id.in_(rated_movies.keys()),
                           ~MovieSimilarity.target_id != movie_id)
                    .order_by(MovieSimilarity.similarity.desc())
                    .limit(self._max_candidates))
            ret = session.execute(stmt)

            movie_similarities = ret.scalars().all()

        if len(movie_similarities) == 0:
            return 0.0

        rated_sim_sum = 0
        sim_sum = 0

        for movie_sim in movie_similarities:
            rating = rated_movies[movie_sim.source_id]
            rated_sim_sum += movie_sim.similarity * rating
            sim_sum += movie_sim.similarity

        return rated_sim_sum / sim_sum
