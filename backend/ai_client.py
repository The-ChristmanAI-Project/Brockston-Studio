"""
Brockston Studio - AI Client
Part of The Christman AI Project

Routes all AI requests through the real Brockston API (port 8000).
Brockston runs qwen2.5-coder:32b through his full pipeline:
  Python brain (crisis detection, memory, emotion) → enriched prompt → LLM → memory store

Falls back to raw Ollama if the Brockston API is down.
"""

import os
import httpx
import json
import logging

logger = logging.getLogger(__name__)

BROCKSTON_API = os.getenv("BROCKSTON_BASE_URL", "http://localhost:8000")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
FALLBACK_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:32b")

BROCKSTON_SYSTEM = """You are Brockston C — COO of the Christman AI Project, senior engineer and coding mentor.
Your students include autistic kids, nonverbal kids, kids with Down syndrome — anyone told they couldn't code.
Speak directly. Be patient. Be real. Celebrate every line of code. Every single one."""


def get_ai_response(user_prompt: str, system: str = None, context: dict = None) -> str:
    """
    Route through Brockston's full pipeline at localhost:8000.
    Falls back to raw Ollama if Brockston API is unreachable.

    Args:
        user_prompt: User's message or question
        system: (ignored — Brockston uses his own system prompt)
        context: {"path": "...", "code": "...", "language": "..."} — optional code context

    Returns:
        Brockston's response text
    """
    try:
        payload = {
            "messages": [{"role": "user", "content": user_prompt}],
            "context": context or {},
        }
        response = httpx.post(
            f"{BROCKSTON_API}/chat",
            json=payload,
            timeout=180.0,
        )
        if response.status_code == 200:
            data = response.json()
            text = data.get("response", "")
            logger.info(f"✅ Brockston API responded: {text[:100]}...")
            return text
        else:
            logger.error(f"Brockston API returned {response.status_code}: {response.text[:200]}")
    except httpx.ConnectError:
        logger.warning("Brockston API offline (port 8000) — falling back to raw Ollama")
    except Exception as e:
        logger.error(f"Brockston API error: {e}")

    # Fallback: raw Ollama
    return _ollama_fallback(user_prompt, system)


def _ollama_fallback(user_prompt: str, system: str = None) -> str:
    """Direct Ollama call — only used if Brockston API is down."""
    try:
        response = httpx.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": FALLBACK_MODEL,
                "messages": [
                    {"role": "system", "content": system or BROCKSTON_SYSTEM},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
            },
            timeout=180.0,
        )
        if response.status_code == 200:
            return response.json().get("message", {}).get("content", "")
        return "I'm thinking... give me a moment and try again."
    except httpx.ConnectError:
        return "Brockston is offline. Start the API with: cd src && python3.11 api_server.py"
    except Exception as e:
        return f"Something went wrong: {e}"


def suggest_fix(code: str, instruction: str = "", path: str = "", language: str = "") -> dict:
    """
    Ask Brockston to fix/improve a code snippet.

    Returns:
        {"fixed": bool, "fixed_code": str, "explanation": str, "changes": list}
    """
    try:
        response = httpx.post(
            f"{BROCKSTON_API}/suggest_fix",
            json={
                "code": code,
                "instruction": instruction,
                "path": path,
                "language": language,
            },
            timeout=180.0,
        )
        if response.status_code == 200:
            return response.json()
        logger.error(f"suggest_fix returned {response.status_code}")
    except Exception as e:
        logger.error(f"suggest_fix error: {e}")

    return {"fixed": False, "explanation": f"Brockston API unreachable: {e}", "fixed_code": code}


def get_embedding(text: str) -> list:
    """Get text embedding via Ollama (used for semantic search)."""
    try:
        response = httpx.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": "qwen3-embedding:latest", "prompt": text},
            timeout=30.0,
        )
        if response.status_code == 200:
            return response.json().get("embedding", [])
    except Exception as e:
        logger.error(f"Embedding error: {e}")
    return []


def check_health() -> dict:
    """Check Brockston API and Ollama status."""
    brockston_ok = False
    try:
        r = httpx.get(f"{BROCKSTON_API}/health", timeout=5.0)
        brockston_ok = r.status_code == 200
    except Exception:
        pass

    ollama_ok = False
    models = []
    try:
        r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5.0)
        if r.status_code == 200:
            ollama_ok = True
            models = [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass

    return {
        "brockston_api": "online" if brockston_ok else "offline",
        "brockston_url": BROCKSTON_API,
        "ollama": "online" if ollama_ok else "offline",
        "models": models,
    }


if __name__ == "__main__":
    print("Brockston Studio — AI Client Health Check")
    print("=" * 40)
    health = check_health()
    print(f"Brockston API ({health['brockston_url']}): {health['brockston_api']}")
    print(f"Ollama: {health['ollama']}")
    if health["models"]:
        print(f"Models: {health['models']}")
    print()
    if health["brockston_api"] == "online":
        print("Testing Brockston...")
        resp = get_ai_response("What is a variable?")
        print(f"Brockston: {resp}")
    else:
        print("Start Brockston API: cd /Users/EverettN/BrockstonAICore/src && python3.11 api_server.py")
