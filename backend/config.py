# ==============================================================================
# Patent Pending
# Christman-AI Family
# Shared-neutral implementation for internal system use.
# ==============================================================================



"""
Brockston-Studio configuration — this IDE repo only.
Not the separate BROCKSTON sovereign stack (~/BROCKSTON).
"""

import os
from pathlib import Path


def _env_first(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return default


# Base directory of the project (this repo)
BASE_DIR = Path(__file__).resolve().parent.parent

# Brockston-Studio server bind + educator API (backend/launcher.py)
HOST = _env_first("STUDIO_HOST", "BROCKSTON_HOST", default="127.0.0.1")
PORT = int(_env_first("STUDIO_BACKEND_PORT", "BROCKSTON_PORT", default="9003"))

# Model Settings
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# GENERAL for chat, vocal, being-to-being comms (fast/low-latency)
LLM_MODEL_GENERAL = os.getenv("LLM_MODEL_GENERAL", "llama3.2")
# CODER for heavy code work, suggest, analysis (can be large/slow)
LLM_MODEL_CODER = os.getenv("LLM_MODEL_CODER", "qwen2.5-coder:32b")

# Studio IDE default project folder (explorer + terminal start here).
# Not the Brockston educator backend — set STUDIO_WORKSPACE in .env (e.g. ~/Code).
_STUDIO_WS_RAW = os.getenv("STUDIO_WORKSPACE") or os.getenv("BROCKSTON_WORKSPACE")
STUDIO_WORKSPACE = str(
    Path(_STUDIO_WS_RAW or str(BASE_DIR.resolve())).expanduser().resolve()
)
BROCKSTON_WORKSPACE = STUDIO_WORKSPACE  # deprecated alias

print(f"--- Brockston-Studio config ---")
print(f"Workspace:      {STUDIO_WORKSPACE}")
print(f"Studio backend: {HOST}:{PORT}")
print(f"Ollama:    {OLLAMA_BASE_URL}")
print(f"GENERAL (chat/vocal): {LLM_MODEL_GENERAL}")
print(f"CODER (heavy):        {LLM_MODEL_CODER}")
print(f"-------------------------------")

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Patent pending — The Christman AI Project
