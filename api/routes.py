from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any

from api.models import StormRequest, StormResponse
from core.storm_wrapper import StormWrapper
from utils.text_encoding import normalize_dict, normalize_list, safe_json_serialize

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/core", response_model=StormResponse)
async def generate_storm(request: StormRequest):
    """
    Generate a STORM response for the given request.
    Returns a JSON response with the results.
    """
    try:
        storm = StormWrapper()
        result = await storm.run(request)
        
        # Normalize all string fields in the response
        if result.conversation_log:
            result.conversation_log = normalize_list(result.conversation_log)
        if result.raw_search_results:
            result.raw_search_results = normalize_list(result.raw_search_results)
        if result.direct_gen_outline:
            result.direct_gen_outline = normalize_text(result.direct_gen_outline)
        if result.storm_gen_outline:
            result.storm_gen_outline = normalize_text(result.storm_gen_outline)
        if result.url_to_info:
            result.url_to_info = normalize_dict(result.url_to_info)
        if result.storm_gen_article:
            result.storm_gen_article = normalize_text(result.storm_gen_article)
        if result.storm_gen_article_polished:
            result.storm_gen_article_polished = normalize_text(result.storm_gen_article_polished)
            
        return result
    except Exception as e:
        logger.error(f"Error in STORM API: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def stream_storm_response(request: StormRequest) -> AsyncGenerator[bytes, None]:
    """Stream STORM response as it's being generated."""
    storm = StormWrapper()
    generator = storm.run_stream(request)

    async for update in generator:
        # Use our safe JSON serialization
        json_str = safe_json_serialize(update)
        yield f"data: {json_str}\n\n".encode('utf-8')


@router.post("/core/stream")
async def generate_storm_stream(request: StormRequest):
    """
    Generate a STORM response for the given request.
    Returns a streaming response with partial results as they become available.
    """
    try:
        if not request.stream:
            request.stream = True

        return StreamingResponse(
            stream_storm_response(request),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Error in STORM API streaming: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))