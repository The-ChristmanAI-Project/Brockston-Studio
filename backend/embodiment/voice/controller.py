"""Speech tier controlling expressive output."""

from __future__ import annotations

from random import choice
from typing import Dict, Any, Optional
import os
import platform
import subprocess

from events import EventBus
from .profiles import resolve_profile


class SystemVoice:
    """Lightweight voice synthesiser using OS facilities."""

    def __init__(self, voice_id: str = "matthew", **_: Any) -> None:
        self.voice_id = voice_id

    def speak(self, text: str) -> None:
        system = platform.system()
        try:
            if system == "Darwin":
                subprocess.run(["say", text], check=True)
            elif system == "Linux":
                subprocess.run(["espeak", text], check=True)
            else:
                print(f"🗣️ {text}")
        except Exception:
            print(f"🗣️ {text}")


def _load_voice_class() -> Optional[type]:
    use_ultimate = os.getenv("BROCKSTON_USE_ULTIMATE_VOICE", "0").lower() in {
        "1",
        "true",
        "yes",
    }
    if not use_ultimate:
        return SystemVoice
    # Ultimate voice module does not exist - using SystemVoice
    return SystemVoice


class SpeechController:
    """Handles expressive speech with empathy-aware fallbacks."""

    def __init__(self, bus: EventBus, enable_voice: bool = True) -> None:
        self.bus = bus
        self.voice = None
        self._voice_cls = _load_voice_class() if enable_voice else None

    def speak(self, text: str, affect: str = "neutral") -> Dict[str, Any]:
        profile = resolve_profile(affect)
        enriched_text = f"{profile.prefix}{text}" if text else choice(profile.fallback)

        delivered = False
        self._ensure_voice()
        if self.voice:
            try:
                if hasattr(self.voice, "voice_id"):
                    setattr(self.voice, "voice_id", profile.voice_id)
                self.voice.speak(enriched_text)  # type: ignore[attr-defined]
                delivered = True
            except Exception:
                delivered = False

        if not delivered:
            print(f"[SPEECH:{affect}] {enriched_text}")

        payload = {"text": enriched_text, "affect": affect, "delivered": delivered}
        self.bus.publish("speech.delivered", payload)
        return payload

    def _ensure_voice(self) -> None:
        if self.voice or not self._voice_cls:
            return
        try:
            self.voice = self._voice_cls(enable_speech=False, use_web_search=False)
        except Exception:
            self.voice = None
