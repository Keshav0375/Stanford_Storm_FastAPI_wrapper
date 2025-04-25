from pydantic import BaseModel
from typing import Dict, Any, Optional


class TopicRequest(BaseModel):
    topic: str


class WikiResponse(BaseModel):
    direct_gen_outline: Optional[str] = None
    storm_gen_outline: Optional[str] = None
    storm_gen_article: Optional[str] = None
    storm_gen_article_polished: Optional[str] = None
    url_to_info: Optional[Dict[str, Any]] = None
    raw_search_results: Optional[Dict[str, Any]] = None
