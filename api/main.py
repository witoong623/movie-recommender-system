from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from common.models import create_session, Rating, Movie
from recommender.base import Recommender
from recommender.item_based_cf import ItemBasedCF


LIMIT = 20
recommend_engine: Recommender = None


def get_db():
    session = create_session()
    try:
        yield session
    finally:
        session.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global recommend_engine
    recommend_engine = ItemBasedCF()
    try:
        yield
    finally:
        recommend_engine = None


app = FastAPI(lifespan=lifespan)


@app.get("/recommendations")
def get_recommendations(user_id: int, returnMetadata: bool=False,
                        db: Session=Depends(get_db)):
    user_exist = db.execute(select(exists().where(Rating.user_id == user_id))).scalar()
    if not user_exist:
        raise HTTPException(status_code=404, detail="User not found")

    predicted_rating = recommend_engine.get_recommended_movies(user_id, LIMIT)

    if returnMetadata:
        stmt = select(Movie).where(Movie.id.in_([movie_id for movie_id, _ in predicted_rating]))
        ret = db.execute(stmt)
        predicted_rating = dict(predicted_rating)
        to_sort_objs = [(movie, predicted_rating[movie.id]) for movie in ret.scalars()]
        sorted_movies = sorted(to_sort_objs, key=lambda x: x[1], reverse=True)
        returned_obj = {'items': [{'id': movie.id, 'title': movie.title, 'genres': movie.genres.split('|')} for movie, _ in sorted_movies]}
    else:
        returned_obj = {'items': [{'id': movie_id} for movie_id, _ in predicted_rating]}

    return returned_obj


@app.get('/features')
def get_features(user_id: int, db: Session=Depends(get_db)):
    user_exist = db.execute(select(exists().where(Rating.user_id == user_id))).scalar()
    if not user_exist:
        raise HTTPException(status_code=404, detail="User not found")

    stmt = select(Rating).where(Rating.user_id == user_id)
    ret = db.execute(stmt)
    watched_movies = [rating.movie_id for rating in ret.scalars()]

    return {'features': [{'histories': watched_movies}]}
