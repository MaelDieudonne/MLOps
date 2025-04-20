import os
import random
import streamlit as st
import time

from PIL import Image
from src.utils.db import PostgreSQLDatabase
from src.utils.logger import setup_logging, get_frontend_logger
from src.utils.s3 import s3

setup_logging()
logger = get_frontend_logger()

st.set_page_config(layout="wide")
st.title("🎬 Movie search")

# Setup S3 client
s3 = s3()

@st.cache_data
def get_movie_titles():
    with PostgreSQLDatabase() as db:
        result = db.query_raw("SELECT movie_id, title FROM movies")
        return result

def get_random_movies(n=3):
    movie_list = get_movie_titles()
    return random.sample(movie_list, k=min(n, len(movie_list)))

# Load all movie titles once
movie_list = get_movie_titles()


# -----------------------------
# 🔎 Search functionality
# -----------------------------
search_query = st.text_input("Search with movie title")

if search_query:
    filtered = [movie for movie in movie_list if search_query.lower() in movie[1].lower()]
    if filtered:
        for movie_id, title in filtered:
            s3.retrieve_cover(movie_id)
            if st.button(f"See {title}"):
                st.session_state["selected_movie"] = movie_id
                st.switch_page("pages/dashboard.py")
    else:
        st.warning("No movie found.")


# -----------------------------
# 🎲 Random picks
# -----------------------------
st.subheader("🎲 Random Picks")

cols = st.columns(3)
random_movies = get_random_movies()

for i, (movie_id, title) in enumerate(random_movies):
    s3.retrieve_cover(movie_id)
    cover_path = f"data/covers/{movie_id}.jpg"

    with cols[i]:
        if os.path.exists(cover_path):
            img = Image.open(cover_path)
            st.image(img, caption=title, use_container_width=True)
            if st.button(f"▶️ Select {title}", key=f"btn_{movie_id}"):
                with st.spinner("Loading movie..."):
                    st.session_state["selected_movie"] = movie_id
                    time.sleep(2)  # 500 ms de pause pour eviter un flash
                    st.switch_page("pages/dashboard.py")
        else:
            st.warning(f"No cover for {title}")
