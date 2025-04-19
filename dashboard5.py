import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.interpolate import CubicSpline
from scipy.signal import savgol_filter
from src.utils.db import PostgreSQLDatabase
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor
import asyncio
import logging
import os

st.set_page_config(layout="wide")

# Ton movie_id (à ajuster selon l'utilisateur ou la logique de ton app)
movie_id = "tt6208148"

# Configure logging
# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

with PostgreSQLDatabase() as db:
    logging.info("Connexion à la base de données PostgreSQL établie.")

    # Récupération des données du film
    movie_data = db.query_data("movies", condition=f"movie_id = '{movie_id}'")
    data_columns = ['movie_id','title','release_date','nb_reviews','scrapping_timestamp']
    df_data = pd.DataFrame(movie_data, columns=data_columns)
    logging.info(f"{len(movie_data)} enregistrements récupérés depuis la table 'movies' pour le movie_id '{movie_id}'.")

    query = f"""
        SELECT s.review_id, s.story, s.acting, s.visuals, s.sounds, s.values, s.overall, r.date
        FROM reviews_sentiments s
        JOIN reviews_raw r ON s.review_id = r.review_id
        WHERE r.movie_id = '{movie_id}'
    """
    
    sentiments = db.query_raw(query)
    logging.info(f"{len(sentiments)} entrées récupérées depuis la table 'reviews_sentiments'.")

    # Création du DataFrame sentiments
    sents_columns = ['id','story', 'acting', 'visuals', 'sounds', 'values', 'overall','date']
    df_sents = pd.DataFrame(sentiments, columns=sents_columns)
    logging.info(f"DataFrame des sentiments créé avec {df_sents.shape[0]} lignes et {df_sents.shape[1]} colonnes.")

cols = ['story', 'acting', 'visuals', 'sounds', 'values', 'overall']
averages = df_sents[cols].mean(skipna=True).tolist()
movie_title = movie_data[0][1]  # Le titre du film
movie_year = movie_data[0][2]  # L'année du film

# Ajouter du CSS personnalisé
st.markdown("""
    <style>
        /* Réduire les espaces au-dessus du titre */
        .css-1d391kg {
            margin-top: 0px;
        }

        /* Réduire l'espace au-dessus du corps principal (contient tout sauf l'en-tête et la barre de déploiement) */
        .main {
            padding-top: 0px;
        }

        /* Réduire l'espace de la barre contenant le bouton Deploy */
        header {
            padding: 0px 0px;
            height: 0px;  /* Ajustez la hauteur de la barre en fonction de vos besoins */
        }

        /* Réduire l'espace en bas de la page */
        .block-container {
            padding-bottom: 0px;
        }

        /* Style de fond du dashboard */
        .main .block-container {
            background-color: #0d0f14;  /* Couleur de fond gris foncé */
        }
    </style>
""", unsafe_allow_html=True)

# Ajout de marges vides de chaque côté
# Première ligne : colonnes vides et titre, nb reviews
empty_col10, main_col11, empty_col12, main_col13, empty_col14 = st.columns([3, 3, 6, 3, 3])  # Colonnes avec marges vides

with main_col11:
    st.title(movie_title)

with main_col13:
    st.title(str(df_sents.shape[0])+" reviews")

# Deuxième ligne : image et radar
empty_col20, main_col21, empty_col22, main_col23, empty_col24 = st.columns([3, 5, 1, 5, 3])  # Colonnes avec marges vides

with main_col21:
    # Section 1 - Image
    st.image(f"data/covers/{movie_id}.jpg", width=330)
    
with main_col23:
    # Section 2 - Radar avec les évaluations du film
    labels = ['story', 'acting', 'visuals', 'sounds', 'values']
    notes = averages[:5].copy()  # Valeurs pour les différentes catégories
    note_generale = averages[5]  # Note générale du film

    # Boucle pour fermer le radar
    labels += [labels[0]]
    notes += [notes[0]]

    # Angles pour chaque label
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=True).tolist()

    # Création du graphique radar
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))

    # Appliquer le même fond que les autres graphiques
    ax.set_facecolor('#0d0f14')  # Fond du graphique radar
    fig.patch.set_facecolor('#0d0f14')  # Fond autour du graphique

    ax.plot(angles, notes, 'o-', linewidth=2, color='blue')
    ax.fill(angles, notes, alpha=0.25, color='blue')

    # Cercle pour la note générale
    theta = np.linspace(0, 2 * np.pi, 100)
    r = np.full_like(theta, note_generale)
    ax.plot(theta, r, color='red', alpha=0.4)

    # Label rouge en haut du cercle
    ax.text(3 * np.pi / 5, note_generale + 0.3, 'Note générale', ha='center', color='red', fontsize=12)

    # Affichage des lignes radiales mais sans leurs labels
    angle_degrees = np.degrees(angles[:-1])
    ax.set_thetagrids(angle_degrees, labels=[''] * len(angle_degrees))  # Vide les labels

    # Ajouter les labels manuellement avec un décalage radial
    label_offset = 2.6
    for angle, label in zip(angles[:-1], labels[:-1]):
        ax.text(angle, label_offset, label, ha='center', va='center', fontsize=10, color='white')

    # Ajustement des axes
    ax.set_ylim(-2, 2)
    ax.set_yticks([-2, -1, 0, 1, 2])
    ax.set_yticklabels(['-2', '-1', '0', '1', '2'], color='white')

    # Mettre la bordure extérieure du cercle en blanc
    ax.spines['polar'].set_visible(True)
    ax.spines['polar'].set_color('white')  # Cercle extérieur en blanc

    # Affichage du graphique dans Streamlit
    st.pyplot(fig)

# Troisième ligne : release date et rating
empty_col30, main_col31, empty_col32, main_col33, empty_col34 = st.columns([2, 3, 4, 3, 2])  # Colonnes avec marges vides

with main_col31:
    st.title(str(df_data['release_date']))

with main_col33:
    st.title("Note : "+str(round(averages[5], 2)))

# Quatrième ligne : publication date
empty_col40, main_col41, empty_col42 = st.columns([2, 7, 2])  # Colonnes avec marges vides

with main_col41:
    # Créer les 20 intervalles de temps
    bins = pd.date_range(start=df_sents['date'].min(), end=df_sents['date'].max(), periods=21)
    
    # Couper les dates en bins
    df_sents['date_bin'] = pd.cut(df_sents['date'], bins=bins)
    
    # Compter le nombre de lignes par bin
    hist_data = df_sents['date_bin'].value_counts().sort_index()
    
    # Tracer l'histogramme
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(hist_data.index.astype(str), hist_data.values, color='white')
    ax.set_xticks(range(len(hist_data)))
    ax.set_xticklabels([str(interval.left.date()) for interval in hist_data.index], rotation=45, ha='right')
    ax.set_title("Nombre de lignes par période de temps")
    ax.set_ylabel("Nombre de lignes")
    ax.set_xlabel("Intervalle de dates")
    ax.set_facecolor('#0d0f14')  # Fond du graphique
    plt.tight_layout()
    plt.show()

# Deuxième ligne : colonnes vides et colonnes principales
empty_col3, main_col3bis, empty_col5, main_col4, empty_col4 = st.columns([4, 9, 3, 12, 4])  # Colonnes avec marges vides

with main_col3bis:
    # Graphique 1 : Moyenne mobile lissée du nombre de ratings par jour
    # Exécution sur un jeu de données fictif
    dates = pd.date_range("20230101", periods=100)
    ratings = np.random.randint(1, 6, 100)
    movie_id_selected = 1
    df_movie = pd.DataFrame({"date": dates, "rating": ratings, "movie_id": [movie_id_selected]*100})

    # Nombre de ratings par jour
    daily_counts = df_movie.groupby('date').size().sort_index()

    # Déterminer la taille de la fenêtre pour la moyenne mobile
    window_size = int((daily_counts.index[-1] - daily_counts.index[0]).days / 40)

    # Calculer la moyenne mobile du nombre de ratings
    rolling_avg_counts = daily_counts.rolling(window=window_size).mean()

    # Appliquer un filtre Savitzky-Golay pour un lissage supplémentaire (optionnel)
    smoothed_rolling_avg_counts = savgol_filter(rolling_avg_counts.dropna(), window_length=31, polyorder=3)

    # Supprimer les valeurs NaN avant de faire l'interpolation
    valid_indices_counts = ~np.isnan(smoothed_rolling_avg_counts)  # Trouver les indices valides
    x_counts = np.arange(len(smoothed_rolling_avg_counts))[valid_indices_counts]  # Index des données valides
    y_counts = smoothed_rolling_avg_counts  # Moyenne mobile sans NaN

    # Créer une spline cubique pour lisser la moyenne mobile du nombre de ratings
    cs_counts = CubicSpline(x_counts, y_counts)

    # Générer des points lissés pour le nombre de ratings
    x_new_counts = np.linspace(0, len(smoothed_rolling_avg_counts)-1, 1000)  # Augmenter le nombre de points
    y_new_counts = cs_counts(x_new_counts)

    # Tracer le graphique
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.set_facecolor('#0d0f14')  # Fond du graphique
    fig.patch.set_facecolor('#0d0f14')  # Fond autour du graphique
    ax.plot(daily_counts.index[x_new_counts.astype(int)], y_new_counts, color='blue', label='Spline cubique lissée')
    ax.fill_between(daily_counts.index[x_new_counts.astype(int)], y_new_counts, color='blue', alpha=0.3)  # Aire colorée sous la courbe
    ax.set_title('Moyenne mobile lissée du nombre de ratings', color='white')
    ax.set_xlabel('Date', color='white')
    ax.set_ylabel('Nombre de ratings', color='white')

    # Couleur du texte
    ax.tick_params(colors='white')  # Couleur des ticks
    ax.xaxis.label.set_color('white')  # Label X
    ax.yaxis.label.set_color('white')  # Label Y
    ax.title.set_color('white')  # Titre

    # Bordures des axes (spines)
    for spine in ax.spines.values():
        spine.set_edgecolor('#2e2e2e')

    st.pyplot(fig)

with main_col4:
    # Graphique 2 : Moyenne mobile lissée des ratings par jour
    # Moyenne des valeurs des ratings par jour
    daily_avg_ratings = df_movie.groupby('date')['rating'].mean().sort_index()

    # Calculer la moyenne mobile des valeurs des ratings
    rolling_avg_ratings = daily_avg_ratings.rolling(window=window_size).mean()

    # Appliquer un filtre Savitzky-Golay pour un lissage supplémentaire (optionnel)
    smoothed_rolling_avg_ratings = savgol_filter(rolling_avg_ratings.dropna(), window_length=31, polyorder=3)

    # Supprimer les valeurs NaN avant de faire l'interpolation
    valid_indices_ratings = ~np.isnan(smoothed_rolling_avg_ratings)  # Trouver les indices valides
    x_ratings = np.arange(len(smoothed_rolling_avg_ratings))[valid_indices_ratings]  # Index des données valides
    y_ratings = smoothed_rolling_avg_ratings  # Moyenne mobile sans NaN

    # Créer une spline cubique pour lisser la moyenne mobile des ratings
    cs_ratings = CubicSpline(x_ratings, y_ratings)

    # Générer des points lissés pour la moyenne des ratings
    x_new_ratings = np.linspace(0, len(smoothed_rolling_avg_ratings)-1, 1000)  # Augmenter le nombre de points
    y_new_ratings = cs_ratings(x_new_ratings)

    # Tracer le graphique
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.set_facecolor('#0d0f14')  # Fond du graphique
    fig.patch.set_facecolor('#0d0f14')  # Fond autour du graphique
    ax.plot(daily_avg_ratings.index[x_new_ratings.astype(int)], y_new_ratings, color='blue', label='Spline cubique lissée')
    ax.fill_between(daily_avg_ratings.index[x_new_ratings.astype(int)], y_new_ratings, color='blue', alpha=0.3)  # Aire colorée sous la courbe
    ax.set_title('Moyenne mobile lissée des ratings', color='white')
    ax.set_xlabel('Date', color='white')
    ax.set_ylabel('Moyenne des ratings', color='white')

    # Couleur du texte
    ax.tick_params(colors='white')  # Couleur des ticks
    ax.xaxis.label.set_color('white')  # Label X
    ax.yaxis.label.set_color('white')  # Label Y
    ax.title.set_color('white')  # Titre

    # Bordures des axes (spines)
    for spine in ax.spines.values():
        spine.set_edgecolor('#2e2e2e')

    st.pyplot(fig)
