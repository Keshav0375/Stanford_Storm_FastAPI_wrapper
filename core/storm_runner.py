import os
import json
from typing import Dict, Any, Optional
import tempfile
import shutil

from storm.knowledge_storm import (
    STORMWikiRunnerArguments,
    STORMWikiRunner,
    STORMWikiLMConfigs,
)
from storm.knowledge_storm.lm import OpenAIModel, AzureOpenAIModel
from storm.knowledge_storm.rm import (
    YouRM,
    BingSearch,
    BraveRM,
    SerperRM,
    DuckDuckGoSearchRM,
    TavilySearchRM,
    SearXNG,
    AzureAISearch,
)
from utils.file_io import read_json_file, read_text_file
from storm.knowledge_storm.utils import load_api_key

def get_lm_configs():
    """Create and configure language models."""
    load_api_key(toml_file_path="secrets.toml")
    lm_configs = STORMWikiLMConfigs()

    openai_kwargs = {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "temperature": 1.0,
        "top_p": 0.9,
    }

    openai_4o_kwargs = {
        "api_key": os.getenv("AZURE_API_KEY_4O"),
        "temperature": 1.0,
        "top_p": 0.9,
    }

    ModelClass = (
        OpenAIModel if os.getenv("OPENAI_API_TYPE") == "openai" else AzureOpenAIModel
    )

    gpt_35_model_name = (
        "gpt-3.5-turbo" if os.getenv("OPENAI_API_TYPE") == "openai" else os.getenv("GPT_3_5_DEPLOYMENT_NAME")
    )

    gpt_4_model_name = (
        "gpt-4o" if os.getenv("OPENAI_API_TYPE") == "openai" else os.getenv("GPT_4O_DEPLOYMENT_NAME")
    )

    if os.getenv("OPENAI_API_TYPE") == "azure":
        openai_kwargs["azure_endpoint"] = os.getenv("AZURE_API_BASE")
        openai_kwargs["api_version"] = os.getenv("AZURE_API_VERSION")
        openai_4o_kwargs["azure_endpoint"] = os.getenv("AZURE_ENDPOINT_4O")
        openai_4o_kwargs["api_version"] = os.getenv("AZURE_VERSION_4O")

    conv_simulator_lm = ModelClass(
        model=gpt_35_model_name, max_tokens=1000, **openai_kwargs
    )
    question_asker_lm = ModelClass(
        model=gpt_35_model_name, max_tokens=1000, **openai_kwargs
    )
    outline_gen_lm = ModelClass(model=gpt_4_model_name, max_tokens=2500, **openai_4o_kwargs)
    article_gen_lm = ModelClass(model=gpt_4_model_name, max_tokens=2500, **openai_4o_kwargs)
    article_polish_lm = ModelClass(
        model=gpt_4_model_name, max_tokens=2500, **openai_kwargs
    )

    lm_configs.set_conv_simulator_lm(conv_simulator_lm)
    lm_configs.set_question_asker_lm(question_asker_lm)
    lm_configs.set_outline_gen_lm(outline_gen_lm)
    lm_configs.set_article_gen_lm(article_gen_lm)
    lm_configs.set_article_polish_lm(article_polish_lm)

    return lm_configs


def get_retrieval_module(search_top_k: int = 3):
    """Create and configure retrieval module based on available API keys."""
    retriever_priority = [
        ("you", "YDC_API_KEY", YouRM),
        ("bing", "BING_SEARCH_API_KEY", BingSearch),
        ("brave", "BRAVE_API_KEY", BraveRM),
        ("serper", "SERPER_API_KEY", SerperRM),
        ("tavily", "TAVILY_API_KEY", TavilySearchRM),
        ("searxng", "SEARXNG_API_KEY", SearXNG),
        ("azure_ai_search", "AZURE_AI_SEARCH_API_KEY", AzureAISearch),
    ]

    # Choose the first available retriever with an API key
    for retriever_name, env_key, RetrieverClass in retriever_priority:
        api_key = os.getenv(env_key)
        if api_key:
            retriever_kwargs = {"k": search_top_k}

            if retriever_name == "you":
                retriever_kwargs["ydc_api_key"] = api_key
            elif retriever_name == "bing":
                retriever_kwargs["bing_search_api"] = api_key
            elif retriever_name == "brave":
                retriever_kwargs["brave_search_api_key"] = api_key
            elif retriever_name == "serper":
                retriever_kwargs["serper_search_api_key"] = api_key
                retriever_kwargs["query_params"] = {"autocorrect": True, "num": 10, "page": 1}
            elif retriever_name == "tavily":
                retriever_kwargs["tavily_search_api_key"] = api_key
                retriever_kwargs["include_raw_content"] = True
            elif retriever_name == "searxng":
                retriever_kwargs["searxng_api_key"] = api_key
            elif retriever_name == "azure_ai_search":
                retriever_kwargs["azure_ai_search_api_key"] = api_key

            return RetrieverClass(**retriever_kwargs)

    # Fall back to DuckDuckGo if no API key is available
    return DuckDuckGoSearchRM(k=search_top_k, safe_search="On", region="us-en")


class APISTORMWikiRunner(STORMWikiRunner):
    """Extended STORMWikiRunner with API support."""

    def run_api(
            self,
            topic: str,
            do_research: bool = True,
            do_generate_outline: bool = True,
            do_generate_article: bool = True,
            do_polish_article: bool = True,
            return_json: bool = True
    ) -> Dict[str, Any]:
        """Run the STORM Wiki pipeline and return results as JSON."""
        # Run the normal pipeline process
        self.run(
            topic=topic,
            do_research=do_research,
            do_generate_outline=do_generate_outline,
            do_generate_article=do_generate_article,
            do_polish_article=do_polish_article
        )

        # Collect results from files
        if return_json:
            return self.collect_results()

        return {}

    def collect_results(self) -> Dict[str, Any]:
        """Collect results from output files."""
        result = {}

        try:
            # Text files
            text_files = {
                "direct_gen_outline": "direct_gen_outline.txt",
                "storm_gen_outline": "storm_gen_outline.txt",
                "storm_gen_article": "storm_gen_article.txt",
                "storm_gen_article_polished": "storm_gen_article_polished.txt",
            }

            for key, filename in text_files.items():
                file_path = os.path.join(self.article_output_dir, filename)
                if os.path.exists(file_path):
                    result[key] = read_text_file(file_path)

            # JSON files
            json_files = {
                "raw_search_results": "raw_search_results.json",
                "url_to_info": "url_to_info.json"
            }

            for key, filename in json_files.items():
                file_path = os.path.join(self.article_output_dir, filename)
                if os.path.exists(file_path):
                    result[key] = read_json_file(file_path)

        except Exception as e:
            print(f"Error collecting results: {e}")

        return result


def get_storm_runner(
        max_conv_turn: int = 3,
        max_perspective: int = 3,
        search_top_k: int = 3,
        max_thread_num: int = 3
) -> APISTORMWikiRunner:
    """Create and configure the STORM Wiki runner."""
    # Create a temporary directory for outputs
    temp_dir = tempfile.mkdtemp(prefix="storm_wiki_")

    # Configure the runner
    lm_configs = get_lm_configs()
    rm = get_retrieval_module(search_top_k)

    engine_args = STORMWikiRunnerArguments(
        output_dir=temp_dir,
        max_conv_turn=max_conv_turn,
        max_perspective=max_perspective,
        search_top_k=search_top_k,
        max_thread_num=max_thread_num,
    )

    return APISTORMWikiRunner(engine_args, lm_configs, rm)