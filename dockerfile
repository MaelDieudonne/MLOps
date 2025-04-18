FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.1.2 \
    DEBIAN_FRONTEND=noninteractive

# Set timezone
RUN ln -sf /usr/share/zoneinfo/Europe/Paris /etc/localtime && \
    echo "Europe/Paris" > /etc/timezone

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    gnupg \
    wget \
    tzdata \
    postgresql-client \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/* /root/.cache/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Set work directory
WORKDIR /app
ENV PYTHONPATH=/app

# Copy dependency files first for caching
COPY pyproject.toml poetry.lock* README.md /app/

# Install dependencies (let Poetry create a virtualenv)
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

# Copy your actual project
COPY . /app/

# Make scripts executable
RUN chmod +x /app/setup/db_init.py /app/scheduler.py /app/main.py /app/src/api.py /app/streamlit.py