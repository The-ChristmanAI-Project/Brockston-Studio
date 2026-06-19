"""
NVIDIA Nemotron 3 Ultra — Brockston Studio Research Engine
===========================================================
Replaces Perplexity Sonar as the selectable research instructor
in Brockston Studio. Routes through OpenRouter's free tier.

Model: nvidia/nemotron-3-ultra-550b-a55b:free
  - 55B active / 550B total parameters (MoE)
  - Hybrid Transformer-Mamba architecture
  - 1M token context window
  - $0 input / $0 output via OpenRouter free tier
  - Strong multi-step reasoning, agentic workflows, deep research

Environment variable required:
    OPENROUTER_API_KEY — get one at https://openrouter.ai/keys

Drop-in replacement for PerplexityService:
    Same is_available property
    Same generate_content() signature
    Same raise-on-failure behavior (Rule 6: Fail Loud)

© 2026 Everett Nathaniel Christman & The Christman AI Project
Cardinal Rule 1: It actually works.
Cardinal Rule 6: Fail loud — no silent failures.
Cardinal Rule 13: No hallucinations. No invented sources.
"""

import os
import json
import logging
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL      = "nvidia/nemotron-3-ultra-550b-a55b:free"


class NemotronService:
    """
    NVIDIA Nemotron 3 Ultra via OpenRouter.

    Drop-in replacement for PerplexityService — same interface,
    same error contract, same Cardinal Rule compliance.
    """

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model   = model
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self._available = False

        if not self.api_key:
            logger.warning(
                "[NemotronService] OPENROUTER_API_KEY not set — "
                "Nemotron research engine will not be available. "
                "Add OPENROUTER_API_KEY to your .env to enable it."
            )
            return

        self._available = True
        logger.info(
            f"[NemotronService] NVIDIA Nemotron 3 Ultra online — "
            f"model: {self.model} — 1M context, free tier, ready."
        )

    @property
    def is_available(self) -> bool:
        """True if OpenRouter key is configured and service is ready."""
        return self._available

    def generate_content(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        recency_filter: Optional[str] = None,      # accepted, not used (Perplexity-compat)
        domain_filter: Optional[List[str]] = None,  # accepted, not used (Perplexity-compat)
        search_mode: str = "web",                   # accepted, not used (Perplexity-compat)
    ) -> str:
        """
        Send a prompt to Nemotron 3 Ultra via OpenRouter and return the response.

        Args:
            prompt:        The question or task.
            system_prompt: Optional system context. Defaults to Brockston instructor persona.
            max_tokens:    Max tokens in response (default 1024).
            recency_filter, domain_filter, search_mode:
                           Accepted for Perplexity API compatibility — not forwarded.

        Returns:
            str: Model response text.

        Raises:
            RuntimeError: On any failure (Rule 6 — loud, not silent).
        """
        if not self.is_available:
            raise RuntimeError(
                "[NemotronService] Research engine not available. "
                "Set OPENROUTER_API_KEY in your .env file."
            )

        if not system_prompt:
            system_prompt = (
                "You are Brockston's research engine — powered by NVIDIA Nemotron 3 Ultra. "
                "You reason carefully, answer precisely, and never invent facts. "
                "When you don't know something, say so. "
                "Cardinal Rule 13: Absolute honesty. No hallucinations."
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": prompt},
        ]

        payload: Dict[str, Any] = {
            "model":      self.model,
            "messages":   messages,
            "max_tokens": max_tokens,
        }

        try:
            logger.info(
                f"[NemotronService] Querying: {prompt[:80]}... "
                f"(model={self.model})"
            )

            req = urllib.request.Request(
                OPENROUTER_API_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type":  "application/json",
                    "Accept":        "application/json",
                    "HTTP-Referer":  "https://brockston.studio",
                    "X-Title":       "Brockston Studio — The Christman AI Project",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            answer = data["choices"][0]["message"]["content"]
            logger.info("[NemotronService] Response received.")
            return answer

        except urllib.error.URLError as e:
            logger.error(f"[NemotronService] Network error: {e}", exc_info=True)
            raise RuntimeError(
                f"Nemotron network error: {e}. Check your internet connection."
            )
        except Exception as e:
            logger.error(f"[NemotronService] Request failed: {e}", exc_info=True)
            raise RuntimeError(
                f"Nemotron request failed: {e}. Check your OPENROUTER_API_KEY."
            )

    # ------------------------------------------------------------------
    # Convenience aliases matching PerplexityService helper methods
    # ------------------------------------------------------------------

    def search_code(self, query: str, language: Optional[str] = None) -> str:
        """Code-focused query — mirrors PerplexityService.search_code()."""
        focused = f"{language}: {query}" if language else query
        system = (
            "You are finding coding information for Brockston Studio. "
            "Return working, tested code examples. Explain what the code does and why. "
            "Flag known pitfalls. Cite official documentation where relevant. "
            "No hallucinated APIs. No invented package names."
        )
        return self.generate_content(focused, system_prompt=system, max_tokens=1500)

    def search_current_events(self, query: str) -> str:
        """Current events query — mirrors PerplexityService.search_current_events()."""
        return self.generate_content(query, max_tokens=800)

    def search_academic(self, query: str) -> str:
        """Academic/research query — mirrors PerplexityService.search_academic()."""
        return self.generate_content(query, max_tokens=1200)


# =============================================================================
# SINGLETON
# =============================================================================

_nemotron_instance: Optional[NemotronService] = None


def get_nemotron_service(model: str = DEFAULT_MODEL) -> NemotronService:
    """Get or create the shared Nemotron service instance."""
    global _nemotron_instance
    if _nemotron_instance is None:
        _nemotron_instance = NemotronService(model=model)
    return _nemotron_instance


# =============================================================================
# © 2026 Everett Nathaniel Christman & The Christman AI Project
# Luma Cognify AI — "How can we help you love yourself more?"
#
# Nemotron Ultra: 550B parameters. 1M context. Free.
# The research engine Brockston deserves.
# Cardinal Rule 13: No hallucinations. No invented sources. Truth only.
# =============================================================================
