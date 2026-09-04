# Aegis Engineering & Debugging Log

This log documents key technical challenges, debugging sessions, and architectural decisions made during the development of Aegis.

---

## 1. Python Externally Managed Environment (PEP 668)

### Problem
On modern Linux distributions (Ubuntu 23.04+, Debian 12+), global `pip install` commands trigger `error: externally-managed-environment` under PEP 668 to protect system packages.

### Resolution
- Provisioned a dedicated Linux service user `searxng` with home directory `/usr/local/searxng`.
- Isolated SearXNG and client dependencies inside a dedicated Python virtual environment (`/usr/local/searxng/searx-pyenv`).
- Always activate the environment via `source /usr/local/searxng/searx-pyenv/bin/activate` or execute using full path binaries.

---

## 2. WAF & Bot Mitigation Bypass (`HTTP 429` / `HTTP 403`)

### Problem
When making requests to local SearXNG instances using Python's `requests` library without custom headers, requests were blocked with `HTTP 403 Forbidden` or `HTTP 429 Too Many Requests`. This occurred because SearXNG's internal bot mitigation filters out default `python-requests/*` User-Agents.

### Resolution
- Added realistic desktop browser User-Agent headers across both CLI (`rag_search.py`) and Streamlit dashboard (`app.py`):
  ```python
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
          "AppleWebKit/537.36 (KHTML, like Gecko) "
          "Chrome/120.0.0.0 Safari/537.36"
      )
  }
  ```
- Configured SearXNG `settings.yml` with `limiter: false` for internal API calls on localhost.

---

## 3. JSON Stream Decoding & Fault Tolerant Parsing

### Problem
When SearXNG engine queries timed out or encountered upstream engine CAPTCHAs, SearXNG returned HTML error pages instead of JSON payloads. Direct invocations of `response.json()` resulted in unhandled `json.decoder.JSONDecodeError` exceptions.

### Resolution
- Added explicit HTTP response status validation (`response.status_code == 200`) before invoking `.json()`.
- Implemented connection error and timeout handling (`requests.exceptions.ConnectionError`, `requests.exceptions.Timeout`) with actionable error messages directing users to check the backend service.
- Safe extraction for snippets: fallback to `title` if `content` snippet is missing or empty.
- Handled empty result sets gracefully to avoid passing empty prompts to the LLM.

---

## 4. Gemini API Model Version Upgrades

### Problem
Early iterations targeted older model names or endpoints. As Gemini transitioned models, naming conventions evolved to `gemini-3.5-flash`.

### Resolution
- Standardized model initialization across all entry points to `genai.GenerativeModel("gemini-3.5-flash")`.
- Added strict environment variable checks for `GEMINI_API_KEY` before initialization to prevent cryptic runtime errors during downstream API calls.
