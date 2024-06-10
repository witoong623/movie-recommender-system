from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends

from recommender.base import Recommender
from recommender.dummy import DummyRecommender


LIMIT = 20
recommend_engine: Recommender = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global recommend_engine
    recommend_engine = DummyRecommender()
    try:
        yield
    finally:
        recommend_engine = None


app = FastAPI(lifespan=lifespan)


@app.get("/recommendations")
def get_recommendations(user_id: int, returnMetadata: bool=False):
    return {'items': [{'id': movie_id} for movie_id in recommend_engine.get_recommended_movies(user_id, LIMIT)]}
