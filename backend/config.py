# ==============================================================================
# Patent Pending
# Christman-AI Family
# Shared-neutral implementation for internal system use.
# ==============================================================================



"""
BROCKSTON Studio Configuration
Centralized settings for the environment.
"""

import os
from pathlib import Path


# Base directory of the project
# Resolves to this repo unless BROCKSTON_WORKSPACE is set in .env
BASE_DIR = Path(__file__).resolve().parent.parent

# Server configuration
HOST = os.getenv("BROCKSTON_HOST", "127.0.0.1")
PORT = int(os.getenv("BROCKSTON_PORT", "9003"))

# Model Settings
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# GENERAL for chat, vocal, being-to-being comms (fast/low-latency)
LLM_MODEL_GENERAL = os.getenv("LLM_MODEL_GENERAL", "llama3.2")
# CODER for heavy code work, suggest, analysis (can be large/slow)
LLM_MODEL_CODER = os.getenv("LLM_MODEL_CODER", "qwen2.5-coder:32b")

# Workspace Settings — single source of truth for beings + IDE file ops
BROCKSTON_WORKSPACE = str(
    Path(os.getenv("BROCKSTON_WORKSPACE", str(BASE_DIR.resolve()))).expanduser().resolve()
)

print(f"--- BROCKSTON CONFIG LOADED ---")
print(f"Workspace: {BROCKSTON_WORKSPACE}")
print(f"Backend:   {HOST}:{PORT}")
print(f"Ollama:    {OLLAMA_BASE_URL}")
print(f"GENERAL (chat/vocal): {LLM_MODEL_GENERAL}")
print(f"CODER (heavy):        {LLM_MODEL_CODER}")
print(f"-------------------------------")

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Patent pending — The Christman AI Project
