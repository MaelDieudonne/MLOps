import streamlit as st
from src.utils.db import PostgreSQLDatabase
from src.utils.logger import setup_logging, get_frontend_logger
import random
import os
from PIL import Image

setup_logging()
logger = get_frontend_logger()

st.set_page_config(layout="wide")
st.title("🎬 Movie search")

@st.cache_data
def get_movie_titles():
    with PostgreSQLDatabase() as db:
        result = db.query_raw("SELECT movie_id, title FROM movies")
        return result

search_query = st.text_input("Search with movie title")

if search_query:
    movie_list = get_movie_titles()
    filtered = [movie for movie in movie_list if search_query.lower() in movie[1].lower()]

    if filtered:
        for movie_id, title in filtered:
            if st.button(f"See {title}"):
                st.session_state["selected_movie"] = movie_id
                st.switch_page("pages/dashboard.py")
    else:
        st.warning("No movie found.")

st.subheader("🎲 Random Picks")

@st.cache_data
def get_random_movies(n=3):
    movie_list = get_movie_titles()
    return random.sample(movie_list, k=min(n, len(movie_list)))

# Layout en colonnes pour l'affichage
cols = st.columns(3)
random_movies = get_random_movies()

for i, (movie_id, title) in enumerate(random_movies):
    cover_path = f"data/covers/{movie_id}.jpg"
    if os.path.exists(cover_path):
        img = Image.open(cover_path)
        with cols[i]:
            st.image(img, caption=title, use_column_width=True)
            if st.button(f"▶️ Select {title}", key=f"btn_{movie_id}"):
                st.session_state["selected_movie"] = movie_id
                st.switch_page("pages/dashboard.py")
    else:
        with cols[i]:
            st.warning(f"No cover for {title}")

