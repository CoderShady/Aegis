#!/usr/bin/env bash
# Aegis Unified Launcher - Runs SearXNG and Streamlit together

set -e

SEARXNG_PID=""

cleanup() {
    echo ""
    echo "🛑 Shutting down Aegis..."
    if [ -n "$SEARXNG_PID" ]; then
        kill "$SEARXNG_PID" 2>/dev/null || true
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# 1. Check if SearXNG is already running on port 8888
if curl -s "http://127.0.0.1:8888" >/dev/null 2>&1; then
    echo "✅ SearXNG backend is already active on http://127.0.0.1:8888"
else
    echo "🚀 Starting SearXNG backend on port 8888..."
    export SEARXNG_SETTINGS_PATH="${SEARXNG_SETTINGS_PATH:-/etc/searxng/settings.yml}"
    if [ ! -f "$SEARXNG_SETTINGS_PATH" ] && [ -f "config/settings.yml" ]; then
        export SEARXNG_SETTINGS_PATH="$(pwd)/config/settings.yml"
    fi
    python -m searx.webapp > searxng.log 2>&1 &
    SEARXNG_PID=$!
    echo "⏳ Initializing SearXNG (PID: $SEARXNG_PID)..."
    sleep 2
fi

# 2. Start Streamlit Dashboard
echo "🌐 Launching Aegis Streamlit Web Interface..."
streamlit run app.py
