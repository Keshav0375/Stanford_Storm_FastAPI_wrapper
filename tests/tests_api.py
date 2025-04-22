import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json
import asyncio

from main import app


@pytest.fixture
def client():
    """Test client for the FastAPI app."""
    return TestClient(app)


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_status(client):
    """Test the status endpoint."""
    response = client.get("/status")
    assert response.status_code == 200
    assert "environment" in response.json()
    assert "available_retrievers" in response.json()


@pytest.mark.asyncio
@patch("core.storm_wrapper.StormWrapper.run")
async def test_storm_endpoint(mock_run, client):
    """Test the STORM endpoint."""
    # Mock the response
    mock_response = MagicMock()
    mock_response.topic = "Test Topic"
    mock_response.conversation_log = []
    mock_response.raw_search_results = []
    mock_response.direct_gen_outline = "Test outline"
    mock_response.storm_gen_outline = "Test STORM outline"
    mock_response.url_to_info = {}
    mock_response.storm_gen_article = "Test article"
    mock_response.storm_gen_article_polished = "Test polished article"
    
    # Configure the mock to return this response
    mock_run.return_value = mock_response
    
    # Make the request
    request_data = {
        "topic": "Test Topic",
        "max_conv_turn": 3,
        "max_perspective": 3,
        "search_top_k": 3,
        "retriever": "you",
        "do_research": True,
        "do_generate_outline": True,
        "do_generate_article": True
    }
    
    response = client.post("/api/storm", json=request_data)
    
    # Check the response
    assert response.status_code == 200
    assert response.json()["topic"] == "Test Topic"
    assert response.json()["direct_gen_outline"] == "Test outline"
    assert response.json()["storm_gen_article"] == "Test article"
    
    # Verify the mock was called correctly
    mock_run.assert_called_once()


@pytest.mark.asyncio
@patch("core.storm_wrapper.StormWrapper.run_stream")
async def test_storm_stream_endpoint(mock_run_stream, client):
    """Test the streaming STORM endpoint."""
    # Create a mock async generator
    async def mock_generator():
        yield {"phase": "conversation_log", "content": []}
        yield {"phase": "direct_gen_outline", "content": "Test outline"}
        yield {"phase": "storm_gen_article", "content": "Test article"}
        yield {"phase": "complete", "content": True}
    
    mock_run_stream.return_value = mock_generator()
    
    # Make the request
    request_data = {
        "topic": "Test Topic",
        "max_conv_turn": 3,
        "max_perspective": 3,
        "search_top_k": 3,
        "retriever": "you",
        "do_research": True,
        "do_generate_outline": True,
        "do_generate_article": True,
        "stream": True
    }
    
    response = client.post("/api/storm/stream", json=request_data)
    
    # Check the response
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"
    
    # Verify the response content
    content = response.content.decode('utf-8')
    assert "data:" in content
    assert "Test outline" in content
    assert "Test article" in content
    
    # Verify the mock was called correctly
    mock_run_stream.assert_called_once()


@pytest.mark.asyncio
@patch("core.storm_wrapper.StormWrapper.run")
async def test_storm_error_handling(mock_run, client):
    """Test error handling in the STORM endpoint."""
    # Configure the mock to raise an exception
    mock_run.side_effect = Exception("Test error")
    
    # Make the request
    request_data = {
        "topic": "Test Topic",
        "max_conv_turn": 3,
        "max_perspective": 3,
        "search_top_k": 3,
        "retriever": "you",
        "do_research": True,
        "do_generate_outline": True,
        "do_generate_article": True
    }
    
    response = client.post("/api/storm", json=request_data)
    
    # Check the response
    assert response.status_code == 500
    assert "detail" in response.json()
    
    # Verify the mock was called
    mock_run.assert_called_once()


@pytest.mark.asyncio
async def test_invalid_request_validation(client):
    """Test input validation for the STORM endpoint."""
    # Make an invalid request (missing required field)
    request_data = {
        "max_conv_turn": 3,
        "max_perspective": 3,
        "search_top_k": 3,
        # Missing topic field
        "do_research": True,
        "do_generate_outline": True,
        "do_generate_article": True
    }
    
    response = client.post("/api/storm", json=request_data)
    
    # Check the response
    assert response.status_code == 422  # Validation error
    assert "detail" in response.json()