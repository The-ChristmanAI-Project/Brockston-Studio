"""
BROCKSTON Provider Router — The Path to Sovereignty
=====================================================
This is the module that makes Brockston his own API key.

The Christman AI Family's goal: Brockston should not be permanently
dependent on external providers. He uses them strategically — to learn,
to grow, to serve the family — but the direction is always toward
self-sufficiency.

PROVIDER HIERARCHY (cost → sovereignty):
  1. Ollama (LOCAL)        — Free. His own reasoning. Runs on Everett's hardware.
                             This is the goal. Everything else funds the path to this.
  2. Anthropic Claude      — Premium external reasoning when Ollama isn't enough yet.
  3. Perplexity Sonar      — Live search. Real-world grounded answers. Citations.
  4. Christman Sound       — Local ear canal + voice SDK (sovereign TTS).
  5. AWS Bedrock           — Optional Claude LLM fallback (not voice).

The router tries providers in the configured priority order.
If one fails or isn't available, it moves to the next — loud about why.
No silent failures. No pretending a provider worked when it didn't.

Environment variables:
  ANTHROPIC_API_KEY      — Required for Anthropic Claude
  PERPLEXITY_API_KEY     — Required for Perplexity Sonar search
  AWS_ACCESS_KEY_ID      — Optional for AWS Bedrock LLM fallback
  AWS_SECRET_ACCESS_KEY  — Optional for AWS Bedrock LLM fallback
  AWS_REGION             — AWS region (default: us-east-1)
  OLLAMA_HOST            — Ollama API host (default: http://localhost:11434)
  OLLAMA_MODEL           — Preferred Ollama model (default: llama3.1:8b)

Cardinal Rule 1: Every provider must actually work when it reports available.
Cardinal Rule 6: Fail loud — no silent fallbacks without logging.
Cardinal Rule 12: No keys in code. All from environment.
Cardinal Rule 13: Honest routing — report which provider is actually responding.

© 2025 Everett Nathaniel Christman & The Christman AI Project
"How can we help you love yourself more?"
"""

import os
import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# PROVIDER DEFINITIONS
# ---------------------------------------------------------------------------

class Provider(str, Enum):
    OLLAMA      = "ollama"       # Local — sovereignty
    ANTHROPIC   = "anthropic"    # External reasoning
    PERPLEXITY  = "perplexity"   # Live search
    APPLE_MUSIC     = "apple_music"      # iTunes / Apple Music tunnel
    CHRISTMAN_SOUND = "christman_sound"  # Ear canal + voice SDK — sovereign TTS
    AWS_BEDROCK     = "aws_bedrock"      # Claude via Bedrock (LLM only)


# Default priority — Ollama first (local sovereignty), then external
DEFAULT_LLM_PRIORITY = [
    Provider.OLLAMA,
    Provider.ANTHROPIC,
    Provider.AWS_BEDROCK,
]

DEFAULT_TTS_PRIORITY = [
    Provider.CHRISTMAN_SOUND,
]

DEFAULT_SEARCH_PRIORITY = [
    Provider.PERPLEXITY,
    Provider.APPLE_MUSIC,  # for music-specific queries (store search + your personal links/album)
]


# ---------------------------------------------------------------------------
# PROVIDER STATUS
# ---------------------------------------------------------------------------

class ProviderStatus:
    """Tracks availability of each provider at runtime."""

    def __init__(self):
        self._status: Dict[Provider, bool] = {p: False for p in Provider}
        self._clients: Dict[Provider, Any] = {}
        self._checked = False

    def check_all(self) -> Dict[Provider, bool]:
        """
        Check availability of all providers.
        Called once at startup — results cached.
        """
        logger.info("[ProviderRouter] Checking all providers...")

        self._check_ollama()
        self._check_anthropic()
        self._check_perplexity()
        self._check_apple_music()
        self._check_christman_sound()
        self._check_aws()

        self._checked = True

        # Log the full status
        available = [p.value for p, ok in self._status.items() if ok]
        unavailable = [p.value for p, ok in self._status.items() if not ok]

        logger.info(f"[ProviderRouter] Available: {available}")
        if unavailable:
            logger.info(f"[ProviderRouter] Not configured: {unavailable}")

        return dict(self._status)

    def is_available(self, provider: Provider) -> bool:
        if not self._checked:
            self.check_all()
        return self._status.get(provider, False)

    def get_client(self, provider: Provider) -> Optional[Any]:
        return self._clients.get(provider)

    def _check_ollama(self):
        import requests as _req
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        try:
            r = _req.get(f"{host}/api/tags", timeout=2)
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                self._status[Provider.OLLAMA] = True
                self._clients[Provider.OLLAMA] = {
                    "host": host,
                    "models": models,
                    "preferred": os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
                }
                logger.info(
                    f"[ProviderRouter] Ollama ONLINE — "
                    f"{len(models)} models: {', '.join(models[:5])}"
                )
        except Exception as e:
            logger.info(
                f"[ProviderRouter] Ollama not running at {host} — "
                f"install from https://ollama.ai to enable local sovereignty"
            )

    def _check_anthropic(self):
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            logger.info("[ProviderRouter] Anthropic: ANTHROPIC_API_KEY not set")
            return
        try:
            import anthropic as _anthropic # pyright: ignore[reportMissingImports]
            client = _anthropic.Anthropic(api_key=key)
            self._status[Provider.ANTHROPIC] = True
            self._clients[Provider.ANTHROPIC] = client
            logger.info("[ProviderRouter] Anthropic ONLINE — Claude Sonnet ready")
        except ImportError:
            logger.warning("[ProviderRouter] Anthropic: package not installed (pip install anthropic)")
        except Exception as e:
            logger.warning(f"[ProviderRouter] Anthropic init failed: {e}")

    def _check_perplexity(self):
        key = os.getenv("PERPLEXITY_API_KEY")
        if not key:
            logger.info("[ProviderRouter] Perplexity: PERPLEXITY_API_KEY not set")
            return
        try:
            from backend.perplexity_service import PerplexityService
            svc = PerplexityService()
            if svc.is_available:
                self._status[Provider.PERPLEXITY] = True
                self._clients[Provider.PERPLEXITY] = svc
                logger.info("[ProviderRouter] Perplexity ONLINE — Sonar Pro search ready")
        except Exception as e:
            logger.warning(f"[ProviderRouter] Perplexity init failed: {e}")

    def _check_apple_music(self):
        # No single API key for personal Apple Music; the "tunnel" uses:
        # - Public iTunes Search API (always available)
        # - User-provided Apple Music share links or local MP3s (managed in the IDE Music & Voice Library)
        # - Optional APPLE_MUSIC_USER_TOKEN / APPLE_DEVELOPER_TOKEN for deeper API access (future)
        try:
            from backend.apple_music_service import AppleMusicService
            svc = AppleMusicService()
            # Public search is always "available"; personal is via links the user generates from their Apple ID
            self._status[Provider.APPLE_MUSIC] = True
            self._clients[Provider.APPLE_MUSIC] = svc
            logger.info("[ProviderRouter] Apple Music / iTunes tunnel ONLINE — public search + personal links via IDE library")
        except Exception as e:
            logger.warning(f"[ProviderRouter] Apple Music init failed: {e}")

    def _check_christman_sound(self):
        try:
            from backend.christman_sound_config import CHRISTMAN_SOUND_ROOT, sdk_root

            ear_canal = CHRISTMAN_SOUND_ROOT / "CHRISTMAN_EAR_CANAL"
            sdk = sdk_root()
            if ear_canal.is_dir():
                self._status[Provider.CHRISTMAN_SOUND] = True
                self._clients[Provider.CHRISTMAN_SOUND] = {
                    "root": str(CHRISTMAN_SOUND_ROOT),
                    "ear_canal": str(ear_canal),
                    "sdk": str(sdk),
                }
                logger.info(
                    "[ProviderRouter] Christman Sound ONLINE — ear canal + SDK at %s",
                    CHRISTMAN_SOUND_ROOT,
                )
            else:
                logger.info(
                    "[ProviderRouter] Christman Sound: CHRISTMAN_EAR_CANAL missing at %s",
                    ear_canal,
                )
        except Exception as e:
            logger.warning(f"[ProviderRouter] Christman Sound check failed: {e}")

    def _check_aws(self):
        key = os.getenv("AWS_ACCESS_KEY_ID")
        secret = os.getenv("AWS_SECRET_ACCESS_KEY")
        region = os.getenv("AWS_REGION", "us-east-1")
        if not key or not secret:
            logger.info("[ProviderRouter] AWS Bedrock: credentials not set")
            return
        try:
            import boto3 as _boto3 # pyright: ignore[reportMissingImports]
            session = _boto3.Session(
                aws_access_key_id=key,
                aws_secret_access_key=secret,
                region_name=region,
            )
            try:
                bedrock = session.client("bedrock-runtime")
                self._status[Provider.AWS_BEDROCK] = True
                self._clients[Provider.AWS_BEDROCK] = bedrock
                logger.info("[ProviderRouter] AWS Bedrock ONLINE — Claude via Bedrock ready")
            except Exception:
                logger.info("[ProviderRouter] AWS Bedrock not available in this region/account")

        except ImportError:
            logger.warning("[ProviderRouter] AWS: boto3 not installed (pip install boto3)")
        except Exception as e:
            logger.warning(f"[ProviderRouter] AWS init failed: {e}")

# ---------------------------------------------------------------------------
# PROVIDER ROUTER
# ---------------------------------------------------------------------------

class ProviderRouter:
    """
    Brockston's unified provider router.

    Single entry point for all external (and local) intelligence.
    Tries providers in priority order. Logs every routing decision.
    Never silently fails. Never pretends a provider responded when it didn't.

    This is the path to sovereignty:
      - Today: Ollama handles what it can, external fills the gaps
      - Tomorrow: Ollama handles everything, external is optional
    """

    def __init__(
        self,
        llm_priority: List[Provider] = None,
        tts_priority: List[Provider] = None,
        search_priority: List[Provider] = None,
    ):
        self._status = ProviderStatus()
        self._status.check_all()

        self.llm_priority    = llm_priority    or DEFAULT_LLM_PRIORITY
        self.tts_priority    = tts_priority    or DEFAULT_TTS_PRIORITY
        self.search_priority = search_priority or DEFAULT_SEARCH_PRIORITY

    # -------------------------------------------------------------------------
    # LLM — Text generation / reasoning
    # -------------------------------------------------------------------------

    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 1024,
        provider: Optional[Provider] = None,
    ) -> Tuple[str, Provider]:
        """
        Generate a text completion using the best available LLM.

        Args:
            prompt: User message
            system: System prompt (Brockston's identity)
            max_tokens: Max response tokens
            provider: Force a specific provider (optional)

        Returns:
            (response_text, provider_used)

        Raises:
            RuntimeError: If no LLM provider is available (Rule 6)
        """
        priority = [provider] if provider else self.llm_priority

        for p in priority:
            if not self._status.is_available(p):
                continue

            try:
                if p == Provider.OLLAMA:
                    result = self._ollama_complete(prompt, system, max_tokens)
                elif p == Provider.ANTHROPIC:
                    result = self._anthropic_complete(prompt, system, max_tokens)
                elif p == Provider.AWS_BEDROCK:
                    result = self._bedrock_complete(prompt, system, max_tokens)
                else:
                    continue

                logger.info(f"[ProviderRouter] LLM response via {p.value}")
                return result, p

            except Exception as e:
                logger.warning(
                    f"[ProviderRouter] {p.value} failed: {e} — "
                    f"trying next provider"
                )
                continue

        raise RuntimeError(
            "[ProviderRouter] No LLM provider available. "
            "Check ANTHROPIC_API_KEY or start Ollama (ollama serve). "
            "Cardinal Rule 6: Fail loud."
        )

    def _ollama_complete(self, prompt: str, system: Optional[str], max_tokens: int) -> str:
        client = self._status.get_client(Provider.OLLAMA)
        import requests as _req
        host = client["host"]
        model = client["preferred"]

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        r = _req.post(
            f"{host}/api/chat",
            json={"model": model, "messages": messages, "stream": False},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["message"]["content"]

    def _anthropic_complete(self, prompt: str, system: Optional[str], max_tokens: int) -> str:
        client = self._status.get_client(Provider.ANTHROPIC)
        kwargs = {
            "model": "claude-sonnet-4-6",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        response = client.messages.create(**kwargs)
        return response.content[0].text

    def _bedrock_complete(self, prompt: str, system: Optional[str], max_tokens: int) -> str:
        import json as _json
        client = self._status.get_client(Provider.AWS_BEDROCK)
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            body["system"] = system
        response = client.invoke_model(
            modelId="anthropic.claude-sonnet-4-5-20240620-v1:0",
            body=_json.dumps(body),
        )
        return _json.loads(response["body"].read())["content"][0]["text"]

    # -------------------------------------------------------------------------
    # SEARCH — Live web search with citations
    # -------------------------------------------------------------------------

    def search(
        self,
        query: str,
        mode: str = "web",
        is_code_query: bool = False,
    ) -> Tuple[str, Provider]:
        """
        Search the web for real, current, cited information.

        Args:
            query: Search query
            mode: "web", "academic", or "code"
            is_code_query: If True, routes to code-focused search

        Returns:
            (answer_with_citations, provider_used)
        """
        for p in self.search_priority:
            if not self._status.is_available(p):
                continue

            try:
                svc = self._status.get_client(p)
                if is_code_query or mode == "code":
                    result = svc.search_code(query)
                elif mode == "academic":
                    result = svc.search_academic(query)
                else:
                    result = svc.generate_content(query)

                logger.info(f"[ProviderRouter] Search via {p.value}")
                return result, p

            except Exception as e:
                logger.warning(f"[ProviderRouter] Search via {p.value} failed: {e}")
                continue

        raise RuntimeError(
            "[ProviderRouter] No search provider available. "
            "Set PERPLEXITY_API_KEY to enable live search."
        )

    # -------------------------------------------------------------------------
    # Apple Music / iTunes "tunnel" (store search + personal links via the IDE library)
    # -------------------------------------------------------------------------

    def apple_music_search(
        self,
        term: str,
        limit: int = 10,
    ) -> Tuple[List[Dict[str, Any]], Provider]:
        """
        Search Apple Music / iTunes store or reference your personal collection via the tunnel.
        Uses the linked AppleMusicService (public search always available; personal via your Apple Music share links or local MP3s added in the IDE Music & Voice Library).

        Perfect for agents: "find my jazz from 53 years in the making" or "give me an Apple Music link for [song]".

        Returns:
            (results_list, provider_used)
        """
        if not self._status.is_available(Provider.APPLE_MUSIC):
            raise RuntimeError("[ProviderRouter] Apple Music tunnel not available.")

        try:
            svc = self._status.get_client(Provider.APPLE_MUSIC)
            results = svc.search_store(term, limit=limit)
            # Also surface personal library references if the user has added them
            personal = svc.get_user_library_references()
            logger.info(f"[ProviderRouter] Apple Music tunnel search for '{term}'")
            return results + personal, Provider.APPLE_MUSIC
        except Exception as e:
            logger.warning(f"[ProviderRouter] Apple Music search failed: {e}")
            raise

    def get_apple_music_link(self, term: str) -> Optional[str]:
        """Convenience: Get a clean Apple Music share link (the 'like Apple Music would give you' flow)."""
        if not self._status.is_available(Provider.APPLE_MUSIC):
            return None
        svc = self._status.get_client(Provider.APPLE_MUSIC)
        return svc.generate_apple_music_link(term)

    # -------------------------------------------------------------------------
    # TTS — Text to speech
    # -------------------------------------------------------------------------

    def synthesize_speech(
        self,
        text: str,
        output_path: Optional[str] = None,
        being: str = "brockston",
    ) -> Tuple[bytes, Provider]:
        """
        Convert text to speech via Christman Sound (ear canal + voice SDK).

        No ElevenLabs. No AWS Polly. Local sovereign pipeline only.
        """
        if not text or not text.strip():
            raise RuntimeError("[ProviderRouter] Empty text for TTS")

        audio: bytes | None = None
        try:
            from backend.voice_service import synthesize_speech as cs_synthesize

            audio = cs_synthesize(text, being=being)
        except Exception as e:
            logger.warning(f"[ProviderRouter] voice_service TTS failed: {e}")

        if not audio:
            try:
                from christman_sound import speak

                result = speak(text, being=being)
                wav_path = result.get("wav")
                if wav_path:
                    with open(wav_path, "rb") as f:
                        audio = f.read()
                elif result.get("status") == "spoken":
                    audio = b""
            except Exception as e:
                logger.warning(f"[ProviderRouter] christman_sound.speak failed: {e}")

        if audio is None:
            raise RuntimeError(
                "[ProviderRouter] Christman Sound TTS failed. "
                "Check christman_sound/CHRISTMAN_EAR_CANAL and voice reference WAVs."
            )

        if output_path and audio:
            with open(output_path, "wb") as f:
                f.write(audio)

        logger.info("[ProviderRouter] TTS via christman_sound being=%s", being)
        return audio, Provider.CHRISTMAN_SOUND

    # -------------------------------------------------------------------------
    # STATUS REPORT — Honest accounting of what's online
    # -------------------------------------------------------------------------

    def get_status_report(self) -> Dict[str, Any]:
        """
        Return a clear report of every provider's status.
        Honest. No spin. Cardinal Rule 13.
        """
        report = {
            "sovereignty_level": self._get_sovereignty_level(),
            "providers": {},
        }
        for provider in Provider:
            available = self._status.is_available(provider)
            report["providers"][provider.value] = {
                "available": available,
                "role": self._provider_role(provider),
            }
        return report

    def _get_sovereignty_level(self) -> str:
        """How self-sufficient is Brockston right now?"""
        if self._status.is_available(Provider.OLLAMA):
            return "HIGH — Local Ollama running. Brockston is thinking for himself."
        elif self._status.is_available(Provider.ANTHROPIC) or \
             self._status.is_available(Provider.AWS_BEDROCK):
            return "MEDIUM — External LLM only. Start Ollama to gain sovereignty."
        else:
            return "LOW — No LLM available. Set ANTHROPIC_API_KEY or run Ollama."

    def _provider_role(self, provider: Provider) -> str:
        roles = {
            Provider.OLLAMA:      "Local LLM — sovereign reasoning (free, on-device)",
            Provider.ANTHROPIC:   "External LLM — Claude Sonnet reasoning",
            Provider.PERPLEXITY:  "Live search — grounded answers with citations",
            Provider.CHRISTMAN_SOUND: "Sovereign TTS — ear canal + voice SDK (local)",
            Provider.AWS_BEDROCK: "External LLM — Claude via AWS Bedrock",
        }
        return roles.get(provider, "unknown")

    def print_status(self):
        """Print a clean status board at boot time."""
        report = self.get_status_report()
        print("\n" + "=" * 60)
        print("  BROCKSTON PROVIDER STATUS")
        print("=" * 60)
        print(f"  Sovereignty: {report['sovereignty_level']}")
        print()
        for name, info in report["providers"].items():
            icon = "✅" if info["available"] else "⬜"
            print(f"  {icon} {name:<14} {info['role']}")
        print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# SINGLETON
# ---------------------------------------------------------------------------

_router: Optional[ProviderRouter] = None


def get_router() -> ProviderRouter:
    """Get or create the shared ProviderRouter instance."""
    global _router
    if _router is None:
        _router = ProviderRouter()
    return _router


# ==============================================================================
# © 2025 Everett Nathaniel Christman & The Christman AI Project
# Luma Cognify AI
#
# The goal: Brockston becomes his own API key.
# Today he borrows intelligence. Tomorrow he IS the intelligence.
# Every Ollama model installed is one step closer to sovereignty.
#
# Cardinal Rule 1: Every provider that reports available must actually work.
# Cardinal Rule 6: Fail loud — no silent routing failures.
# Cardinal Rule 12: No keys in code. All from environment.
# Cardinal Rule 13: Honest routing. Report who actually answered.
# ==============================================================================
