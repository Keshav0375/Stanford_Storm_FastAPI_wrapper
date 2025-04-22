import os
import asyncio
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
import io
from contextlib import redirect_stdout, redirect_stderr

from knowledge_storm import (
    STORMWikiRunnerArguments,
    STORMWikiRunner,
    STORMWikiLMConfigs,
)
from knowledge_storm.lm import OpenAIModel, AzureOpenAIModel
from knowledge_storm.rm import (
    YouRM,
    BingSearch,
    BraveRM,
    SerperRM,
    DuckDuckGoSearchRM,
    TavilySearchRM,
    SearXNG,
    AzureAISearch,
)
from knowledge_storm.utils import load_api_key
from utils.text_encoding import normalize_text, normalize_dict, normalize_list

from api.models import StormRequest, StormResponse

logger = logging.getLogger(__name__)


class MemoryStormWikiRunner(STORMWikiRunner):
    """
    Override STORMWikiRunner to prevent writing to disk and
    instead capture outputs in memory.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.outputs = {
            "conversation_log": [],
            "raw_search_results": [],
            "direct_gen_outline": "",
            "storm_gen_outline": "",
            "url_to_info": {},
            "storm_gen_article": "",
            "storm_gen_article_polished": "",
        }
        self._current_phase = None
        self._streaming_enabled = False
        self._streaming_callback = None

    def set_streaming(self, enabled=True, callback=None):
        """Enable or disable streaming updates."""
        self._streaming_enabled = enabled
        self._streaming_callback = callback

    def _send_stream_update(self, phase, content):
        """Send streaming update if streaming is enabled."""
        if self._streaming_enabled and self._streaming_callback:
            asyncio.create_task(self._streaming_callback(phase, content))

    # Override file-writing methods
    def _create_output_dir(self, *args, **kwargs):
        """Override to prevent directory creation."""
        pass

    def save_conversation_log(self, conversation_log):
        """Capture conversation log in memory instead of writing to disk."""
        self.outputs["conversation_log"] = normalize_list(conversation_log)
        self._send_stream_update("conversation_log", self.outputs["conversation_log"])
        logger.debug(f"Saved conversation log with {len(conversation_log)} entries")

    def save_raw_search_results(self, raw_search_results):
        """Capture raw search results in memory instead of writing to disk."""
        self.outputs["raw_search_results"] = normalize_list(raw_search_results)
        self._send_stream_update("raw_search_results", self.outputs["raw_search_results"])
        logger.debug(f"Saved {len(raw_search_results)} raw search results")

    def save_direct_gen_outline(self, direct_gen_outline):
        """Capture direct gen outline in memory instead of writing to disk."""
        self.outputs["direct_gen_outline"] = normalize_text(direct_gen_outline)
        self._send_stream_update("direct_gen_outline", self.outputs["direct_gen_outline"])
        logger.debug("Saved direct gen outline")

    def save_storm_gen_outline(self, storm_gen_outline):
        """Capture STORM gen outline in memory instead of writing to disk."""
        self.outputs["storm_gen_outline"] = normalize_text(storm_gen_outline)
        self._send_stream_update("storm_gen_outline", self.outputs["storm_gen_outline"])
        logger.debug("Saved STORM gen outline")

    def save_url_to_info(self, url_to_info):
        """Capture URL to info mapping in memory instead of writing to disk."""
        self.outputs["url_to_info"] = normalize_dict(url_to_info)
        self._send_stream_update("url_to_info", self.outputs["url_to_info"])
        logger.debug(f"Saved URL to info mapping with {len(url_to_info)} entries")

    def save_storm_gen_article(self, storm_gen_article):
        """Capture STORM gen article in memory instead of writing to disk."""
        self.outputs["storm_gen_article"] = normalize_text(storm_gen_article)
        self._send_stream_update("storm_gen_article", self.outputs["storm_gen_article"])
        logger.debug("Saved STORM gen article")

    def save_storm_gen_article_polished(self, storm_gen_article_polished):
        """Capture polished STORM gen article in memory instead of writing to disk."""
        self.outputs["storm_gen_article_polished"] = normalize_text(storm_gen_article_polished)
        self._send_stream_update("storm_gen_article_polished", self.outputs["storm_gen_article_polished"])
        logger.debug("Saved polished STORM gen article")

    def post_run(self):
        """Override post_run to avoid file operations."""
        pass

    def summary(self):
        """Override summary to return in-memory results instead of printing."""
        logger.debug("Returning summary of all captured outputs")
        return self.outputs


class StormWrapper:
    """Wrapper for Stanford STORM to provide a clean API interface."""

    def __init__(self):
        load_api_key(toml_file_path="secrets.toml")
        self.lm_configs = STORMWikiLMConfigs()

    def _configure_lm(self):
        """Configure language models for STORM."""
        openai_kwargs = {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "temperature": 1.0,
            "top_p": 0.9,
        }

        ModelClass = (
            OpenAIModel if os.getenv("OPENAI_API_TYPE") == "openai" else AzureOpenAIModel
        )

        gpt_35_model_name = (
            "gpt-3.5-turbo" if os.getenv("OPENAI_API_TYPE") == "openai" else "gpt-35-turbo"
        )
        gpt_4_model_name = "gpt-4o"

        if os.getenv("OPENAI_API_TYPE") == "azure":
            openai_kwargs["api_base"] = os.getenv("AZURE_API_BASE")
            openai_kwargs["api_version"] = os.getenv("AZURE_API_VERSION")

        conv_simulator_lm = ModelClass(
            model=gpt_35_model_name, max_tokens=500, **openai_kwargs
        )
        question_asker_lm = ModelClass(
            model=gpt_35_model_name, max_tokens=500, **openai_kwargs
        )
        outline_gen_lm = ModelClass(
            model=gpt_4_model_name, max_tokens=400, **openai_kwargs
        )
        article_gen_lm = ModelClass(
            model=gpt_4_model_name, max_tokens=700, **openai_kwargs
        )
        article_polish_lm = ModelClass(
            model=gpt_4_model_name, max_tokens=4000, **openai_kwargs
        )

        self.lm_configs.set_conv_simulator_lm(conv_simulator_lm)
        self.lm_configs.set_question_asker_lm(question_asker_lm)
        self.lm_configs.set_outline_gen_lm(outline_gen_lm)
        self.lm_configs.set_article_gen_lm(article_gen_lm)
        self.lm_configs.set_article_polish_lm(article_polish_lm)

        return self.lm_configs

    def _get_retriever(self, retriever_name: str, search_top_k: int):
        """Get the appropriate retriever based on the request."""
        match retriever_name:
            case "bing":
                return BingSearch(
                    bing_search_api=os.getenv("BING_SEARCH_API_KEY"),
                    k=search_top_k,
                )
            case "you":
                return YouRM(
                    ydc_api_key=os.getenv("YDC_API_KEY"),
                    k=search_top_k
                )
            case "brave":
                return BraveRM(
                    brave_search_api_key=os.getenv("BRAVE_API_KEY"),
                    k=search_top_k,
                )
            case "duckduckgo":
                return DuckDuckGoSearchRM(
                    k=search_top_k,
                    safe_search="On",
                    region="us-en"
                )
            case "serper":
                return SerperRM(
                    serper_search_api_key=os.getenv("SERPER_API_KEY"),
                    query_params={"autocorrect": True, "num": 10, "page": 1},
                )
            case "tavily":
                return TavilySearchRM(
                    tavily_search_api_key=os.getenv("TAVILY_API_KEY"),
                    k=search_top_k,
                    include_raw_content=True,
                )
            case "searxng":
                return SearXNG(
                    searxng_api_key=os.getenv("SEARXNG_API_KEY"),
                    k=search_top_k
                )
            case "azure_ai_search":
                return AzureAISearch(
                    azure_ai_search_api_key=os.getenv("AZURE_AI_SEARCH_API_KEY"),
                    k=search_top_k,
                )
            case _:
                # Default to You.com if retriever is not recognized
                logger.warning(f"Unknown retriever: {retriever_name}. Using 'you' instead.")
                return YouRM(
                    ydc_api_key=os.getenv("YDC_API_KEY"),
                    k=search_top_k
                )

    async def run(self, request: StormRequest) -> StormResponse:
        """Run STORM and return results."""
        # Redirect stdout/stderr to capture and suppress any print statements
        stdout = io.StringIO()
        stderr = io.StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            # Configure LM
            lm_configs = self._configure_lm()

            # Set up engine arguments
            engine_args = STORMWikiRunnerArguments(
                output_dir="/tmp/storm_output",  # Dummy dir, won't be used
                max_conv_turn=request.max_conv_turn,
                max_perspective=request.max_perspective,
                search_top_k=request.search_top_k,
                max_thread_num=request.max_thread_num,
            )

            # Set up retriever
            rm = self._get_retriever(request.retriever, request.search_top_k)

            # Create and run STORM
            runner = MemoryStormWikiRunner(engine_args, lm_configs, rm)

            # Run STORM with the provided parameters
            runner.run(
                topic=request.topic,
                do_research=request.do_research,
                do_generate_outline=request.do_generate_outline,
                do_generate_article=request.do_generate_article,
                do_polish_article=request.do_polish_article,
            )

            # Get results and create StormResponse
            results = runner.summary()
            return StormResponse(
                topic=request.topic,
                conversation_log=results["conversation_log"],
                raw_search_results=results["raw_search_results"],
                direct_gen_outline=results["direct_gen_outline"],
                storm_gen_outline=results["storm_gen_outline"],
                url_to_info=results["url_to_info"],
                storm_gen_article=results["storm_gen_article"],
                storm_gen_article_polished=results["storm_gen_article_polished"]
            )

    async def run_stream(self, request: StormRequest) -> AsyncGenerator[Dict[str, Any], None]:
        """Run STORM and yield streaming updates."""
        # Create a queue for streaming updates
        queue = asyncio.Queue()

        async def stream_callback(phase, content):
            await queue.put({"phase": phase, "content": content})

        # Run STORM in a separate thread to avoid blocking the event loop
        async def run_storm():
            try:
                # Redirect stdout/stderr to capture and suppress any print statements
                stdout = io.StringIO()
                stderr = io.StringIO()

                with redirect_stdout(stdout), redirect_stderr(stderr):
                    # Configure LM
                    lm_configs = self._configure_lm()

                    # Set up engine arguments
                    engine_args = STORMWikiRunnerArguments(
                        output_dir="/tmp/storm_output",  # Dummy dir, won't be used
                        max_conv_turn=request.max_conv_turn,
                        max_perspective=request.max_perspective,
                        search_top_k=request.search_top_k,
                        max_thread_num=request.max_thread_num,
                    )

                    # Set up retriever
                    rm = self._get_retriever(request.retriever, request.search_top_k)

                    # Create and run STORM
                    runner = MemoryStormWikiRunner(engine_args, lm_configs, rm)
                    runner.set_streaming(enabled=True, callback=stream_callback)

                    # Run STORM with the provided parameters
                    runner.run(
                        topic=request.topic,
                        do_research=request.do_research,
                        do_generate_outline=request.do_generate_outline,
                        do_generate_article=request.do_generate_article,
                        do_polish_article=request.do_polish_article,
                    )

                    # Mark completion
                    await queue.put({"phase": "complete", "content": True})
            except Exception as e:
                logger.error(f"Error in STORM streaming: {str(e)}")
                await queue.put({"phase": "error", "content": str(e)})

        # Start the STORM process
        asyncio.create_task(run_storm())

        # Yield updates from the queue
        while True:
            update = await queue.get()
            yield update

            if update["phase"] in ["complete", "error"]:
                break