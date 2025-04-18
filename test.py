import os
import pandas as pd

from src.utils.db import PostgreSQLDatabase

with PostgreSQLDatabase() as db:
    movies = db.query_data('movies')
print(movies)