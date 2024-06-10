import os

from sqlalchemy import create_engine, String, LargeBinary, Float, Integer
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column


DB_URL = os.getenv("DB_URL", "sqlite:///./sql_app.db")

connect_args = {}
if DB_URL.startswith("sqlite"):
    connect_args.update({"check_same_thread": False})

engine = create_engine(
    DB_URL, connect_args=connect_args, pool_recycle=3600
)
create_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

class Rating(Base):
    __tablename__ = "rating"

    id = mapped_column(Integer, primary_key=True)
    user_id = mapped_column(Integer)
    movie_id = mapped_column(Integer)
    rating = mapped_column(Float)


class Movie(Base):
    __tablename__ = "movie"

    id = mapped_column(Integer, primary_key=True)
    title = mapped_column(String)
    genres = mapped_column(String)


Base.metadata.create_all(bind=engine)
