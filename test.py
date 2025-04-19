import os
import pandas as pd

from src.utils.db import PostgreSQLDatabase

movie_id = "tt6208148"

with PostgreSQLDatabase() as db:
    # 1. Récupérer les reviews pour un film donné
    movie_review = db.query_data("reviews_raw", condition=f"movie_id = '{movie_id}'")

    # 2. Convertir en DataFrame
    review_columns = [desc[0] for desc in db.cursor.description]
    df_reviews = pd.DataFrame(movie_review, columns=review_columns)
    print(df_reviews)

    # 3. Extraire les review_id
    review_ids = df_reviews['review_id'].tolist()
    review_ids_sql = ",".join([f"'{r}'" for r in review_ids])

    # 4. Requête sur les sentiments pour les review_ids
    sentiments = db.query_data("reviews_sentiments", condition=f"review_id IN ({review_ids_sql})")
    sents_columns = [desc[0] for desc in db.cursor.description]
    df_sents = pd.DataFrame(sentiments, columns=sents_columns)

    # 5. Merger les deux DataFrames sur review_id
    df_merged = df_reviews.merge(df_sents, on="review_id", how="left")

# 6. Afficher les 3 premières lignes
print(df_merged)
print(df_merged.columns)

cols = ['story', 'acting', 'visuals', 'sounds', 'values', 'overall']
averages = df_merged[cols].mean(skipna=True)

print(averages)

import matplotlib.pyplot as plt

# Création de l'histogramme avec 20 intervalles (bins)
plt.figure(figsize=(12, 4))
plt.hist(df_merged['date'], bins=20, color='skyblue', edgecolor='black')
plt.xlabel("Date")
plt.ylabel("Nombre de lignes")
plt.title("Distribution des reviews dans le temps")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("test.png", dpi=300)
plt.close()
