import os

import google.generativeai as genai
import requests
import streamlit as st

# Configure page settings
st.set_page_config(page_title="Aegis AI", page_icon="🔍", layout="centered")

# Initialize Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("Missing GEMINI_API_KEY environment variable. Export it before running.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-3.5-flash")

st.title("🔍 Aegis")
st.write("Privacy-preserving, real-time RAG search engine powered by SearXNG and Gemini.")

# User query input box
user_query = st.text_input("Enter research topic:", placeholder="e.g., Explain Zero Trust Architecture")

if st.button("Search & Analyze") and user_query:
    with st.spinner("Executing metasearch and generating summary..."):
        try:
            # 1. Fetch from SearXNG
            url = "http://127.0.0.1:8888/search"
            params = {"q": user_query, "format": "json"}
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
            
            try:
                response = requests.get(url, params=params, headers=headers, timeout=10)
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to SearXNG at http://127.0.0.1:8888. Please ensure the SearXNG service is running.")
                st.stop()
            except requests.exceptions.Timeout:
                st.error("Connection to SearXNG timed out. Please check your backend instance.")
                st.stop()

            if response.status_code != 200:
                st.error(f"Search backend error: HTTP {response.status_code}")
                st.stop()
                
            data = response.json()
            
            results = data.get('results', [])
            if not results:
                st.warning("No search results found. Try modifying your query.")
                st.stop()

            context_list = []
            sources = []
            for item in results[:5]:
                content = item.get('content') or item.get('title') or ''
                context_list.append(f"URL: {item.get('url')}\nContent: {content}")
                if item.get('url'):
                    sources.append(item.get('url'))
                
            search_context = "\n\n".join(context_list)
            
            # 2. Summarize with Gemini
            prompt = (
                f"Provide a structured, compact answer to the user's query using ONLY "
                f"the provided search results context. Keep it clear, use bullet points if helpful, "
                f"and include inline source citations using the URLs provided.\n\n"
                f"User Query: {user_query}\n\n"
                f"Search Results Context:\n{search_context}"
            )
            
            ai_response = model.generate_content(prompt)
            
            # 3. Display Results on UI
            st.subheader("🤖 AI Intelligence Summary")
            st.markdown(ai_response.text)
            
            if sources:
                with st.expander("🔗 View Extracted Source URLs"):
                    for src in dict.fromkeys(sources):
                        st.write(src)
                    
        except Exception as e:  # noqa: BLE001
            st.error(f"Pipeline failure: {e}")
