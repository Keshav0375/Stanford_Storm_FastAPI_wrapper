FROM python:3.10-slim

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry==1.6.1

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock* /app/

# Configure Poetry to not create a virtual environment inside the container
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy the rest of the application
COPY . /app/

# Create a directory for secrets
RUN mkdir -p /app/secrets

# Expose port for the API
EXPOSE 8000

# Set the command to run the API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]