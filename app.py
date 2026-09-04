import os
import streamlit as st
import requests
import google.generativeai as genai

# Setup Gemini
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-3.5-flash')

st.set_page_config(page_title="AI Search Engine", page_icon="🔍", layout="centered")

st.title("🔍 Private AI Search Engine")
st.write("A privacy-respecting RAG search engine powered by your local SearXNG instance and Gemini.")

# User query input box
user_query = st.text_input("What would you like to research?", placeholder="e.g., Have you starred my repo yet?")

if st.button("Search & Analyze") and user_query:
    with st.spinner("Fetching live data from SearXNG and generating AI summary..."):
        try:
            # 1. Fetch from SearXNG
            url = "http://127.0.0.1:8888/search"
            params = {"q": user_query, "format": "json"}
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            response = requests.get(url, params=params, headers=headers)
            data = response.json()
            
            context_list = []
            sources = []
            for item in data.get('results', [])[:5]:
                context_list.append(f"URL: {item.get('url')}\nInformation: {item.get('content')}")
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
            st.subheader("🤖 AI Summary")
            st.markdown(ai_response.text)
            
            with st.expander("🔗 View Raw Sources"):
                for src in set(sources):
                    st.write(src)
                    
        except Exception as e:
            st.error(f"An error occurred: {e}")
