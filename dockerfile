### Build stage
FROM python:3.12-slim AS builder

ARG DB_HOST
ARG DB_USER
ARG DB_PASSWORD
ARG DB_NAME
ARG OPENAI_API_KEY
ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_SESSION_TOKEN
ARG AWS_S3_ENDPOINT
ARG AWS_DEFAULT_REGION

# Set environment variables for the build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.1.2 \
    DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* /root/.cache/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Set workdir
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock* /app/

# Install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi


### Final stage
FROM python:3.12-slim

ARG DB_HOST
ARG DB_USER
ARG DB_PASSWORD
ARG DB_NAME
ARG OPENAI_API_KEY
ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_SESSION_TOKEN
ARG AWS_S3_ENDPOINT
ARG AWS_DEFAULT_REGION

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.1.2 \
    DEBIAN_FRONTEND=noninteractive

# Set timezone
RUN ln -sf /usr/share/zoneinfo/Europe/Paris /etc/localtime && \
    echo "Europe/Paris" > /etc/timezone

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    wget \
    gnupg \
    curl \
    postgresql-client \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/* /root/.cache/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Verify timezone
RUN echo "Verifying timezone during build:" && date

# Set workdir
WORKDIR /app

# Copy Python packages installed by Poetry from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy the source code
COPY . /app/

# Create the .env file with secrets passed as build arguments
RUN echo "DB_NAME=$DB_NAME" > /app/.env && \
    echo "DB_HOST=$DB_HOST" >> /app/.env && \
    echo "DB_USER=$DB_USER" >> /app/.env && \
    echo "DB_PASSWORD=$DB_PASSWORD" >> /app/.env && \
    echo "OPENAI_API_KEY=$OPENAI_API_KEY" >> /app/.env && \
    echo "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID" >> /app/.env && \
    echo "AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY" >> /app/.env && \
    echo "AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN" >> /app/.env && \
    echo "AWS_S3_ENDPOINT=$AWS_S3_ENDPOINT" >> /app/.env && \
    echo "AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION" >> /app/.env

# Make the scripts executable
RUN chmod +x /app/setup/db_init.py /app/scheduler.py /app/main.py /app/ api.py /app/Streamlit/streamlit.py
