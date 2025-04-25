from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.router import router
from utils.storm_patches import apply_patches
import os
import logging
from storm.knowledge_storm.utils import load_api_key

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("main")
logging.getLogger('trafilatura').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)
logging.getLogger('httpx').setLevel(logging.CRITICAL)

patch_successful = apply_patches()


app = FastAPI(
    title="STORM Wiki API",
    description="API wrapper for STORM Wiki pipeline",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Basic health check endpoint that also verifies STORM patching status."""
    return {
        "status": "ok"
    }


@app.get("/status")
async def status():
    """Get the status of available API keys and services."""
    load_api_key(toml_file_path="secrets.toml")

    api_keys = {
        "OPENAI_KEY": bool(os.getenv("OPENAI_API_KEY")),
        "ydc": bool(os.getenv("YDC_API_KEY")),
        "bing": bool(os.getenv("BING_SEARCH_API_KEY")),
        "brave": bool(os.getenv("BRAVE_API_KEY")),
        "serper": bool(os.getenv("SERPER_API_KEY")),
        "tavily": bool(os.getenv("TAVILY_API_KEY")),
        "searxng": bool(os.getenv("SEARXNG_API_KEY")),
        "azure_ai_search": bool(os.getenv("AZURE_AI_SEARCH_API_KEY")),
    }

    if api_keys["OPENAI_KEY"]:
        openai_api_type = os.getenv("OPENAI_API_TYPE")

    search_provider = "duckduckgo"
    for provider, env_var in [
        ("you", "YDC_API_KEY"),
        ("bing", "BING_SEARCH_API_KEY"),
        ("brave", "BRAVE_API_KEY"),
        ("serper", "SERPER_API_KEY"),
        ("tavily", "TAVILY_API_KEY"),
        ("searxng", "SEARXNG_API_KEY"),
        ("azure_ai_search", "AZURE_AI_SEARCH_API_KEY"),
    ]:
        if os.getenv(env_var):
            search_provider = provider
            break

    return {
        "status": "ok",
        "OpenAI_type": openai_api_type,
        "search_provider": search_provider
    }


app.include_router(router, prefix="/api/storm")

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting STORM Wiki API server...")

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)