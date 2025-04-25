import streamlit as st
import requests
import time
import json
from typing import Dict, Any, Optional, Iterator
import re

# App title and description
st.set_page_config(page_title="STORM API Tester", layout="wide")
st.title("Stanford STORM API Tester")
st.markdown("""
Use this interface to test the STORM API endpoints.
- Regular mode: Get the complete response at once
- Streaming mode: See the content appear word by word
""")

# Server configuration
API_BASE_URL = "http://localhost:8000/api/storm"

# Form for user input
with st.form("storm_form"):
    col1, col2 = st.columns([3, 1])

    with col1:
        topic = st.text_input("Enter a topic to research:")

    with col2:
        is_streaming = st.toggle("Enable streaming", value=False)


    submit_button = st.form_submit_button("Generate Content")


def get_complete_content(topic: str):
    url = f"{API_BASE_URL}/generate"
    payload = {"topic": topic}

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error: {response.status_code} - {response.text}")
        return {}


def stream_content(topic: str):
    url = f"{API_BASE_URL}/stream-article"
    payload = {"topic": topic}

    with requests.post(url, json=payload, stream=True) as response:
        if response.status_code == 200:
            for chunk in response.iter_content(chunk_size=1):
                if chunk:
                    yield chunk.decode('utf-8')
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
            yield ""


def show_research_spinner():
    research_steps = [
        "Choosing a topic...",
        "Planning what to find...",
        "Searching for information...",
        "Reading different sources...",
        "Taking important notes...",
        "Comparing ideas...",
        "Thinking about different views...",
        "Putting ideas together...",
        "Making an outline...",
        "Finishing the research..."
    ]

    placeholder = st.empty()

    for i, step in enumerate(research_steps):
        with placeholder:
            st.info(f"Step {i + 1}/6: {step}")
        time.sleep(5)

if submit_button:

    tab1, tab2, tab3 = st.tabs(["Article", "Outline", "Research Data"])

    with tab1:
        if is_streaming:
            with st.spinner("Preparing to stream content..."):
                show_research_spinner()

            content_placeholder = st.empty()
            full_content = ""

            st.write("Streaming content:")
            content_container = st.empty()

            for word in stream_content(topic):
                full_content += word
                content_container.markdown(full_content)
                time.sleep(0.01)

        else:
            # Handle complete response
            with st.spinner("Researching and generating content..."):
                # Show changing research messages
                show_research_spinner()

                # Get the complete response
                result = get_complete_content(topic)

            # Display polished article or regular article
            article = result.get("storm_gen_article_polished") or result.get("storm_gen_article")
            if article:
                st.markdown(article)
            else:
                st.warning("No article was generated.")

        with tab2:
            if not is_streaming:
                # Display outline if available
                outline = result.get("storm_gen_outline") or result.get("direct_gen_outline")
                if outline:
                    st.markdown(outline)
                else:
                    st.warning("No outline was generated.")

        with tab3:
            if not is_streaming:
                # Display raw search results if available
                search_results = result.get("raw_search_results")
                if search_results:
                    st.json(search_results)

                # Display URL info if available
                url_info = result.get("url_to_info")
                if url_info:
                    st.subheader("Sources Used")
                    for url, info in url_info.items():
                        st.markdown(f"- [{url}]({url})")