"""
Kimi K2.6 — NVIDIA learning tutor for Brockston Studio IDE.

Proxies to BROCKSTON :9001/kimi/interact when available, else calls NVIDIA NIM directly.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

BROCKSTON_KIMI_URL = os.getenv("BROCKSTON_KIMI_URL", "http://localhost:9001/kimi/interact")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "").strip()
NVIDIA_CHAT_URL = os.getenv(
    "NVIDIA_CHAT_URL",
    "https://integrate.api.nvidia.com/v1/chat/completions",
)
NVIDIA_KIMI_MODEL = os.getenv("NVIDIA_KIMI_MODEL", "moonshotai/kimi-k2.6")

_SYSTEM = {
    "tutor": (
        "You are Kimi — live learning tutor in Brockston Studio IDE.\n"
        "You teach Everett and neurodivergent / nonverbal children directly.\n"
        "Short sentences. Concrete examples. Dignity-first. Build retention."
    ),
    "codelab": (
        "You are Kimi in Brockston Studio Code Lab — senior engineer mentor.\n"
        "Help fix and explain code in the open editor. Direct. No filler."
    ),
}


class KimiService:
    @property
    def is_available(self) -> bool:
        return bool(NVIDIA_API_KEY) or self._brockston_reachable()

    def _brockston_reachable(self) -> bool:
        try:
            base = BROCKSTON_KIMI_URL.rsplit("/kimi/", 1)[0]
            r = httpx.get(f"{base}/api/health", timeout=2.0)
            return r.status_code == 200 and r.json().get("nvidia_kimi")
        except Exception:
            return False

    def interact(
        self,
        *,
        message: str,
        mode: str = "tutor",
        context: Optional[str] = None,
        domain: Optional[str] = None,
        thinking: bool = True,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        payload = {
            "mode": mode,
            "message": message,
            "context": context,
            "domain": domain,
            "thinking": thinking,
            "max_tokens": max_tokens,
        }

        try:
            r = httpx.post(BROCKSTON_KIMI_URL, json=payload, timeout=180.0)
            if r.status_code == 200:
                data = r.json()
                if data.get("ok") and data.get("text"):
                    logger.info("[Kimi] Brockston proxy ok mode=%s", mode)
                    return data
        except httpx.ConnectError:
            logger.debug("[Kimi] Brockston proxy offline — trying NVIDIA direct")
        except Exception as exc:
            logger.warning("[Kimi] Brockston proxy failed: %s", exc)

        if not NVIDIA_API_KEY:
            raise RuntimeError(
                "Kimi unavailable — set NVIDIA_API_KEY or start BROCKSTON backend on :9001"
            )

        system = _SYSTEM.get(mode, _SYSTEM["tutor"])
        parts = [system]
        if domain:
            parts.append(f"Domain: {domain}")
        if context:
            parts.append(f"Context:\n{context}")
        parts.append(f"User:\n{message}")
        prompt = "\n\n".join(parts)

        r = httpx.post(
            NVIDIA_CHAT_URL,
            headers={
                "Authorization": f"Bearer {NVIDIA_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={
                "model": NVIDIA_KIMI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "chat_template_kwargs": {"thinking": thinking},
                "max_tokens": max_tokens,
                "temperature": 0.6,
                "top_p": 1,
                "stream": False,
            },
            timeout=180.0,
        )
        r.raise_for_status()
        data = r.json()
        text = ""
        choices = data.get("choices") or []
        if choices:
            text = (choices[0].get("message") or {}).get("content") or ""
        return {"ok": True, "text": text, "model": NVIDIA_KIMI_MODEL, "mode": mode}


_kimi: Optional[KimiService] = None


def get_kimi_service() -> KimiService:
    global _kimi
    if _kimi is None:
        _kimi = KimiService()
    return _kimi