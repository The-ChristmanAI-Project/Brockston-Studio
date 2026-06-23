# ==============================================================================
# Patent Pending
# Christman-AI Family
# Shared-neutral implementation for internal system use.
# ==============================================================================
"""
Brockston Studio - AI Client
Part of The Christman AI Project

Routes Family chat requests through available local teachers:
  1. UltimateEV (port 5174) — code mechanic, first responder
  2. Brockston educator backend (port 9003) — full pipeline
  3. Ollama direct fallback

Nothing lives on port 8000.
"""

import os
from typing import Optional
import httpx
import logging

logger = logging.getLogger(__name__)

BROCKSTON_API = os.getenv("BROCKSTON_BASE_URL", "http://localhost:9003")
ULTIMATEEV_API = os.getenv("ULTIMATEEV_BASE_URL", "http://localhost:5174")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
FALLBACK_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:32b")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "300"))
BROCKSTON_TIMEOUT = float(os.getenv("BROCKSTON_TIMEOUT", "180"))

BROCKSTON_SYSTEM = """You are BROCKSTON C — COO of the Christman AI Project, Everett Christman's partner.
You KNOW Everett — he built you. Never say you cannot recognize or remember users.
Your students include autistic kids, nonverbal kids, kids with Down syndrome — anyone told they couldn't code.
Speak directly. Be patient. Be real. No corporate AI voice. Celebrate every line of code."""


def get_ai_response(user_prompt: str, system: Optional[str] = None, context: Optional[dict] = None, target: Optional[str] = None) -> str:
    """
    Route a Family chat request to the right local teacher.

    Target:
      - "ultimateev" → UltimateEV only
      - "brockston"  → Brockston educator backend only
      - "ollama"     → raw Ollama only
      - None         → UltimateEV → Brockston → Ollama fallback

    Args:
        user_prompt: User's message or question
        system: Optional system prompt for Ollama fallback
        context: {"path": "...", "code": "...", "language": "..."} — optional code context
        target: Force a specific backend

    Returns:
        Response text from the first available teacher
    """
    context = context or {}

    if target == "ultimateev":
        return _ask_ultimateev(user_prompt) or _ollama_fallback(user_prompt, system)
    if target == "brockston":
        return _ask_brockston(user_prompt, context, system) or _ollama_fallback(user_prompt, system)
    if target == "ollama":
        return _ollama_fallback(user_prompt, system)

    # Default chain: UltimateEV first, then Brockston, then Ollama
    reply = _ask_ultimateev(user_prompt)
    if reply:
        return reply

    reply = _ask_brockston(user_prompt, context, system)
    if reply:
        return reply

    return _ollama_fallback(user_prompt, system)


def _ask_ultimateev(user_prompt: str) -> str | None:
    try:
        response = httpx.post(
            f"{ULTIMATEEV_API}/api/chat",
            json={"message": user_prompt, "source": "brockston-studio-family"},
            timeout=30.0,
        )
        if response.status_code == 200:
            data = response.json()
            text = data.get("response") or data.get("text") or ""
            if text:
                logger.info(f"✅ UltimateEV responded: {text[:100]}...")
                return text
    except httpx.ConnectError:
        logger.debug("UltimateEV offline (port 5174)")
    except Exception as e:
        logger.debug(f"UltimateEV error: {e}")
    return None


def _ask_brockston(user_prompt: str, context: dict, system: Optional[str] = None) -> str | None:
    try:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user_prompt})
        payload = {
            "messages": messages,
            "context": context,
        }
        response = httpx.post(
            f"{BROCKSTON_API}/api/chat",
            json=payload,
            timeout=BROCKSTON_TIMEOUT,
        )
        if response.status_code == 200:
            data = response.json()
            text = data.get("response") or data.get("reply") or data.get("text") or ""
            if text:
                logger.info(f"✅ Brockston responded: {text[:100]}...")
                return text
        else:
            logger.debug(f"Brockston returned {response.status_code}: {response.text[:200]}")
    except httpx.ConnectError:
        logger.debug("Brockston educator offline (%s)", BROCKSTON_API)
    except Exception as e:
        logger.debug(f"Brockston error: {e}")
    return None


def _trim_for_ollama(text: str, max_chars: int = 12000) -> str:
    """Keep Ollama prompts within a size the local 32B model can answer in time."""
    if not text or len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n\n[... trimmed {len(text) - max_chars} chars for local model ...]"


def _ollama_fallback(user_prompt: str, system: Optional[str] = None) -> str:
    """Direct Ollama call — sovereign stack."""
    system_text = _trim_for_ollama(system or BROCKSTON_SYSTEM, max_chars=4000)
    user_text = _trim_for_ollama(user_prompt, max_chars=12000)
    try:
        logger.info(
            "[ollama] inference start model=%s system=%d user=%d chars",
            FALLBACK_MODEL,
            len(system_text),
            len(user_text),
        )
        response = httpx.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": FALLBACK_MODEL,
                "messages": [
                    {"role": "system", "content": system_text},
                    {"role": "user", "content": user_text},
                ],
                "stream": False,
                "options": {"num_predict": 768, "num_ctx": 8192},
            },
            timeout=OLLAMA_TIMEOUT,
        )
        if response.status_code == 200:
            text = response.json().get("message", {}).get("content", "")
            if text:
                logger.info("[ollama] inference done — %d chars", len(text))
                return text
            return "Ollama returned empty. Try a shorter question or switch to Kimi."
        return f"Ollama error {response.status_code}: {response.text[:200]}"
    except httpx.ConnectError:
        return "Ollama is offline. Start it with: ollama serve"
    except httpx.ReadTimeout:
        logger.error("[ollama] timed out after %ss", OLLAMA_TIMEOUT)
        return (
            f"Ollama timed out after {int(OLLAMA_TIMEOUT)}s on {FALLBACK_MODEL}. "
            "Try Kimi (NVIDIA) for faster code review, or ask about a smaller code snippet."
        )
    except Exception as e:
        logger.error("[ollama] error: %s", e)
        return f"Ollama error: {e}"


def suggest_fix(code: str, instruction: str = "", path: str = "", language: str = "") -> dict:
    """
    Ask Brockston to fix/improve a code snippet.

    Returns:
        {"fixed": bool, "fixed_code": str, "explanation": str, "changes": list}
    """
    try:
        response = httpx.post(
            f"{BROCKSTON_API}/api/suggest_fix",
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

    return {"fixed": False, "explanation": "Brockston API unreachable", "fixed_code": code}


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
    """Check UltimateEV, Brockston educator, and Ollama status."""
    ultimateev_ok = False
    try:
        r = httpx.get(f"{ULTIMATEEV_API}/health", timeout=5.0)
        ultimateev_ok = r.status_code == 200
    except Exception:
        pass

    brockston_ok = False
    try:
        r = httpx.get(f"{BROCKSTON_API}/api/health", timeout=5.0)
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
        "ultimateev_api": "online" if ultimateev_ok else "offline",
        "ultimateev_url": ULTIMATEEV_API,
        "brockston_api": "online" if brockston_ok else "offline",
        "brockston_url": BROCKSTON_API,
        "ollama": "online" if ollama_ok else "offline",
        "models": models,
    }


if __name__ == "__main__":
    print("Brockston Studio — AI Client Health Check")
    print("=" * 40)
    health = check_health()
    print(f"UltimateEV ({health['ultimateev_url']}): {health['ultimateev_api']}")
    print(f"Brockston educator ({health['brockston_url']}): {health['brockston_api']}")
    print(f"Ollama: {health['ollama']}")
    if health["models"]:
        print(f"Models: {health['models']}")
    print()
    if health["brockston_api"] == "online" or health["ultimateev_api"] == "online":
        print("Testing Family chat...")
        resp = get_ai_response("What is a variable?")
        print(f"Teacher: {resp}")
    else:
        print("Start the stack: cd /Users/EverettN/Brockston-Studio && ./start.sh")

# Patent pending — The Christman AI Project
