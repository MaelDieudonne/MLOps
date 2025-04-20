import os
import pandas as pd

from src.utils.s3 import s3
from src.utils.db import PostgreSQLDatabase


with PostgreSQLDatabase() as db:
    movies = db.query_data('movies')
movies = pd.DataFrame(movies)
column_names = {
    'movie_id': 'VARCHAR(10) PRIMARY KEY',
    'title': 'VARCHAR(250)',
    'release_date': 'DATE',
    'nb_reviews': 'INTEGER',
    'scrapping_timestamp': 'TIMESTAMP'
}
movies.columns = column_names.keys()


with PostgreSQLDatabase() as db:
    reviews_raw = db.query_data('reviews_raw')
reviews_raw = pd.DataFrame(reviews_raw)
column_names = {
    'movie_id': 'VARCHAR(10) REFERENCES movies(movie_id) ON DELETE CASCADE',
    'review_id': 'VARCHAR(10) PRIMARY KEY',
    'author': 'VARCHAR(150)',
    'title': 'VARCHAR(500)',
    'text': 'TEXT',
    'rating': 'INTEGER',
    'date': 'DATE',
    'upvotes': 'INTEGER',
    'downvotes': 'INTEGER',
    'last_update': 'TIMESTAMP',
    'to_process': 'INTEGER'
}
reviews_raw.columns = column_names.keys()


with PostgreSQLDatabase() as db:
    reviews_sentiments = db.query_data('reviews_sentiments')
reviews_sentiments = pd.DataFrame(reviews_sentiments)
column_names = {
    'review_id': 'VARCHAR(10) PRIMARY KEY REFERENCES reviews_raw(review_id) ON DELETE CASCADE',
    'author': 'VARCHAR(150)',
    'story': 'INTEGER',
    'acting': 'INTEGER',
    'visuals': 'INTEGER',
    'sounds': 'INTEGER',
    'values': 'INTEGER',
    'overall': 'INTEGER'
}
reviews_sentiments.columns = column_names.keys()


movies.to_csv("data/sample/movies.csv", index=False)
reviews_raw.to_csv("data/sample/reviews_raw.csv", index=False)
reviews_sentiments.to_csv("data/sample/reviews_sentiments.csv", index=False)
