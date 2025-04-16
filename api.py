# Base api that can be launched with: uvicorn api:app --reload
# And accessed from the terminal with: curl http://127.0.0.1:8000/movies/tt0029583

from fastapi import FastAPI, HTTPException
from src.utils.db import PostgreSQLDatabase


app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/movies/{movie_id}")
def get_movie(movie_id: str):
    try:
        with PostgreSQLDatabase() as db:
            metadata = db.query_data("movies", condition=f"movie_id = '{movie_id}'")
        if not metadata:
            raise HTTPException(status_code=404, detail="Movie not found")
        return {"movie": metadata}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))