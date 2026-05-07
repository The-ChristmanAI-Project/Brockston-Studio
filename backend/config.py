"""
BROCKSTON Studio Configuration
Centralized settings for the environment.
"""

import os
from pathlib import Path

# Base directory of the project
# This resolves to /Users/EverettN/Brockston-IDE-Studio
BASE_DIR = Path(__file__).resolve().parent.parent

<<<<<<< HEAD
# Server Settings
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5055
=======
# Server configuration
HOST = os.getenv("BROCKSTON_HOST", "127.0.0.1")
PORT = int(os.getenv("BROCKSTON_PORT", "5055"))
>>>>>>> dbb5f601697d6dc0f41d9b98198aeded8fa706bc

# Model Settings
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL_CODER = "qwen2.5-coder:32b"
LLM_MODEL_GENERAL = os.getenv("LLM_MODEL_GENERAL", "llama3.2:3b")

# Workspace Settings
# Pointing directly to the project root for v1
BROCKSTON_WORKSPACE = str(BASE_DIR.resolve())

# Final resolution check
BROCKSTON_WORKSPACE = str(Path(BROCKSTON_WORKSPACE).expanduser().resolve())

print(f"--- BROCKSTON CONFIG LOADED ---")
print(f"Workspace: {BROCKSTON_WORKSPACE}")
print(f"Backend:   {SERVER_HOST}:{SERVER_PORT}")
print(f"Ollama:    {OLLAMA_BASE_URL}")
print(f"-------------------------------")
