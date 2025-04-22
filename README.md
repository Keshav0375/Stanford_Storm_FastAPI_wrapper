# Stanford STORM FastAPI Wrapper

This project provides a FastAPI wrapper for the Stanford STORM (Structure-based Optimized Retrieval Method) project, allowing you to use STORM's functionality via a RESTful API interface.

## Features

- **Clean API Interface**: Access STORM functionality via HTTP endpoints
- **In-Memory Processing**: Results are returned directly in memory instead of writing to disk
- **Streamed Responses**: Support for streaming responses as they're generated
- **Dockerized**: Ready to run in a Docker container
- **Poetry-managed**: All dependencies are managed via Poetry

## Setup

### Prerequisites

- Python 3.9+
- Poetry
- Docker (optional)

### Environment Variables

Create a `secrets.toml` file at the root of the project with the following content:

```toml
OPENAI_API_KEY = "your-openai-api-key"
OPENAI_API_TYPE = "openai"  # or "azure"

# Required for You.com search (default retriever)
YDC_API_KEY = "your-you-api-key"

# Optional: required only if using Azure OpenAI
AZURE_API_BASE = "your-azure-api-base"
AZURE_API_VERSION = "your-azure-api-version"

# Optional: for other search engines
BING_SEARCH_API_KEY = "your-bing-api-key"
BRAVE_API_KEY = "your-brave-api-key"
SERPER_API_KEY = "your-serper-api-key"
TAVILY_API_KEY = "your-tavily-api-key"
SEARXNG_API_KEY = "your-searxng-api-key"
AZURE_AI_SEARCH_API_KEY = "your-azure-ai-search-api-key"
```

### Installation

#### Using Poetry

```bash
# Install dependencies
poetry install

# Run the API
poetry run uvicorn main:app --host 0.0.0.0 --port 8000
```

#### Using Docker

```bash
# Build the Docker image
docker build -t core-api .

# Run the container
docker run -p 8000:8000 -v $(pwd)/secrets.toml:/app/secrets/secrets.toml core-api
```

## API Usage

### Generate STORM Content

```bash
curl -X POST http://localhost:8000/api/storm \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "The impact of artificial intelligence on healthcare",
    "max_conv_turn": 3,
    "max_perspective": 3,
    "search_top_k": 3,
    "retriever": "you",
    "do_research": true,
    "do_generate_outline": true,
    "do_generate_article": true,
    "do_polish_article": false
  }'
```

### Stream STORM Content

```bash
curl -X POST http://localhost:8000/api/storm/stream \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "The impact of artificial intelligence on healthcare",
    "max_conv_turn": 3,
    "max_perspective": 3,
    "search_top_k": 3,
    "retriever": "you",
    "do_research": true,
    "do_generate_outline": true,
    "do_generate_article": true,
    "stream": true
  }'
```

## API Endpoints

- `GET /health`: Health check endpoint
- `GET /status`: Check the status of environment variables and available retrievers
- `POST /api/storm`: Generate STORM content
- `POST /api/storm/stream`: Stream STORM content as it's being generated

## Development

To run tests:

```bash
poetry run pytest
```

## License

This project is licensed under the terms of the same license as the Stanford STORM project.