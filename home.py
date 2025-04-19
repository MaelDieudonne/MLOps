import streamlit as st
from src.utils.db import PostgreSQLDatabase  # Assure-toi que ce module est accessible

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
                st.switch_page("pages/dashboard.py")  # Redirige vers le dashboard
    else:
        st.warning("No movie found.")
