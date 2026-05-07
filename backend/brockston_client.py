"""
BROCKSTON Client - Ollama Integration

Bridge for communicating with local Ollama models.
Supports chat, code suggestions, and analysis.
"""

import httpx
import json
import logging
import re
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class BrockstonClient:
    """
    Client for interacting with BROCKSTON models via Ollama.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5-coder:32b",
        timeout: float = 120.0
    ):
        """Initialize BROCKSTON client pointing to Ollama."""
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

        logger.info(f"BROCKSTON client initialized with endpoint: {self.base_url}")
        logger.info(f"Model: {self.model}")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        context: Optional[Dict] = None
    ) -> str:
        """
        Send a chat request to Ollama and get a response.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            context: Optional additional context (currently unused)
        
        Returns:
            Response text from the model
        """
        try:
            # Extract the last user message
            user_message = None
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_message = msg.get("content", "")
                    break

            if not user_message:
                return "No user message provided"

            # Call Ollama chat API
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                }
            )

            if response.status_code != 200:
                logger.error(f"Ollama error: {response.status_code} - {response.text}")
                return f"Error from model: {response.status_code}"

            data = response.json()
            reply = data.get("message", {}).get("content", "")

            return reply if reply else "No response from model"

        except Exception as e:
            logger.error(f"Chat error: {e}")
            return f"Error: {str(e)}"

    async def suggest_fix(
        self,
        code: str,
        instruction: str,
        path: Optional[str] = None
    ) -> Dict:
        """
        Suggest fixes for code based on instruction.
        
        Args:
            code: The code to analyze
            instruction: What to fix or improve
            path: Optional file path for context
        
        Returns:
            Dict with 'suggestion' and 'fixed_code' keys
        """
        try:
            prompt = f"""You are a code expert. Analyze the following code and {instruction}.

File: {path or 'unknown'}

```
{code}
```

Provide a clear suggestion and corrected code."""

            messages = [
                {"role": "user", "content": prompt}
            ]

            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                }
            )

            if response.status_code != 200:
                logger.error(f"Ollama error: {response.status_code}")
                return {"suggestion": "Error contacting model", "fixed_code": code}

            data = response.json()
            suggestion = data.get("message", {}).get("content", "")

            return {
                "suggestion": suggestion,
                "fixed_code": code
            }

        except Exception as e:
            logger.error(f"Suggest fix error: {e}")
            return {
                "suggestion": f"Error: {str(e)}",
                "fixed_code": code
            }

    def _clean_code_response(self, text: str) -> str:
        """Remove markdown code fences from response."""
        text = re.sub(r'```[\w]*\n?', '', text)
        text = re.sub(r'```', '', text)
        return text.strip()
