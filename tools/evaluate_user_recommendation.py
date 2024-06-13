import argparse

from sqlalchemy.sql import select

from common.models import create_session, Rating
from recommender.item_based_cf import ItemBasedCF


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--user-id', type=str, required=True, help='user ID to use for calculate MSE')
    args = parser.parse_args()

    recommend_engine = ItemBasedCF()
    recommend_engine.build()
    recommend_engine.save()

    with create_session() as session:
        ret = session.execute(select(Rating).where(Rating.user_id == args.user_id))
        rated_movies = {rating.movie_id:rating.rating for rating in ret.scalars()}

        sum_squared_error = 0
        for movie_id, rating in rated_movies.items():
            predicted_rating = recommend_engine.predict_rating(args.user_id, movie_id)
            sum_squared_error += (rating - predicted_rating) ** 2

        mse = sum_squared_error / len(rated_movies)
        print(f'Mean Squared Error of rating for user {args.user_id}: {mse}')
