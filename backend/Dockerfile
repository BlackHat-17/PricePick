# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# System deps for lxml, mysqlclient alternative, and Selenium (no browser here)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    libxml2 \
    libxslt1.1 \
    libxslt1-dev \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first for better layer caching
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy app
COPY . .

EXPOSE 8000

# Default environment
ENV HOST=0.0.0.0 \
    PORT=8000 \
    DEBUG=false

# Use uvicorn directly in Docker (avoids venv scripts)
CMD ["python", "main.py"]


