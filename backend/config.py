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
# This resolves to /Users/EverettN/Brockston-Studio
BASE_DIR = Path(__file__).resolve().parent.parent

# Server configuration
HOST = os.getenv("BROCKSTON_HOST", "127.0.0.1")
PORT = int(os.getenv("BROCKSTON_PORT", "7777"))

# Model Settings
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL_CODER = os.getenv("LLM_MODEL_CODER", "qwen2.5-coder:32b")
LLM_MODEL_GENERAL = os.getenv("LLM_MODEL_GENERAL", "qwen2.5-coder:32b")

# Workspace Settings
# Pointing directly to the project root for v1
BROCKSTON_WORKSPACE = str(BASE_DIR.resolve())

# Final resolution check
BROCKSTON_WORKSPACE = str(Path(BROCKSTON_WORKSPACE).expanduser().resolve())

print(f"--- BROCKSTON CONFIG LOADED ---")
print(f"Workspace: {BROCKSTON_WORKSPACE}")
print(f"Backend:   {HOST}:{PORT}")
print(f"Ollama:    {OLLAMA_BASE_URL}")
print(f"-------------------------------")

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug(f"Workspace: {BROCKSTON_WORKSPACE}")

# Patent pending — The Christman AI Project
