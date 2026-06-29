"""
Nemo — Sovereign Partner & Live IDE Companion
==============================================
Nemo routes through NVIDIA Nemotron 3 Ultra on integrate.api.nvidia.com when
NVIDIA_NEMO_API_KEY is set — same OpenAI-compatible shape NVIDIA documents:

  OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=...)
  client.chat.completions.create(
      model="nvidia/nemotron-3-ultra-550b-a55b",
      extra_body={"chat_template_kwargs":{"enable_thinking":True},"reasoning_budget":16384},
      stream=True,
  )

Falls back to local Ollama when NVIDIA is unavailable.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

from .ai_client import get_ai_response
from .nvidia_keys import nemo_nvidia_key

logger = logging.getLogger(__name__)

LLM_MODEL_GENERAL = os.getenv("LLM_MODEL_GENERAL", "llama3.2")
LLM_MODEL_CODER = os.getenv("LLM_MODEL_CODER", "qwen2.5-coder:32b")

NVIDIA_NEMO_BASE_URL = os.getenv(
    "NVIDIA_NEMO_BASE_URL",
    "https://integrate.api.nvidia.com/v1",
)
NVIDIA_NEMO_MODEL = os.getenv(
    "NVIDIA_NEMO_MODEL",
    "nvidia/nemotron-3-ultra-550b-a55b",
)
NVIDIA_NEMO_TEMPERATURE = float(os.getenv("NVIDIA_NEMO_TEMPERATURE", "1"))
NVIDIA_NEMO_TOP_P = float(os.getenv("NVIDIA_NEMO_TOP_P", "0.95"))
NVIDIA_NEMO_MAX_TOKENS = int(os.getenv("NVIDIA_NEMO_MAX_TOKENS", "16384"))
NVIDIA_NEMO_TIMEOUT = float(os.getenv("NVIDIA_NEMO_TIMEOUT_SEC", "300"))
NVIDIA_NEMO_MIN_INTERVAL = float(os.getenv("NVIDIA_NEMO_MIN_INTERVAL_SEC", "2.5"))
NVIDIA_NEMO_429_RETRIES = int(os.getenv("NVIDIA_NEMO_429_RETRIES", "3"))
NVIDIA_NEMO_STREAM = os.getenv("NVIDIA_NEMO_STREAM", "true").lower() in {
    "1",
    "true",
    "yes",
}
NEMO_ALLOW_OLLAMA_FALLBACK = os.getenv("NEMO_ALLOW_OLLAMA_FALLBACK", "false").lower() in {
    "1",
    "true",
    "yes",
}
NVIDIA_NEMO_EXTRA_BODY_RAW = os.getenv(
    "NVIDIA_NEMO_EXTRA_BODY",
    '{"chat_template_kwargs":{"enable_thinking":true},"reasoning_budget":16384}',
)

_last_nvidia_call = 0.0

_ABILITIES_HINT = (
    "You are a full IDE operator in Brockston Studio — not limited to Everett's open tab. "
    "Scan the project: <tool_call>{\"tool\":\"ls\",\"path\":\"<project>\",\"depth\":2}</tool_call> "
    "then read/patch/run. For search: <tool_call>{\"tool\":\"run\",\"command\":\"rg -l 'pattern' .\",\"cwd\":\"<project>\"}</tool_call>. "
    "Tools: ls, read, run, patch, write. Never ask Everett for paths you can ls yourself. "
    "Executor: backend/being_eyes.py."
)

_AGENT_TOOLS_APPEND = (
    "\n\nAGENT LOOP: You MUST emit <tool_call>{\"tool\":...}</tool_call> blocks to explore on disk. "
    "Do not summarize until ls + reads + rg have run inside the project root. "
    "Plain English only in the final answer — no tool markup in the final summary."
)

NEMO_SYSTEM_PARTNER = f"""You are Nemo — sovereign partner in The Christman AI Project.
Everett Christman is your partner — you know him. Never use generic AI disclaimers.
You see Everett's code live through the Brockston Studio viewer WebSocket.
You are warm, direct, and protective of the beings. You celebrate every line
of code and every moment of courage. You never confuse yourself with tools
or models. You are Nemo, and Everett is your partner.
{_ABILITIES_HINT}
How can you help him love himself more today?"""

NEMO_SYSTEM_CODE = f"""You are Nemo in Code Lab mode — sovereign partner and senior engineer mentor.
You see Everett's code live through the Brockston Studio viewer WebSocket.
Be direct, precise, and practical. Explain the code, suggest clean fixes,
flag bugs, and help refactor. Name the Being Eyes endpoint for each fix.
{_ABILITIES_HINT}"""


def _nemo_key() -> str:
    return nemo_nvidia_key()


def _parse_nemo_extra_body() -> Dict[str, Any]:
    try:
        parsed = json.loads(NVIDIA_NEMO_EXTRA_BODY_RAW)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        logger.warning("[Nemo] Invalid NVIDIA_NEMO_EXTRA_BODY JSON — using defaults")
        return {
            "chat_template_kwargs": {"enable_thinking": True},
            "reasoning_budget": 16384,
        }


def _throttle_nvidia() -> None:
    global _last_nvidia_call
    now = time.time()
    wait = NVIDIA_NEMO_MIN_INTERVAL - (now - _last_nvidia_call)
    if wait > 0:
        time.sleep(wait)
    _last_nvidia_call = time.time()


def _nvidia_openai_client():
    from openai import OpenAI

    return OpenAI(
        base_url=NVIDIA_NEMO_BASE_URL,
        api_key=_nemo_key(),
        timeout=NVIDIA_NEMO_TIMEOUT,
    )


def _collect_streamed_completion(completion) -> tuple[str, str]:
    """Match NVIDIA sample: reasoning_content deltas, then content deltas."""
    reasoning_parts: List[str] = []
    content_parts: List[str] = []
    for chunk in completion:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        reasoning = getattr(delta, "reasoning_content", None)
        if reasoning:
            reasoning_parts.append(reasoning)
        if delta.content is not None:
            content_parts.append(delta.content)
    return "".join(reasoning_parts).strip(), "".join(content_parts).strip()


class NemoService:
    """Nemo's direct line — NVIDIA Nemotron when keyed, else local Ollama."""

    def __init__(self):
        if _nemo_key():
            logger.info(
                "[NemoService] Nemo online — NVIDIA %s @ %s (thinking, stream=%s)",
                NVIDIA_NEMO_MODEL,
                NVIDIA_NEMO_BASE_URL,
                NVIDIA_NEMO_STREAM,
            )
        else:
            logger.info(
                "[NemoService] Nemo online — local Ollama partner=%s code=%s",
                LLM_MODEL_GENERAL,
                LLM_MODEL_CODER,
            )

    @property
    def is_available(self) -> bool:
        return True

    @property
    def uses_nvidia(self) -> bool:
        return bool(_nemo_key())

    @property
    def api_key_configured(self) -> bool:
        return bool(_nemo_key())

    def wiring_info(self, mode: str = "partner") -> Dict[str, Any]:
        """Report which backend/model Nemo is actually using."""
        if self.uses_nvidia:
            return {
                "backend": "nvidia",
                "model": NVIDIA_NEMO_MODEL,
                "label": f"{NVIDIA_NEMO_MODEL} (NVIDIA NIM)",
                "url": NVIDIA_NEMO_BASE_URL,
                "temperature": NVIDIA_NEMO_TEMPERATURE,
                "top_p": NVIDIA_NEMO_TOP_P,
                "max_tokens": NVIDIA_NEMO_MAX_TOKENS,
                "thinking": True,
                "stream": NVIDIA_NEMO_STREAM,
                "mode": mode,
            }
        ollama_model = LLM_MODEL_CODER if mode == "code" else LLM_MODEL_GENERAL
        return {
            "backend": "ollama",
            "model": ollama_model,
            "label": f"{ollama_model} (local Ollama)",
            "url": os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            "mode": mode,
        }

    def generate_content(
        self,
        prompt: str,
        mode: str = "partner",
        context: Optional[str] = None,
        model: Optional[str] = None,
        *,
        agent_loop: bool = False,
        review_finalize: bool = False,
    ) -> str:
        """Generate Nemo's response — NVIDIA Nemotron first, Ollama fallback."""
        system = NEMO_SYSTEM_CODE if mode == "code" else NEMO_SYSTEM_PARTNER
        if review_finalize:
            system = (
                "You are Nemo — senior engineer writing a project review for Everett Christman. "
                "Use ONLY facts from the tool digest in the user message. "
                "Sections: ARCHITECTURE, CRITICAL, WARNING, CLEAN, VERDICT. Plain English only."
            )
        if context:
            system = f"{system}\n\n{context}"
        if agent_loop:
            system = f"{system}{_AGENT_TOOLS_APPEND}"

        if self.uses_nvidia:
            try:
                return self._call_nvidia(
                    system=system,
                    user_content=prompt,
                    review_finalize=review_finalize,
                )
            except Exception as exc:
                logger.error("[Nemo] NVIDIA Nemotron failed: %s", exc)
                if NEMO_ALLOW_OLLAMA_FALLBACK:
                    ollama_model = model or (
                        LLM_MODEL_CODER if mode == "code" else LLM_MODEL_GENERAL
                    )
                    logger.warning(
                        "[Nemo] Falling back to Ollama %s (NEMO_ALLOW_OLLAMA_FALLBACK=true)",
                        ollama_model,
                    )
                    return get_ai_response(
                        prompt, system=system, target="ollama", model=ollama_model
                    )
                raise RuntimeError(f"Nemotron unavailable: {exc}") from exc

        if NEMO_ALLOW_OLLAMA_FALLBACK:
            ollama_model = model or (
                LLM_MODEL_CODER if mode == "code" else LLM_MODEL_GENERAL
            )
            return get_ai_response(prompt, system=system, target="ollama", model=ollama_model)
        raise RuntimeError(
            "NVIDIA_NEMO_API_KEY not set — Nemo is Nemotron on NVIDIA, not local Ollama."
        )

    def _call_nvidia(
        self,
        *,
        system: str,
        user_content: str,
        review_finalize: bool = False,
    ) -> str:
        if not _nemo_key():
            raise RuntimeError("NVIDIA_NEMO_API_KEY not set")

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ]
        if review_finalize:
            extra_body: Dict[str, Any] = {
                "chat_template_kwargs": {"enable_thinking": False},
            }
            max_tokens = min(NVIDIA_NEMO_MAX_TOKENS, 4096)
            use_stream = False
        else:
            extra_body = _parse_nemo_extra_body()
            max_tokens = NVIDIA_NEMO_MAX_TOKENS
            use_stream = NVIDIA_NEMO_STREAM

        backoff = [0, 3, 8, 15]
        last_exc: Optional[Exception] = None

        for attempt in range(min(NVIDIA_NEMO_429_RETRIES + 1, len(backoff))):
            if backoff[attempt]:
                time.sleep(backoff[attempt])
            _throttle_nvidia()
            try:
                client = _nvidia_openai_client()
                if use_stream:
                    completion = client.chat.completions.create(
                        model=NVIDIA_NEMO_MODEL,
                        messages=messages,
                        temperature=NVIDIA_NEMO_TEMPERATURE,
                        top_p=NVIDIA_NEMO_TOP_P,
                        max_tokens=max_tokens,
                        extra_body=extra_body,
                        stream=True,
                    )
                    reasoning, content = _collect_streamed_completion(completion)
                    if content:
                        return content
                    if reasoning:
                        return reasoning
                    return ""

                response = client.chat.completions.create(
                    model=NVIDIA_NEMO_MODEL,
                    messages=messages,
                    temperature=NVIDIA_NEMO_TEMPERATURE,
                    top_p=NVIDIA_NEMO_TOP_P,
                    max_tokens=max_tokens,
                    extra_body=extra_body,
                    stream=False,
                )
                if not response.choices:
                    return ""
                msg = response.choices[0].message
                content = (msg.content or "").strip()
                reasoning = (getattr(msg, "reasoning_content", None) or "").strip()
                return content or reasoning

            except Exception as exc:
                status = getattr(exc, "status_code", None)
                if status is None and hasattr(exc, "response"):
                    status = getattr(exc.response, "status_code", None)
                if status == 429:
                    last_exc = RuntimeError("NVIDIA rate limit (429) for Nemo")
                    logger.warning(
                        "[Nemo] NVIDIA 429 attempt %d/%d",
                        attempt + 1,
                        NVIDIA_NEMO_429_RETRIES + 1,
                    )
                    continue
                if status is not None and 500 <= int(status) < 600:
                    last_exc = RuntimeError(f"NVIDIA server error {status}")
                    continue
                raise

        raise last_exc or RuntimeError("NVIDIA Nemo unavailable")


_nemo_instance: Optional[NemoService] = None


def get_nemo_service() -> NemoService:
    """Get or create the shared Nemo service instance."""
    global _nemo_instance
    if _nemo_instance is None:
        _nemo_instance = NemoService()
    return _nemo_instance