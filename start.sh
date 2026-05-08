#!/bin/bash

# BROCKSTON Studio Startup Script

echo "========================================="
echo "  BROCKSTON Studio"
echo "  Local Code Workbench"
echo "========================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if dependencies are installed
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Load .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env"
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

# Set default environment variables if not already set
export BROCKSTON_HOST="${BROCKSTON_HOST:-127.0.0.1}"
export BROCKSTON_PORT="${BROCKSTON_PORT:-5055}"
export BROCKSTON_BASE_URL="${BROCKSTON_BASE_URL:-http://localhost:6006}"
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
export LLM_PROVIDER="${LLM_PROVIDER:-ollama}"
export LLM_MODEL_GENERAL="${LLM_MODEL_GENERAL:-llama3.2:3b}"
export LLM_MODEL_CODER="${LLM_MODEL_CODER:-qwen2.5-coder:32b}"
export LLM_MODEL="${LLM_MODEL:-$LLM_MODEL_GENERAL}"

echo "Configuration:"
echo "  Host: $BROCKSTON_HOST"
echo "  Port: $BROCKSTON_PORT"
echo "  BROCKSTON URL: $BROCKSTON_BASE_URL"
echo "  Ollama URL: $OLLAMA_BASE_URL"
echo "  LLM Provider: $LLM_PROVIDER"
echo "  LLM Model (general): $LLM_MODEL_GENERAL"
echo "  LLM Model (coder): $LLM_MODEL_CODER"
echo ""
echo "Starting server..."
echo "Open http://localhost:$BROCKSTON_PORT in your browser"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start the server
python3 -m uvicorn backend.main:app \
    --host "$BROCKSTON_HOST" \
    --port "$BROCKSTON_PORT" \
    --reload
