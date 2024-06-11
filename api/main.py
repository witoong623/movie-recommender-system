from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from common.models import create_session, Rating
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
    
    recommended_movies = recommend_engine.get_recommended_movies(user_id, LIMIT)
    return {'items': [{'id': movie_id} for movie_id, _ in recommended_movies]}


@app.get('/features')
def get_features(user_id: int, db: Session=Depends(get_db)):
    stmt = select(Rating).where(Rating.user_id == user_id)
    ret = db.execute(stmt)
    watched_movies = [rating.movie_id for rating in ret.scalars()]

    return {'features': [{'histories': watched_movies}]}
