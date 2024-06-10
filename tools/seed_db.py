import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func, select

from common.models import create_session, Movie, Rating


def save_to_db(session: Session, item_to_add):
    session.add_all(item_to_add)
    session.commit()


with create_session() as session:
    items_to_add = []

    print('Adding movies')
    movie_df = pd.read_csv('data/movies.csv')

    movie_count_stmt = select(func.count()).select_from(Movie)
    movie_count = session.execute(movie_count_stmt).scalar()

    print(f'There are {movie_count} movies in the database')

    if movie_count == 0:
        for _, row in movie_df.iterrows():
            items_to_add.append(Movie(id=row['movieId'], title=row['title'], genres=row['genres']))

            if len(items_to_add) > 100:
                save_to_db(session, items_to_add)
                items_to_add.clear()

        if len(items_to_add) > 100:
            save_to_db(session, items_to_add)
            items_to_add.clear()
    else:
        print('Movies already added, skipping')

    print('Adding ratings')
    rating_df = pd.read_csv('data/ratings.csv')

    rating_count_stmt = select(func.count()).select_from(Rating)
    rating_count = session.execute(rating_count_stmt).scalar()

    print(f'There are {rating_count} ratings in the database')

    if rating_count == 0:
        for _, row in rating_df.iterrows():
            items_to_add.append(Rating(user_id=row['userId'], movie_id=row['movieId'], rating=row['rating']))

            if len(items_to_add) > 100:
                save_to_db(session, items_to_add)
                items_to_add.clear()

        if len(items_to_add) > 100:
            save_to_db(session, items_to_add)
            items_to_add.clear()
    else:
        print('Ratings already added, skipping')
