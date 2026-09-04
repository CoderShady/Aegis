import os
import sys

import google.generativeai as genai
import requests

# Load Gemini API key from environment
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not found. Please export it before running.")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-3.5-flash")

def fetch_search_results(query: str) -> str:
    """Queries the local SearXNG node and aggregates result snippets."""
    url = "http://127.0.0.1:8888/search"
    params = {"q": query, "format": "json"}
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
        raise ConnectionError("Could not connect to SearXNG at http://127.0.0.1:8888. Please ensure the SearXNG service is running.")
    except requests.exceptions.Timeout:
        raise TimeoutError("Connection to SearXNG timed out.")

    if response.status_code != 200:
        raise ConnectionError(f"SearXNG returned status {response.status_code}: {response.text}")

    data = response.json()
    results = data.get("results", [])
    if not results:
        return ""

    context_list = [
        f"URL: {item.get('url')}\nContent: {item.get('content') or item.get('title') or ''}"
        for item in results[:5]
    ]
    return "\n\n".join(context_list)

def summarize_with_ai(query: str, context: str) -> str:
    """Submits context data to Gemini for structured generation."""
    if not context:
        return "No relevant search results found to answer your query."

    prompt = (
        f"Provide a short, compact, direct answer to the user's query using ONLY "
        f"the provided search results. Keep it brief (under 4 bullet points), "
        f"avoid unnecessary fluff, and include inline citations using the URLs provided.\n\n"
        f"User Query: {query}\n\n"
        f"Search Results Context:\n{context}"
    )
    response = model.generate_content(prompt)
    return response.text

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 Aegis: Privacy-Focused RAG Search Engine")
    print("=" * 60)
    user_query = input("Enter research query: ")
    if not user_query.strip():
        print("Query cannot be empty.")
        sys.exit(0)

    print("\n🔍 Querying local SearXNG node...")
    search_context = fetch_search_results(user_query)

    print("🧠 Generating intelligence summary via Gemini...\n")
    print("-" * 60)
    print(summarize_with_ai(user_query, search_context))
    print("-" * 60)
