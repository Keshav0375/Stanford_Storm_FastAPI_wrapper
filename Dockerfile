# Use official lightweight Python image
FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV POETRY_INSTALLER_MAX_RETRIES=10
ENV PIP_DEFAULT_TIMEOUT=100
ENV PIP_NO_CACHE_DIR=off

# Install curl and pip build dependencies
RUN apt-get update && apt-get install -y curl build-essential && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Set working directory
WORKDIR /app

# Copy only dependency files first
COPY pyproject.toml poetry.lock README.md main.py streamlit_app.py /app/

COPY api/ /app/api/
COPY core/ /app/core/
COPY utils/ /app/utils/

# Install project dependencies
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

# Copy rest of the application code
COPY . /app

# Expose port
EXPOSE 8000

# Start FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
