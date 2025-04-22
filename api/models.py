from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union


class StormRequest(BaseModel):
    """Base request model for STORM API."""
    topic: str = Field(..., description="The topic to research")
    max_conv_turn: int = Field(3, description="Maximum number of questions in conversational question asking")
    max_perspective: int = Field(3, description="Maximum number of perspectives to consider")
    search_top_k: int = Field(3, description="Top k search results to consider for each search query")
    max_thread_num: int = Field(3, description="Maximum number of threads to use")
    retrieve_top_k: int = Field(3, description="Top k collected references for each section title")
    remove_duplicate: bool = Field(False, description="If True, remove duplicate content from the article")
    do_research: bool = Field(True, description="If True, simulate conversation to research the topic")
    do_generate_outline: bool = Field(True, description="If True, generate an outline for the topic")
    do_generate_article: bool = Field(True, description="If True, generate an article for the topic")
    do_polish_article: bool = Field(False, description="If True, polish the article")
    retriever: str = Field("you", description="The search engine API to use (you, bing, brave, etc.)")
    stream: bool = Field(False, description="If True, stream the response")


class SearchResult(BaseModel):
    """Model for search results."""
    url: str
    title: str
    snippet: str


class ConversationTurn(BaseModel):
    """Model for a conversation turn."""
    question: str
    answer: str
    search_results: List[SearchResult]


class StormResponse(BaseModel):
    """Response model for STORM API."""
    topic: str
    conversation_log: Optional[List[ConversationTurn]] = None
    raw_search_results: Optional[List[Dict[str, Any]]] = None
    direct_gen_outline: Optional[str] = None
    storm_gen_outline: Optional[str] = None
    url_to_info: Optional[Dict[str, Any]] = None
    storm_gen_article: Optional[str] = None
    storm_gen_article_polished: Optional[str] = None