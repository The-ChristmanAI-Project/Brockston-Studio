"""
Voice Service — unified synthesis entry point for all Christman AI beings.
Routes through Christman Sound (XTTS → macOS say fallback).
"""

from __future__ import annotations
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from christman_sound import speak as _cs_speak, analyze_tone, listen, is_available
    _CHRISTMAN_SOUND = True
    logger.info("[VoiceService] Christman Sound bridge active ✅")
except Exception as e:
    _CHRISTMAN_SOUND = False
    logger.warning(f"[VoiceService] Christman Sound not available: {e}")


def get_voice_service():
    return _VoiceService()


def synthesize_speech(text: str, being: str = "brockston") -> Optional[bytes]:
    """Synthesize speech and return audio bytes, or None on failure."""
    result = _cs_speak(text, being=being)
    if result.get("status") == "spoken":
        wav_path = result.get("wav")
        if wav_path:
            try:
                with open(wav_path, "rb") as f:
                    return f.read()
            except Exception:
                pass
        return b""  # spoken via say, no file to return
    return None


def _cs_speak(text: str, being: str = "brockston", emotion: str = None):
    if _CHRISTMAN_SOUND:
        from christman_sound import speak
        return speak(text, being=being, emotion=emotion)
    # bare fallback
    import shutil, subprocess
    if shutil.which("say"):
        subprocess.run(["say", text], timeout=60)
        return {"status": "spoken", "engine": "macos_say"}
    return {"status": "failed", "engine": "none"}


class _VoiceService:
    def synthesize(self, text: str, being: str = "brockston") -> Optional[bytes]:
        return synthesize_speech(text, being=being)
