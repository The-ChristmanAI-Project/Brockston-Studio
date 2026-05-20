# ==============================================================================
# Patent Pending
# Christman-AI Family
# Shared-neutral implementation for internal system use.
# ==============================================================================

"""
Brockston Studio - Ollama Integration Client

Bridge for communicating with local Ollama models.
Supports chat, code suggestions, and analysis.
Routes through Brockston API pipeline first.
Falls back to raw Ollama if API is offline.
"""

import re
import logging
import httpx

logger = logging.getLogger(__name__)


class BrockstonClient:
    """
    Async client for interacting with Ollama models.
    Use as async context manager or call close() when done.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5-coder:32b",
        timeout: float = 120.0
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

        logger.info(f"BrockstonClient initialized → {self.base_url}")
        logger.info(f"Model: {self.model}")

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def close(self):
        """Release the underlying HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        """Return active client or create a one-shot client."""
        if self._client:
            return self._client
        return httpx.AsyncClient(timeout=self.timeout)

    # ------------------------------------------------------------------
    # Core chat
    # ------------------------------------------------------------------

    async def chat(
        self,
        messages: list[dict],
        context: dict | None = None
    ) -> str:
        """
        Send a chat request to Ollama.

        Args:
            messages: List of {"role": ..., "content": ...} dicts
            context: Optional {"path": ..., "code": ..., "language": ...}
                     Injected as a system message if provided.

        Returns:
            Response text from the model
        """
        try:
            # Inject context as a leading system message if provided
            if context:
                context_parts = []
                if context.get("path"):
                    context_parts.append(f"File: {context['path']}")
                if context.get("language"):
                    context_parts.append(f"Language: {context['language']}")
                if context.get("code"):
                    context_parts.append(f"Current code:\n```\n{context['code']}\n```")
                if context_parts:
                    messages = [
                        {"role": "system", "content": "\n".join(context_parts)}
                    ] + messages

            client = self._get_client()
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                }
            )

            if response.status_code != 200:
                logger.error(f"Ollama error: {response.status_code} — {response.text[:200]}")
                return f"Error from model: {response.status_code}"

            reply = response.json().get("message", {}).get("content", "")
            return reply if reply else "No response from model"

        except httpx.ConnectError:
            logger.warning("Ollama unreachable on port 11434")
            return "Ollama is offline. Start it with: ollama serve"
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return f"Error: {e}"

    # ------------------------------------------------------------------
    # Code fix / suggestion
    # ------------------------------------------------------------------

    async def suggest_fix(
        self,
        code: str,
        instruction: str,
        path: str | None = None,
        language: str | None = None
    ) -> dict:
        """
        Ask the model to fix or improve a code snippet.

        Args:
            code:        The code to analyze
            instruction: What to fix or improve
            path:        Optional file path for context
            language:    Optional language hint

        Returns:
            {"suggestion": str, "fixed_code": str}
        """
        lang_hint = language or "code"
        file_hint = f"File: {path}" if path else ""

        prompt = (
            f"You are an expert {lang_hint} engineer.\n"
            f"{file_hint}\n\n"
            f"Task: {instruction}\n\n"
            f"```{lang_hint}\n{code}\n```\n\n"
            "Provide a clear explanation of your changes, then provide "
            "the complete corrected code inside a single code block."
        ).strip()

        try:
            client = self._get_client()
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                }
            )

            if response.status_code != 200:
                logger.error(f"suggest_fix error: {response.status_code}")
                return {"suggestion": "Error contacting model", "fixed_code": code}

            full_response = response.json().get("message", {}).get("content", "")
            fixed = self._extract_code_block(full_response)

            return {
                "suggestion": full_response,
                "fixed_code": fixed if fixed else code
            }

        except Exception as e:
            logger.error(f"suggest_fix error: {e}")
            return {"suggestion": f"Error: {e}", "fixed_code": code}

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------

    async def get_embedding(self, text: str) -> list[float]:
        """
        Get a text embedding from Ollama.
        Used for semantic search / memory retrieval.
        """
        try:
            client = self._get_client()
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": "qwen3-embedding:latest", "prompt": text},
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json().get("embedding", [])
        except Exception as e:
            logger.error(f"Embedding error: {e}")
        return []

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    async def health(self) -> dict:
        """Check Ollama status and list available models."""
        try:
            client = self._get_client()
            response = await client.get(
                f"{self.base_url}/api/tags",
                timeout=5.0
            )
            if response.status_code == 200:
                models = [m["name"] for m in response.json().get("models", [])]
                return {"ollama": "online", "models": models}
        except Exception:
            pass
        return {"ollama": "offline", "models": []}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_code_block(self, text: str) -> str:
        """
        Pull the first code block out of a markdown response.
        Falls back to stripping all fences if no block found.
        """
        match = re.search(r"```[\w]*\n?(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        # No fences at all — clean and return full text
        return re.sub(r"```[\w]*\n?", "", text).replace("```", "").strip()


# ==============================================================================
# Patent pending — The Christman AI Project
# ==============================================================================