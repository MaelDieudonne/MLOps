import numpy as np
import pandas as pd
from src.utils.db import PostgreSQLDatabase
import sys
import json

movie_id = sys.argv[1]

with PostgreSQLDatabase() as db:
    movie_data = db.query_data("movies", condition=f"movie_id = '{movie_id}'")
    movie_review = db.query_data("reviews_raw", condition=f"movie_id = '{movie_id}'")
    review_columns = [desc[0] for desc in db.cursor.description]
    df_reviews = pd.DataFrame(movie_review, columns=review_columns)

    review_ids = df_reviews['review_id'].tolist()
    review_ids_sql = ",".join([f"'{r}'" for r in review_ids])

    sentiments = db.query_data("reviews_sentiments", condition=f"review_id IN ({review_ids_sql})")
    sents_columns = [desc[0] for desc in db.cursor.description]
    df_sents = pd.DataFrame(sentiments, columns=sents_columns)
    df_merged = df_reviews.merge(df_sents, on="review_id", how="left")

cols = ['story', 'acting', 'visuals', 'sounds', 'values', 'overall']
averages = df_merged[cols].mean(skipna=True)

# Liste de 7 éléments
data = averages.tolist() + [movie_data[0][1]] + [movie_data[0][2].year]

# Sauvegarder la liste dans un fichier JSON
with open('data/data.json', 'w') as f:
    json.dump(data, f)