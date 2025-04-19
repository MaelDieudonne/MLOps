import pandas as pd

from fastapi import FastAPI, HTTPException
from src.utils.db import PostgreSQLDatabase
from src.utils.logger import setup_logging, get_frontend_logger

setup_logging()
logger = get_frontend_logger()

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def read_root():
    """
    Movie Reviews Analysis API
    
    This API provides access to movie metadata and sentiment analysis of reviews.
    
    Available endpoints:
    - /movies/{movie_id}: Get basic movie metadata
    - /movies/{movie_id}/stats: Get detailed sentiment analysis of movie reviews

    Sample movie_ids: tt0029583, tt6208148
    """
    return {
        "name": "Movie Reviews Analysis API",
        "version": "1.0.0",
        "description": "API for accessing movie metadata and sentiment analysis of reviews",
        "endpoints": {
            "movies": "/movies/{movie_id}",
            "movie_stats": "/movies/{movie_id}/stats"},
        "Sample movie_ids": {
            "Snow White": "tt6208148",
            "Snow White and the Seven Dwarfs": "tt0029583"}
    }


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


@app.get("/movies/{movie_id}/stats")
def get_movie_stats(movie_id: str):
    try:
        query = """
            SELECT 
                m.movie_id,
                m.title,
                m.release_date,
                m.nb_reviews,
                -- Story sentiment
                AVG(rs.story) AS avg_story,
                COUNT(CASE WHEN rs.story = -2 THEN 1 END) AS story_neg2,
                COUNT(CASE WHEN rs.story = -1 THEN 1 END) AS story_neg1,
                COUNT(CASE WHEN rs.story = 0 THEN 1 END) AS story_0,
                COUNT(CASE WHEN rs.story = 1 THEN 1 END) AS story_pos1,
                COUNT(CASE WHEN rs.story = 2 THEN 1 END) AS story_pos2,
                COUNT(CASE WHEN rs.story IS NULL THEN 1 END) AS story_null,
                -- Acting sentiment
                AVG(rs.acting) AS avg_acting,
                COUNT(CASE WHEN rs.acting = -2 THEN 1 END) AS acting_neg2,
                COUNT(CASE WHEN rs.acting = -1 THEN 1 END) AS acting_neg1,
                COUNT(CASE WHEN rs.acting = 0 THEN 1 END) AS acting_0,
                COUNT(CASE WHEN rs.acting = 1 THEN 1 END) AS acting_pos1,
                COUNT(CASE WHEN rs.acting = 2 THEN 1 END) AS acting_pos2,
                COUNT(CASE WHEN rs.acting IS NULL THEN 1 END) AS acting_null,
                -- Visuals sentiment
                AVG(rs.visuals) AS avg_visuals,
                COUNT(CASE WHEN rs.visuals = -2 THEN 1 END) AS visuals_neg2,
                COUNT(CASE WHEN rs.visuals = -1 THEN 1 END) AS visuals_neg1,
                COUNT(CASE WHEN rs.visuals = 0 THEN 1 END) AS visuals_0,
                COUNT(CASE WHEN rs.visuals = 1 THEN 1 END) AS visuals_pos1,
                COUNT(CASE WHEN rs.visuals = 2 THEN 1 END) AS visuals_pos2,
                COUNT(CASE WHEN rs.visuals IS NULL THEN 1 END) AS visuals_null,
                -- Sounds sentiment
                AVG(rs.sounds) AS avg_sounds,
                COUNT(CASE WHEN rs.sounds = -2 THEN 1 END) AS sounds_neg2,
                COUNT(CASE WHEN rs.sounds = -1 THEN 1 END) AS sounds_neg1,
                COUNT(CASE WHEN rs.sounds = 0 THEN 1 END) AS sounds_0,
                COUNT(CASE WHEN rs.sounds = 1 THEN 1 END) AS sounds_pos1,
                COUNT(CASE WHEN rs.sounds = 2 THEN 1 END) AS sounds_pos2,
                COUNT(CASE WHEN rs.sounds IS NULL THEN 1 END) AS sounds_null,
                -- Values sentiment
                AVG(rs.values) AS avg_values,
                COUNT(CASE WHEN rs.values = -2 THEN 1 END) AS values_neg2,
                COUNT(CASE WHEN rs.values = -1 THEN 1 END) AS values_neg1,
                COUNT(CASE WHEN rs.values = 0 THEN 1 END) AS values_0,
                COUNT(CASE WHEN rs.values = 1 THEN 1 END) AS values_pos1,
                COUNT(CASE WHEN rs.values = 2 THEN 1 END) AS values_pos2,
                COUNT(CASE WHEN rs.values IS NULL THEN 1 END) AS values_null,
                -- Overall sentiment counts
                AVG(rs.overall) AS avg_overall,
                COUNT(CASE WHEN rs.overall = -2 THEN 1 END) AS overall_neg2,
                COUNT(CASE WHEN rs.overall = -1 THEN 1 END) AS overall_neg1,
                COUNT(CASE WHEN rs.overall = 0 THEN 1 END) AS overall_0,
                COUNT(CASE WHEN rs.overall = 1 THEN 1 END) AS overall_pos1,
                COUNT(CASE WHEN rs.overall = 2 THEN 1 END) AS overall_pos2,
                COUNT(CASE WHEN rs.overall IS NULL THEN 1 END) AS overall_null
            FROM 
                movies m
            LEFT JOIN 
                reviews_raw rr ON m.movie_id = rr.movie_id
            LEFT JOIN 
                reviews_sentiments rs ON rr.author = rs.author
            WHERE 
                m.movie_id = %s
            GROUP BY 
                m.movie_id, m.title, m.release_date, m.nb_reviews
        """
        
        with PostgreSQLDatabase() as db:
            movie_stats = pd.read_sql(query, db.connection, params=(movie_id,))
            
        if movie_stats.empty:
            raise HTTPException(status_code=404, detail="Movie statistics not found")
            
        # Convert DataFrame to dictionary for JSON response
        return {"movie_stats": movie_stats.to_dict(orient="records")[0]}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
