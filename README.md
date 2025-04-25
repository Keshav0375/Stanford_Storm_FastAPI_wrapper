# STORM API - FastAPI Wrapper for Stanford STORM Wiki Pipeline

This project provides a **FastAPI**-based wrapper around the **Stanford STORM** Wiki GPT research pipeline.  
It allows users to generate articles, outlines, and research content programmatically through simple API endpoints.

---

## 🚀 Features

- Generate wiki-style articles for any topic
- Stream article content word-by-word
- Flexible control over research, outline, article generation and polishing
- Dockerized deployment
- Poetry-based dependency management

---

---

## 📦 Requirements

- Docker Desktop installed
- Git installed
- Internet access for pulling dependencies

---
## 🔑 Create `secrets.toml` File

Before running the server, you must create a `secrets.toml` file at the root of your project.

This file stores all the required API keys securely.

### ✨ Example: Standard OpenAI Setup

```toml
# secrets.toml
# ============ language model configurations ============
# Set up OpenAI API key.
OPENAI_API_KEY="openai_api_key"
OPENAI_API_TYPE="openai"

#OR
# If you are using the API service provided by Microsoft Azure, include the following lines:
#OPENAI_API_TYPE="azure"
#
#OPENAI_API_KEY="openai_api_key"
#AZURE_API_BASE="api_base_url"
#AZURE_API_VERSION="api_version"
#GPT_3_5_DEPLOYMENT_NAME="deployment_name"
#
#AZURE_API_KEY_4O="openai_api_key"
#AZURE_ENDPOINT_4O="api_base_url"
#AZURE_VERSION_4O="api_version"
#GPT_4O_DEPLOYMENT_NAME="deployment_name"


# ============ retriever configurations ============
BING_SEARCH_API_KEY="bing_search_api_key"

# ============ encoder configurations ============
ENCODER_API_TYPE="openai"
```

## 🛠 Setup Instructions

```bash
git clone https://github.com/Keshav0375/Stanford_Storm_FastAPI_wrapper.git
cd Stanford_Storm_FastAPI_wrapper
git clone https://github.com/stanford-oval/storm.git
docker build -t storm-api .
docker run -p 8000:8000 -v "$PWD/storm:/app/storm" storm-api
```

---

## 🌐 API Endpoints

Once the server is running at [http://localhost:8000](http://localhost:8000):

| Method | Endpoint                | Description                          |
|:------:|:------------------------|:-------------------------------------|
| GET    | `/health`                | Health check for server              |
| GET    | `/status`                | Check loaded API keys and configurations |
| POST   | `/api/storm/generate`     | Generate wiki content (full response) |
| POST   | `/api/storm/stream-article` | Stream polished article word-by-word |


# 🚀 Final Quick Start Guide

## 🐳 1. Start Docker Desktop

Make sure **Docker Desktop** is running on your system.

---

## 📥 2. Clone the Project Repository

```bash
git clone https://github.com/Keshav0375/Stanford_Storm_FastAPI_wrapper.git
cd Stanford_Storm_FastAPI_wrapper
```

## 🔑 3. Create secrets.toml file as instructed.


## 📚 4. Clone Stanford STORM Repository
```commandline
git clone https://github.com/stanford-oval/storm.git
```
## 🐳 5. Build and Run the Docker Container
```
docker build -t storm-api .
docker run -p 8000:8000 -v "$PWD/storm:/app/storm" storm-api
```
# Ready to Go

