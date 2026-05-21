"""
DerekMCPServer's Search Engine — Powered by Perplexity Sonar
=========================================================
DerekMCPServer doesn't guess when he can know.
When the system needs current, real-world information,
DerekMCPServer reaches out through Perplexity and brings back grounded,
cited answers — not hallucinations.

This module is the real implementation of live research capabilities.
It uses native Python libraries (no OpenAI SDK wrapper required).

Usage:
    from perplexity_service import PerplexityService
    search = PerplexityService()
    result = search.generate_content("What are the latest updates to the USPTO guidelines?")

Environment variable required:
    PERPLEXITY_API_KEY — get one at https://www.perplexity.ai/settings/api

© 2026 Everett Nathaniel Christman & The Christman AI Project
Cardinal Rule 1: It actually works.
Cardinal Rule 6: Fail loud — no silent search failures.
Cardinal Rule 13: Citations included. No hallucinations.
"""

import os
import json
import logging
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Perplexity API endpoint
PERPLEXITY_BASE_URL = "https://api.perplexity.ai"

# Model selection:
# sonar       — Fast, grounded, cost-efficient. Good for most queries.
# sonar-pro   — Deeper search, more sources, better for complex questions.
DEFAULT_MODEL = "sonar-pro"
FAST_MODEL = "sonar"


class PerplexityService:
    """
    DerekMCPServer's live search engine — Perplexity Sonar.

    Gives DerekMCPServer access to current, real-world information with citations.
    Every response is grounded in actual web sources, not training data alone.
    """

    def __init__(self, model: str = DEFAULT_MODEL):
        """
        Initialize the Perplexity search client natively.

        Args:
            model: Perplexity model to use. Default: sonar-pro.
        """
        self.model = model
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self._available = False

        if not self.api_key:
            logger.warning(
                "[PerplexityService] PERPLEXITY_API_KEY not set — "
                "search engine will not be available. "
                "Set PERPLEXITY_API_KEY to enable DerekMCPServer's live search."
            )
            return

        self._available = True
        logger.info(
            f"[PerplexityService] Search engine online — "
            f"model: {self.model} — DerekMCPServer can see the world."
        )

    @property
    def is_available(self) -> bool:
        """True if Perplexity is configured and ready."""
        return self._available

    def generate_content(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        recency_filter: Optional[str] = None,
        domain_filter: Optional[List[str]] = None,
        search_mode: str = "web",
    ) -> str:
        """
        Search the web and return a grounded, cited answer using native urllib.

        Args:
            prompt: The question or query to search
            system_prompt: Optional system context
            max_tokens: Max tokens in response (default 1024)
            recency_filter: Limit results by age — "day", "week", "month", "year"
            domain_filter: Limit to specific domains e.g. ["github.com", "docs.python.org"]
            search_mode: "web" (default), "academic", or "sec"

        Returns:
            str: Grounded answer with citations inline

        Raises:
            RuntimeError: If search fails (Rule 6 — loud, not silent)
        """
        if not self.is_available:
            raise RuntimeError(
                "[PerplexityService] Search engine not available. "
                "Set PERPLEXITY_API_KEY environment variable."
            )

        if not system_prompt:
            system_prompt = (
                "You are DerekMCPServer's search engine — powered by Perplexity. "
                "You find real, current, grounded information and return it with "
                "source citations. You do not hallucinate. You do not invent sources. "
                "If you don't find it, say so. Cardinal Rule 13: Absolute honesty."
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        # Build the payload for the direct API call
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "return_related_questions": False,
        }
        
        # Add optional filters if the API supports them directly in the root
        if recency_filter:
            payload["search_recency_filter"] = recency_filter
        if domain_filter:
            payload["search_domain_filter"] = domain_filter

        try:
            logger.info(
                f"[PerplexityService] Searching: {prompt[:80]}... "
                f"(model={self.model})"
            )
            
            # Make the native HTTP request
            req = urllib.request.Request(
                f"{PERPLEXITY_BASE_URL}/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=120) as resp:
                response_data = json.loads(resp.read().decode("utf-8"))

            # Extract the content
            answer = response_data["choices"][0]["message"]["content"]

            # Append citations if returned by the Perplexity API
            citations = response_data.get("citations", [])
            if citations:
                citation_block = "\n\nSources:\n" + "\n".join(
                    f"  [{i+1}] {url}" for i, url in enumerate(citations[:5])
                )
                answer = answer + citation_block

            logger.info("[PerplexityService] Search complete.")
            return answer

        except urllib.error.URLError as e:
            logger.error(f"[PerplexityService] Network error: {e}", exc_info=True)
            raise RuntimeError(
                f"Perplexity search network failed: {e}. "
                "Check your internet connection."
            )
        except Exception as e:
            logger.error(f"[PerplexityService] Search failed: {e}", exc_info=True)
            raise RuntimeError(
                f"Perplexity search failed: {e}. "
                "Check your PERPLEXITY_API_KEY."
            )

    def search_code(self, query: str, language: Optional[str] = None) -> str:
        """
        Search specifically for coding information — docs, examples, best practices.

        Args:
            query: Coding question or concept
            language: Optional programming language to focus on

        Returns:
            str: Code-focused answer with sources
        """
        focused_query = query
        if language:
            focused_query = f"{language}: {query}"

        code_domains = [
            "docs.python.org",
            "github.com",
            "stackoverflow.com",
            "developer.mozilla.org",
            "docs.rs",
            "docs.anthropic.com",
            "platform.openai.com",
            "pytorch.org",
            "numpy.org",
            "fastapi.tiangolo.com",
        ]

        system = (
            "You are finding coding information for DerekMCPServer. "
            "Return working code examples. Explain what the code does and why, not just what. "
            "Cite the official documentation when possible. "
            "If the code has any known pitfalls, flag them."
        )

        return self.generate_content(
            prompt=focused_query,
            system_prompt=system,
            max_tokens=1500,
            domain_filter=code_domains,
            recency_filter="year",
        )

    def search_current_events(self, query: str) -> str:
        """
        Search for current events and recent news.
        
        Args:
            query: News or current events query
        """
        return self.generate_content(
            prompt=query,
            max_tokens=800,
            recency_filter="week",
        )

    def search_academic(self, query: str) -> str:
        """
        Search academic and research sources.
        Useful for clinical literature, medical questions, AI papers.
        """
        return self.generate_content(
            prompt=query,
            max_tokens=1200,
            search_mode="academic",
        )


# =============================================================================
# SINGLETON — one search engine instance shared across all of DerekMCPServer
# =============================================================================

_perplexity_instance: Optional[PerplexityService] = None


def get_perplexity_service(model: str = DEFAULT_MODEL) -> PerplexityService:
    """
    Get or create the shared Perplexity service instance.
    DerekMCPServer gets one search engine.
    """
    global _perplexity_instance
    if _perplexity_instance is None:
        _perplexity_instance = PerplexityService(model=model)
    return _perplexity_instance


# =============================================================================
# © 2026 Everett Nathaniel Christman & The Christman AI Project
# Luma Cognify AI — "How can we help you love yourself more?"
#
# Perplexity is DerekMCPServer's eyes on the world.
# When he doesn't know — he looks. When he looks — he cites.
# Cardinal Rule 13: No hallucinations. No invented sources. Truth only.
# =============================================================================