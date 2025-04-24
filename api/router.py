from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from core.storm_runner import get_storm_runner
from api.models import TopicRequest, WikiResponse
from typing import Optional

router = APIRouter()


@router.post("/generate", response_model=WikiResponse)
async def generate_wiki_content(
        request: TopicRequest,
        max_conv_turn: Optional[int] = Query(3, description="Maximum number of conversation turns"),
        max_perspective: Optional[int] = Query(3, description="Maximum number of perspectives to consider"),
        search_top_k: Optional[int] = Query(3, description="Top k search results to consider"),
        do_research: Optional[bool] = Query(True, description="Whether to do research"),
        do_generate_outline: Optional[bool] = Query(True, description="Whether to generate outline"),
        do_generate_article: Optional[bool] = Query(True, description="Whether to generate article"),
        do_polish_article: Optional[bool] = Query(True, description="Whether to polish article")
):
    """
    Generate wiki content for a given topic and return the complete response.
    """
    runner = get_storm_runner(
        max_conv_turn=max_conv_turn,
        max_perspective=max_perspective,
        search_top_k=search_top_k
    )

    result = runner.run_api(
        topic=request.topic,
        do_research=do_research,
        do_generate_outline=do_generate_outline,
        do_generate_article=do_generate_article,
        do_polish_article=do_polish_article,
        return_json=True
    )

    return result


@router.post("/stream-article")
async def stream_polished_article(
        request: TopicRequest,
        max_conv_turn: Optional[int] = Query(3, description="Maximum number of conversation turns"),
        max_perspective: Optional[int] = Query(3, description="Maximum number of perspectives to consider"),
        search_top_k: Optional[int] = Query(3, description="Top k search results to consider"),
        do_research: Optional[bool] = Query(True, description="Whether to do research"),
        do_generate_outline: Optional[bool] = Query(True, description="Whether to generate outline"),
        do_generate_article: Optional[bool] = Query(True, description="Whether to generate article"),
        do_polish_article: Optional[bool] = Query(True, description="Whether to polish article")
):
    """
    Generate wiki content for a given topic and stream the polished article word by word.
    """
    runner = get_storm_runner(
        max_conv_turn=max_conv_turn,
        max_perspective=max_perspective,
        search_top_k=search_top_k
    )

    async def word_by_word_stream():
        result = runner.run_api(
            topic=request.topic,
            do_research=do_research,
            do_generate_outline=do_generate_outline,
            do_generate_article=do_generate_article,
            do_polish_article=do_polish_article,
            return_json=True
        )

        # Get the polished article content, fallback to regular article if needed
        polished_article = result.get("storm_gen_article_polished", "") or result.get("storm_gen_article", "")

        # Split the content into words (keeping spaces and punctuation)
        import re
        words = re.findall(r'\S+|\s+', polished_article)

        # Stream word by word with small delays for natural reading effect
        import asyncio
        for word in words:
            yield word
            # Add a small delay for a more natural streaming effect
            # Adjust the delay based on word length and punctuation
            delay = 0.05  # Base delay in seconds
            if len(word) > 10:
                delay += 0.05  # Longer words get a bit more delay
            if re.search(r'[.!?]$', word):
                delay += 0.1  # Sentences get extra pause
            await asyncio.sleep(delay)

    return StreamingResponse(
        word_by_word_stream(),
        media_type="text/plain"
    )