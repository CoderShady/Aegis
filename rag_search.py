import os
import requests
import google.generativeai as genai

# Setup Gemini (Replace with your actual API key)
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-3.5-flash')

def fetch_search_results(query):
    """Gets raw search data from your local SearXNG."""
    url = "http://127.0.0.1:8888/search"
    params = {"q": query, "format": "json"}
    
    response = requests.get(url, params=params)
    
    # If SearXNG returns an error code or HTML page, print it out for debugging
    if response.status_code != 200:
        raise Exception(f"SearXNG error (Status {response.status_code}): {response.text}")
        
    data = response.json()
    
    # Extract text snippets and URLs from the top 5 results
    context_list = []
    for item in data.get('results', [])[:5]:
        context_list.append(f"URL: {item.get('url')}\nInformation: {item.get('content')}")
        
    return "\n\n".join(context_list)

def summarize_with_ai(query, context):
    """Sends the search data to Gemini to write a summary."""
    prompt = (
        f"Provide a short compact direct answer to the user's query using ONLY "
        f"the provided search results. Keep it brief(under 4 bullet points), "
        f"avoid long paragraphs, and include inline citations using the URLs provided.\n\n "
        f"User Query: {query}\n\n"
        f"Search Results Context:\n{context}"
    )
    response = model.generate_content(prompt)
    return response.text

if __name__ == "__main__":
    user_query = input("What would you like to research? ")
    
    print("\n🔍 Fetching live data from your SearXNG instance...")
    search_context = fetch_search_results(user_query)
    
    print("🧠 Reading data and generating AI summary...\n")
    print("-" * 50)
    print(summarize_with_ai(user_query, search_context))
    print("-" * 50)
