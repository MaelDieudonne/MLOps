import base64
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import os
import pandas as pd
import streamlit as st
from io import BytesIO
from src.utils.db import PostgreSQLDatabase
from src.utils.logger import setup_logging, get_frontend_logger

with open('deployment/user.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)
try:
    authenticator.login()
except Exception as e:
    st.error(e)

setup_logging()
logger = get_frontend_logger()



if "selected_movie" not in st.session_state:
    st.warning("Please choose a movie first.")
    st.stop()

movie_id = st.session_state["selected_movie"]

st.set_page_config(layout="wide")

with PostgreSQLDatabase() as db:
    logger.info("Connexion à la base de données PostgreSQL établie.")

    movie_data = db.query_movie(movie_id)
    data_columns = ['movie_id', 'title', 'release_date']
    df_data = pd.DataFrame(movie_data, columns=data_columns)

    logger.info(f"{len(movie_data)} enregistrements récupérés depuis la table 'movies' pour le movie_id '{movie_id}'.")

    sentiments = db.query_sents(movie_id)
    logger.info(f"{len(sentiments)} entrées récupérées depuis la table 'reviews_sentiments'.")

    # Création du DataFrame sentiments
    sents_columns = ['id','story', 'acting', 'visuals', 'sounds', 'values', 'overall','date','rating']
    df_sents = pd.DataFrame(sentiments, columns=sents_columns)
    logger.info(f"DataFrame des sentiments créé avec {df_sents.shape[0]} lignes et {df_sents.shape[1]} colonnes.")

cols = ['story', 'acting', 'visuals', 'sounds', 'values', 'overall']
averages = df_sents[cols].mean(skipna=True).tolist()
movie_title = movie_data[0][1]  # Le titre du film

background_color = '#DCDCDC'

# Ajouter du CSS personnalisé
st.markdown(f"""
    <style>
        /* Réduire les espaces au-dessus du titre */
        .css-1d391kg {{
            margin-top: 0px;
        }}

        /* Réduire l'espace au-dessus du corps principal (contient tout sauf l'en-tête et la barre de déploiement) */
        .main {{
            padding-top: 0px;
        }}

        /* Réduire l'espace de la barre contenant le bouton Deploy */
        header {{
            padding: 0px 0px;
            height: 0px;
        }}

        /* Réduire l'espace en bas de la page */
        .block-container {{
            padding-bottom: 0px;
        }}

        /* Style de fond du dashboard */
        .main .block-container {{
            background-color: {background_color};
        }}
    </style>
""", unsafe_allow_html=True)


# Ajout de marges vides de chaque côté
# Première ligne : colonnes vides et titre, nb reviews
empty_col10, main_col11, empty_col12, main_col13, empty_col14 = st.columns([3, 3, 4, 3, 3])  # Colonnes avec marges vides

with main_col11:
    st.markdown(f"<h1 style='text-align: center;'>{movie_title}</h1>", unsafe_allow_html=True)

with main_col13:
    review_count = df_sents.shape[0]
    st.markdown(f"<h2 style='text-align: center;'>{review_count} reviews</h2>", unsafe_allow_html=True)

# Deuxième ligne : image et radar
empty_col20, main_col21, empty_col22, main_col23, empty_col24 = st.columns([2, 5, 1, 5, 2])  # Colonnes avec marges vides

with main_col21:
    # Section 1 - Image
    cover_path = f"data/covers/{movie_id}.jpg"
    if os.path.exists(cover_path):
        img = Image.open(cover_path)
        st.image(img, width=330)
    else:
        st.warning("Cover not found")

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
    ax.set_facecolor(background_color)  # Fond du graphique radar
    fig.patch.set_facecolor(background_color)  # Fond autour du graphique

    ax.plot(angles, notes, 'o-', linewidth=2, color='blue')
    ax.fill(angles, notes, alpha=0.25, color='blue')

    # Cercle pour la note générale
    theta = np.linspace(0, 2 * np.pi, 100)
    r = np.full_like(theta, note_generale)
    ax.plot(theta, r, color='red', alpha=0.4)

    # Label rouge en haut du cercle
    ax.text(3 * np.pi / 5, note_generale + 0.35, 'Overall rating', ha='center', color='red', fontsize=12)

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
    # st.pyplot(fig)

    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', transparent=True)
    buf.seek(0)

    # Display centered using markdown
    st.markdown(
        f"""
        <div style="display: flex; justify-content: center;">
            <img src="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}" />
        </div>
        """,
        unsafe_allow_html=True
    )

# Troisième ligne : release date et rating
empty_col30, main_col31, empty_col32, main_col33, empty_col34 = st.columns([1, 3, 2, 3, 1])  # Colonnes avec marges vides

with main_col31:
    # st.title(f"Release date: {pd.to_datetime(df_data['release_date'].iloc[0]).strftime('%Y-%m-%d')}")
    release_date = pd.to_datetime(df_data['release_date'].iloc[0]).strftime('%Y-%m-%d')
    st.markdown(f"<h2 style='text-align: center;'>Release date: {release_date}</h2>", unsafe_allow_html=True)

with main_col33:
    # st.title(f"Overall sentiment: {(round(averages[5], 2}")
    avg_rating = round(averages[5], 2)
    st.markdown(f"<h2 style='text-align: center;'>Average rating {avg_rating}</h2>", unsafe_allow_html=True)

# Quatrième ligne : publication date
empty_col40, main_col41, empty_col42 = st.columns([1, 7, 1])  # Colonnes avec marges vides

with main_col41:
    # Créer les 20 intervalles de temps
    bins = pd.date_range(start=df_sents['date'].min(), end=df_sents['date'].max(), periods=21)

    # Couper les dates en bins
    df_sents['date_bin'] = pd.cut(df_sents['date'], bins=bins)

    # Compter le nombre de lignes par bin
    hist_data = df_sents['date_bin'].value_counts().sort_index()

    # Tracer l'histogramme
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.bar(range(len(hist_data)), hist_data.values, color='#0063B2FF')
    ax.set_facecolor(background_color)
    fig.patch.set_facecolor(background_color)
    ax.set_xticks(range(len(hist_data)))
    ax.set_xticklabels([str(interval.left.date()) for interval in hist_data.index], rotation=45, ha='right', color='#0063B2FF')
    ax.set_title("Number of published reviews", color='#0063B2FF')
    ax.tick_params(colors='#0063B2FF')
    ax.xaxis.label.set_color('#0063B2FF')
    ax.yaxis.label.set_color('#0063B2FF')
    ax.title.set_color('#0063B2FF')
    for spine in ax.spines.values():
        spine.set_edgecolor('#2e2e2e')

    st.pyplot(fig)

# Cinquième ligne : publication date
empty_col50, main_col51, empty_col52 = st.columns([1, 7, 1])  # Colonnes avec marges vides

with main_col51:
    # S'assurer que la colonne date est bien en datetime
    df_sents['date'] = pd.to_datetime(df_sents['date'])

    # Supprimer les lignes où 'rating' est NaN
    df_valid = df_sents.dropna(subset=['rating'])

    # Créer 20 intervalles temporels équidistants
    bins = pd.date_range(start=df_valid['date'].min(), end=df_valid['date'].max(), periods=21)

    # Découper les dates en intervalles
    df_valid['interval'] = pd.cut(df_valid['date'], bins=bins, include_lowest=True)

    # Calculer la moyenne des notes 'rating' pour chaque intervalle
    grouped = df_valid.groupby('interval')['rating'].mean()

    # Tracer l’histogramme
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.bar(grouped.index.astype(str), grouped.values - (-2), color='#0063B2FF', width=0.8)

    # Axe x formaté avec dates lisibles
    ax.set_xticks(range(len(grouped)))
    ax.set_xticklabels(
        [str(interval.left.date()) for interval in grouped.index],
        rotation=45,
        ha='right',
        fontsize=8
    )

    # Style du graphique
    ax.set_title("Average rating per time periods", color='#0063B2FF')
    ax.set_facecolor(background_color)
    fig.patch.set_facecolor(background_color)
    ax.tick_params(colors='#0063B2FF')
    ax.xaxis.label.set_color('#0063B2FF')
    ax.yaxis.label.set_color('#0063B2FF')
    ax.title.set_color('#0063B2FF')
    ax.set_ylim(0, 10)

    # Bordures
    for spine in ax.spines.values():
        spine.set_edgecolor('#2e2e2e')

    st.pyplot(fig)


# Sixième ligne : publication date
empty_col60, main_col61, main_col62, main_col63, empty_col64 = st.columns([1, 4, 4, 4, 1])  # Colonnes avec marges vides

with main_col61:
    story_bins = [-2.5, -1.5, -0.5, 0.5, 1.5, 2.5]
    story_labels = [-2, -1, 0, 1, 2]
    df_sents['story_cat'] = pd.cut(df_sents['story'], bins=story_bins, labels=story_labels)
    story_counts = df_sents['story_cat'].value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(story_counts.index.astype(str), story_counts.values, color='#6A9148', width=0.6)

    ax.set_title("Ratings for Narrative / Storyline", color='black')
    ax.set_ylabel("Votes", color='#6A9148')
    ax.set_facecolor(background_color)
    fig.patch.set_facecolor(background_color)
    ax.set_ylim(0, story_counts.values.max() + 5)
    ax.tick_params(colors='#6A9148')
    ax.xaxis.label.set_color('#6A9148')
    ax.yaxis.label.set_color('#6A9148')
    ax.title.set_color('#6A9148')
    for spine in ax.spines.values():
        spine.set_edgecolor('#2e2e2e')

    st.pyplot(fig)

with main_col62:
    df_sents['acting_cat'] = pd.cut(df_sents['acting'], bins=story_bins, labels=story_labels)
    story_counts = df_sents['acting_cat'].value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(story_counts.index.astype(str), story_counts.values, color='#588CA5', width=0.6)

    ax.set_title("Ratings for Acting / Performance", color='black')
    ax.set_ylabel("Votes", color='#588CA5')
    ax.set_facecolor(background_color)
    fig.patch.set_facecolor(background_color)
    ax.set_ylim(0, story_counts.values.max() + 5)
    ax.tick_params(colors='#588CA5')
    ax.xaxis.label.set_color('#588CA5')
    ax.yaxis.label.set_color('#588CA5')
    ax.title.set_color('#588CA5')
    for spine in ax.spines.values():
        spine.set_edgecolor('#2e2e2e')

    st.pyplot(fig)

with main_col63:
    df_sents['visuals_cat'] = pd.cut(df_sents['visuals'], bins=story_bins, labels=story_labels)
    story_counts = df_sents['visuals_cat'].value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(story_counts.index.astype(str), story_counts.values, color='#C88D7B', width=0.6)

    ax.set_title("Ratings for Visuals / Cinematography", color='black')
    ax.set_ylabel("Votes", color='#C88D7B')
    ax.set_facecolor(background_color)
    fig.patch.set_facecolor(background_color)
    ax.set_ylim(0, story_counts.values.max() + 5)
    ax.tick_params(colors='#C88D7B')
    ax.xaxis.label.set_color('#C88D7B')
    ax.yaxis.label.set_color('#C88D7B')
    ax.title.set_color('#C88D7B')
    for spine in ax.spines.values():
        spine.set_edgecolor('#2e2e2e')

    st.pyplot(fig)

# Ligne suivante
empty_col70, main_col71, main_col72, empty_col73 = st.columns([3, 4, 4, 3])

with main_col71:
    df_sents['sounds_cat'] = pd.cut(df_sents['sounds'], bins=story_bins, labels=story_labels)
    story_counts = df_sents['sounds_cat'].value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(story_counts.index.astype(str), story_counts.values, color='#B8860B', width=0.6)

    ax.set_title("Ratings for Music / Sounds", color='black')
    ax.set_ylabel("Votes", color='#B8860B')
    ax.set_facecolor(background_color)
    fig.patch.set_facecolor(background_color)
    ax.set_ylim(0, story_counts.values.max() + 5)
    ax.tick_params(colors='#B8860B')
    ax.xaxis.label.set_color('#B8860B')
    ax.yaxis.label.set_color('#B8860B')
    ax.title.set_color('#B8860B')
    for spine in ax.spines.values():
        spine.set_edgecolor('#2e2e2e')

    st.pyplot(fig)

with main_col72:
    df_sents['values_cat'] = pd.cut(df_sents['values'], bins=story_bins, labels=story_labels)
    story_counts = df_sents['values_cat'].value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(story_counts.index.astype(str), story_counts.values, color='#68228B', width=0.6)

    ax.set_title("Ratings for Values / Entertainment", color='black')
    ax.set_ylabel("Votes", color='#68228B')
    ax.set_facecolor(background_color)
    fig.patch.set_facecolor(background_color)
    ax.set_ylim(0, story_counts.values.max() + 5)
    ax.tick_params(colors='#68228B')
    ax.xaxis.label.set_color('#68228B')
    ax.yaxis.label.set_color('#68228B')
    ax.title.set_color('#68228B')
    for spine in ax.spines.values():
        spine.set_edgecolor('#2e2e2e')

    st.pyplot(fig)