# The IMDb Reviews Tracker
This project tracks the reception of movies based on user reviews published on [IMDb](https://www.imdb.com). It was realised during the [Deployment of Data Science Projects](https://www.ensae.fr/courses/6052-mise-en-production-des-projets-de-data-science) course at ENSAE (see the [companion website](https://ensae-reproductibilite.github.io/website/)).

## 1. Implementation
There are 5 main components:
- ***Dynamic web scraping*** to retrieve reviews dynamically from the IMDb website.
- ***Aspect-based sentiment analysis*** to extract information from the reviews.
- ***API*** to broadcoast the data.
- ***Dashboard*** to present synthetic information on each movie.
- ***User management system*** to mirror a professional environment.

The dashboard can be accessed [here](https://movie-reviews-tracker.lab.sspcloud.fr/) and the API [there](https://api-movie-reviews-tracker.lab.sspcloud.fr/).

Checklist:
- This project is hosted on GitHub, and development has been organized in separate branches.
- The code has been formatted with `Flake8` and cleaned with `vulture`.
- The credentials are managed securely through the DataLab Vault or an `.env` file.
- The code is fully functionalized, modularized, and structured.
- The environment is managed with `poetry` and various install scripts.
- Detailed logs are collected.
- Data is stored externaly on a PostgreSQL database, with with backups as Parquet files on S3.
- Tests are available and integrated into a GitHub workflow.
- The application is containerized with Docker through another GitHub workflow.
- Deployment is straightforward on Kubernetes.
- Deployment is possible (but non-operational regarding credentials) through Argo CD.

Architecture:
<pre>
app/
├── data/
│   ├── backup/
│   ├── covers/    
│   └── sample/
├── deployment/
│   ├── deployment
│   │   ├── api.yaml
│   │   ├── dashboard.yaml
│   │   └── tracker.yaml
│   ├── service
│   │   ├── api.yaml
│   │   └── dashboard.yaml
│   ├── ingress
│   │   └── ingress.yaml
│   └── argo_cd.yaml
├── dev/
│   ├── db_admin_tools.py
│   ├── db_tools.py
│   └── generate_samples.py    
├── doc/
│   └── kubernetes_commands.md    
├── logs/
│   ├── backend.log
│   └── frontend.log
├── pages/
│   └── dashboard.py
├── setup/
│   ├── create_db.sh
│   ├── create_kubectl_secrets.sh
│   ├── db_init.py
│   └── install_dependencies.sh
├── src/
│   ├── analysis.py
│   ├── api.py
│   ├── backup.py
│   ├── manage_movies.py
│   ├── scraping.py
│   └── utils/
│       ├── db.py
│       ├── logger.py
│       └── s3.py
├── test/
│       ├── backup_test.py
│       └── connection_test.py
├── home.py
├── main.py
└── scheduler.py</pre>

## Installation
### In the DataLab (for developpement)
Launch a Postgresql service, then store the corresponding parameters in an `.env` file or the Datalab Vault:
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`

Launch the installation script with `chmod +x ./setup/install_dependencies.sh && source ./setup/install_dependencies.sh`. This script:
1. Installs Chrome
2. Installs Python and dependencies with Poetry
3. Sets up the database (with `setup/db_init.py`)
4. Launches the scheduler to scrap and analyze reviews on a hourly basis (its state can be checked with `pgrep -fl scheduler.py`)

### With Kubernetes (for production)
- Store the `OPENAI_API_KEY` in an `.env` file or the Datalab.
- Launch a Jupyter or VSCode service **with edit rights** (and **access to the vault** if the `OPENAI_API_KEY` is stored there).
- Run `chmod +x ./setup/create_db.sh && source ./setup/create_db.sh` to launch a PostgrelSQL pod with random passwords.
- Run `chmod +x ./setup/create_kubectl_secrets.sh && source ./setup/create_kubectl_secrets.sh` to register the credentials in the Kubernetes environment.
- Run `kubectl apply -R -f deployment/` to deploy 3 separate pods:
  - For scraping and analyzing reviews
  - For the API
  - For the dashboard

### With Docker (for enjoyment)
A `docker-compose.yml` is provided which runs the tracker, the dashboard, the API, and the database as distinct services. The secrets must be set as environment variables, including parameters for the backup on S3 which can be retrieved [here](https://datalab.sspcloud.fr/account/storage). Then with some luck, everything should run...

### Manage movies
They can be added or removed from the terminal with `poetry run python -m src.manage_movies --add '<movie_id_1>' '<movie_id_2>' --remove '<movie_id_3>'` (where `<movie_id>` must be retrieved manually from IMDb, e.g., `tt0033467` for [Citizen Kane](https://www.imdb.com/title/tt0033467/?ref_=fn_all_ttl_1)).

## 2. Technical aspects
### Data management
Data is stored in a PostgreSQL database with 3 tables:
- `movies` contains movie metadata,
- `reviews_raws` contains reviews as scraped,
- `reviews_sentiments` contains the results of sentiment analysis.

These tables are backed-up as `.parquet` in the DataLab with s3. 

A sample with 4 movies is provided.

### Scraping
Data must be collected from three IMDB pages:
- The movie’s main page for metadata, including the total number of reviews.
- The main reviews page, which shows the 25 most popular reviews by default; some reviews are hidden behind `<spoiler>` tags, and vote counts over 999 are rounded.
- Individual review pages, where exact vote counts are displayed.

Interacting with the webpages was necessary:
- To display all reviews on the main reviews page. It turned out the “Show all” button does not actually display all reviews: it stops at the nearest multiple of 25, requiring an additional click on the “Show more” button for remaining reviews.
- To access text hidden behind `<spoiler>` tags, fetching the individual review pages proved more reliable, though slower.

Our scraper therefore uses `selenium` in combination with `Chrome` and `chromedriver-py`.

The scraping process follows these steps:
- Every hour, scrape the main page to retrieve metadata.
- If new reviews have been published, the movie was just added to the database, or the last full scrape is older than 24 hours, scrape the main reviews page.
- If spoiler tags or rounded vote counts are detected, scrape the corresponding individual review pages.
- Update the database tables, flagging reviews as new or edited for sentiment analysis.

A scheduler launches one script per movie every hour, ensuring no more than five movies are scraped concurrently to avoid overloading the system. The database is also backed up hourly. For some movies, small discrepancies were observed between the number of reviews listed on the main page and the number actually scraped from the reviews page. A cursory investigation found no clear explanation. 

### Sentiment analysis
We want to determine the opinions expressed in the reviews regarding 5 main features of the movies:
- *Storytelling* (including characters and their development, narrative progression, plot twists, screenplay, dialogues, overall pacing)
- *Acting performance* (including vocal, musical, danse, or stunt work if applicable)
- *Cinematography and visual style* (including colors and lightening, set design, costumes, makeup, special effects, overall aesthetic of the film)
- *Music and sound design* (including soundtrack and scores)
- *Theme and values* (including the moral or political message, emotional resonance, cultural or societal impact)

Such a task is called **aspect-base sentiment analysis**. It is a seriously difficult task that dedicated models still struggle to solve (see [Cathy Yua et al., 2024](https://arxiv.org/abs/2311.10777)). Some models extract opinions regarding pre-determined aspects, but are inapplicable here due to the absence of movie-specific datasets to train them. Other models extract aspects and opinions autonomously, but are difficult to use at scale, as their outputs remain very granular and context-dependant.

The only workable solution is to offload sentiment analysis to a **generative LLM**. A cursory experimentation proved that this works well with an adequate prompt. However, it requires very large models, that cannot be run locally but must be called through APIs. The current implementation relies on gpt-4o-mini from OpenAI, which is inexpensive ($0.15 / M tokens) but rather slow. An alternative would be to use Gemini from Google, which has a free tier, albeit with rates limits and requiring an API key as well.

### API
A minimal implementation, primarily intended as a proof of concept. In the DataLab, it can be launched and accessed from the terminal with:
- `poetry run uvicorn src.api:app --reload`
- `curl http://127.0.0.1:8000/movies/tt0029583` (for instance)

### Dashboard and user management
Built with Streamlit, the dashboard includes the following features:
- A landing page for user login and authentication.
- A movie selection page where users can choose a movie to display and add movies to their watchlist.
- A detailed movie page showcasing various statistics related to the movie's reviews.

## 3. Possible improvements
- Have a better looking dashboard
- Add an admin interface to the dashboard allowing to monitor the backend (including API costs) and manage users
- Fully separate the backend and frontend, using an API to communicate between them (with permissions depending on users)
- Use `playwright` for scraping, which is more flexible than Selenium
- Solve deployment with `argo CD`
- Implement more tests
- ...