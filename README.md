# 🔍 Aegis: Privacy-Focused RAG Search Engine

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Frontend](https://img.shields.io/badge/Frontend-Streamlit-red.svg)](https://streamlit.io/)
[![Backend](https://img.shields.io/badge/Backend-SearXNG-green.svg)](https://searxng.org/)
[![AI](https://img.shields.io/badge/AI-Google_Gemini_API-orange.svg)](https://aistudio.google.com/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

An enterprise-grade, self-hosted Retrieval-Augmented Generation (RAG) platform. Aegis queries live web data locally through an isolated SearXNG metasearch instance and synthesizes concise, source-cited intelligence briefs using the Gemini API.

---

## 💡 Overview & Problem Statement

Commercial search engines monetize user telemetry, log search histories, and build digital tracking profiles. Meanwhile, standard standalone AI chatbots suffer from hallucinations and outdated knowledge cutoffs.

**Aegis** solves both challenges using a privacy-first hybrid architecture:
* **Zero Telemetry Tracking:** Self-hosts a private SearXNG metasearch instance isolated from commercial profiling and ad networks.
* **Ground-Truth AI Synthesis:** Retrieves real-time web results via local JSON streams and passes formatted context into an LLM for structured, cited synthesis.
* **Hybrid Cloud Security:** Maintains search aggregation locally on an isolated subnet while offloading inference to cloud endpoints without leaking user tracking identifiers.

---

## 🏛️ System Architecture

```text
                  [ User Web Browser ]
                            │
                            ▼
               [ Streamlit UI (app.py) ]
                            │
       (HTTP GET / Spoofed User-Agent / Port 8888)
                            ▼
              [ Local SearXNG Instance ]
           ┌────────────────┼────────────────┐
           ▼                ▼                ▼
     [ DuckDuckGo ]     [ Google ]     [ Wikipedia ]
           └────────────────┬────────────────┘
                            │ (Raw JSON Results)
                            ▼
               [ Python RAG Controller ]
                            │
            (Real-Time Context + Formatted Prompt)
                            ▼
                 [ Gemini 3.5 Flash API ]
                            │
                            ▼
         [ Structured Summary + Verified Citations ]
```

---

## 🛡️ Security & Engineering Highlights

* **Bot-Mitigation Bypass:** Implements custom User-Agent emulation on internal endpoints to bypass automated scraper detection and prevent `429 Too Many Requests` responses.
* **Credential Isolation:** Strict separation of configuration and secrets; API tokens are managed strictly via non-persisted environment variables rather than hardcoded parameters.
* **Network Segmentation:** Deployed on an Ubuntu Linux server segmented within a local NAT/WPA2 subnet with managed UFW firewall rules.
* **Fault-Tolerant Parsing:** Validates HTTP responses and JSON payloads to prevent parsing exceptions when metasearch engines encounter CAPTCHA or rate-limiting states.

---

## 🚀 Installation & Local Deployment

### 1. Prerequisites
* Ubuntu 22.04 LTS or newer
* Python 3.11+
* Active [Google AI Studio](https://aistudio.google.com/) API Key

### 2. System Dependencies
Install the required system libraries, build tools, and environment packages:

```bash
sudo apt-get update && sudo apt-get install -y \
    python3-dev python3-babel python3-venv python-is-python3 \
    uwsgi uwsgi-plugin-python3 git build-essential \
    libxslt-dev zlib1g-dev libffi-dev libssl-dev
```

### 3. Dedicated Service User & SearXNG Setup
Create an isolated system user and configure the virtual environment:

```bash
# Create service user
sudo useradd --shell /bin/bash --system \
    --home-dir "/usr/local/searxng" \
    --comment 'Privacy-respecting metasearch engine' \
    searxng

# Set directory permissions
sudo mkdir -p "/usr/local/searxng"
sudo chown -R "searxng:searxng" "/usr/local/searxng"

# Clone source code and initialize virtual environment
sudo -H -u searxng -i
git clone "[https://github.com/searxng/searxng](https://github.com/searxng/searxng)" "/usr/local/searxng/searxng-src"
python3 -m venv "/usr/local/searxng/searx-pyenv"
source "/usr/local/searxng/searx-pyenv/bin/activate"

# Install project dependencies
pip install --upgrade pip
pip install requests google-generativeai streamlit
```

### 4. SearXNG Configuration
Edit `/etc/searxng/settings.yml` to enable JSON format output and configure server binding:

```yaml
use_default_settings: true

general:
  debug: false
  instance_name: "SearXNG-SecureNode"

search:
  safe_search: 2
  autocomplete: 'duckduckgo'
  formats:
    - html
    - json

server:
  port: 8888
  bind_address: "0.0.0.0"
  secret_key: "GENERATE_A_RANDOM_HEX_KEY"
  limiter: false
  image_proxy: true
```

---

## 💻 Source Code

### 1. Terminal Client (`rag_search.py`)

```python
import os
import requests
import google.generativeai as genai

# Load Gemini API key from environment
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not found.")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-3.5-flash")

def fetch_search_results(query: str) -> str:
    """Queries the local SearXNG node and aggregates result snippets."""
    url = "[http://127.0.0.1:8888/search](http://127.0.0.1:8888/search)"
    params = {"q": query, "format": "json"}
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        raise ConnectionError(f"SearXNG returned status {response.status_code}: {response.text}")

    data = response.json()
    context_list = [
        f"URL: {item.get('url')}\nContent: {item.get('content')}"
        for item in data.get("results", [])[:5]
    ]
    return "\n\n".join(context_list)

def summarize_with_ai(query: str, context: str) -> str:
    """Submits context data to Gemini for structured generation."""
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
    user_query = input("Enter research query: ")
    print("\n🔍 Querying local SearXNG node...")
    search_context = fetch_search_results(user_query)

    print("🧠 Generating intelligence summary via Gemini...\n")
    print("-" * 60)
    print(summarize_with_ai(user_query, search_context))
    print("-" * 60)
```

### 2. Streamlit Web Dashboard (`app.py`)

```python
import os
import streamlit as st
import requests
import google.generativeai as genai

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

user_query = st.text_input("Enter research topic:", placeholder="e.g., Explain Zero Trust Architecture")

if st.button("Search & Analyze") and user_query:
    with st.spinner("Executing metasearch and generating summary..."):
        try:
            url = "[http://127.0.0.1:8888/search](http://127.0.0.1:8888/search)"
            params = {"q": user_query, "format": "json"}
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }

            response = requests.get(url, params=params, headers=headers)
            if response.status_code != 200:
                st.error(f"Search backend error: HTTP {response.status_code}")
                st.stop()

            data = response.json()
            context_list = []
            sources = []

            for item in data.get("results", [])[:5]:
                context_list.append(f"URL: {item.get('url')}\nContent: {item.get('content')}")
                sources.append(item.get("url"))

            search_context = "\n\n".join(context_list)

            prompt = (
                f"Provide a structured, compact answer to the user's query using ONLY "
                f"the provided search results context. Keep it clear, use bullet points if helpful, "
                f"and include inline source citations using the URLs provided.\n\n"
                f"User Query: {user_query}\n\n"
                f"Search Results Context:\n{search_context}"
            )

            ai_response = model.generate_content(prompt)

            st.subheader("🤖 AI Intelligence Summary")
            st.markdown(ai_response.text)

            with st.expander("🔗 View Extracted Source URLs"):
                for src in set(sources):
                    st.write(src)

        except Exception as e:
            st.error(f"Pipeline failure: {e}")
```

---

## 🏃 Execution Guide

Run the pipeline using two terminal instances:

### Terminal 1: Launch SearXNG Backend
```bash
sudo -H -u searxng -i
source "/usr/local/searxng/searx-pyenv/bin/activate"
export SEARXNG_SETTINGS_PATH="/etc/searxng/settings.yml"
python -m searx.webapp
```

### Terminal 2: Run Client Interface
```bash
sudo -H -u searxng -i
source "/usr/local/searxng/searx-pyenv/bin/activate"
export GEMINI_API_KEY="your_gemini_api_key_here"

# For CLI mode:
python rag_search.py

# For Web UI:
streamlit run app.py
```

Access the Streamlit web dashboard via `http://localhost:8501` (or your VM's private network IP, e.g., `http://192.168.x.x:8501`).

---

## 📝 Engineering & Debugging Log

Detailed troubleshooting documentation—including Linux virtual environment permission conflicts (PEP 668), WAF bot rate-limiting (`HTTP 429`), JSON stream decoding errors, and Gemini API model version updates—is recorded in [`DEV_LOG.md`](DEV_LOG.md).
