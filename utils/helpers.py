import os
import logging
from typing import Dict, Any, Optional


# Configure logging
def setup_logging(log_level: str = "INFO") -> None:
    """Set up logging for the application."""
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    level = log_levels.get(log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def check_environment_variables() -> Dict[str, bool]:
    """
    Check if required environment variables are set.
    Returns a dictionary with the status of each variable.
    """
    required_vars = [
        "OPENAI_API_KEY",
        "OPENAI_API_TYPE",
    ]

    optional_vars = [
        "AZURE_API_BASE",
        "AZURE_API_VERSION",
        "YDC_API_KEY",
        "BING_SEARCH_API_KEY",
        "SERPER_API_KEY",
        "BRAVE_API_KEY",
        "TAVILY_API_KEY",
        "SEARXNG_API_KEY",
        "AZURE_AI_SEARCH_API_KEY",
    ]

    result = {}

    # Check required variables
    for var in required_vars:
        result[var] = os.getenv(var) is not None

    # Check optional variables
    for var in optional_vars:
        result[var] = os.getenv(var) is not None

    return result


def get_available_retrievers() -> Dict[str, bool]:
    """
    Return a dictionary of available retrievers based on environment variables.
    """
    retrievers = {
        "you": os.getenv("YDC_API_KEY") is not None,
        "bing": os.getenv("BING_SEARCH_API_KEY") is not None,
        "brave": os.getenv("BRAVE_API_KEY") is not None,
        "serper": os.getenv("SERPER_API_KEY") is not None,
        "duckduckgo": True,  # DuckDuckGo doesn't require an API key
        "tavily": os.getenv("TAVILY_API_KEY") is not None,
        "searxng": os.getenv("SEARXNG_API_KEY") is not None,
        "azure_ai_search": os.getenv("AZURE_AI_SEARCH_API_KEY") is not None,
    }

    return retrievers