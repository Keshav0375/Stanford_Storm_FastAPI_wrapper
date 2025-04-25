from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from core.storm_runner import get_storm_runner
from api.models import TopicRequest, WikiResponse
from typing import Optional
import random

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

    async def dynamic_streaming():
        result = runner.run_api(
            topic=request.topic,
            do_research=do_research,
            do_generate_outline=do_generate_outline,
            do_generate_article=do_generate_article,
            do_polish_article=do_polish_article,
            return_json=True
        )

        polished_article = result.get("storm_gen_article_polished", "") or result.get("storm_gen_article", "")
        if isinstance(polished_article, bytes):
            polished_article = polished_article.decode('utf-8', errors='ignore')  # <-- important
        else:
            polished_article = polished_article.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')

        import re
        sentences = re.split(r'(?<=[.!?])\s+', polished_article)

        import asyncio
        current_paragraph = []
        words_in_paragraph = 0

        for sentence in sentences:
            try:
                words = sentence.split()
                sentence_length = len(words)
                if sentence_length <= 5:
                    yield sentence + " "
                    await asyncio.sleep(0.1)
                elif sentence_length <= 15:
                    chunks = random.randint(1, min(3, sentence_length))
                    chunk_size = sentence_length // chunks

                    for i in range(chunks):
                        start_idx = i * chunk_size
                        end_idx = start_idx + chunk_size if i < chunks - 1 else sentence_length
                        chunk = " ".join(words[start_idx:end_idx])
                        yield chunk + " "
                        await asyncio.sleep(random.uniform(0.05, 0.2))
                else:
                    remaining_words = words.copy()

                    while remaining_words:
                        chunk_size = min(len(remaining_words), random.randint(3, 12))
                        chunk = " ".join(remaining_words[:chunk_size])
                        yield chunk + " "

                        remaining_words = remaining_words[chunk_size:]

                        delay = random.uniform(0.05, 0.15)
                        if any(c in chunk for c in ".!?"):
                            delay += 0.1
                        await asyncio.sleep(delay)

                await asyncio.sleep(random.uniform(0.1, 0.3))
                if random.random() < 0.1:
                    await asyncio.sleep(random.uniform(0.5, 1.0))
            except UnicodeDecodeError as e:
                print(f"Unicode error while streaming sentence: {e}")
                continue

    return StreamingResponse(
        dynamic_streaming(),
        media_type="text/plain"
    )