"""
BROCKSTON TTS Bridge — routes through unified VoiceService.

Previously: imported speech.py directly (unreliable path, wrong voice ID).
Now: routes through voice_service.py which handles ElevenLabs → Polly → gTTS
with the correct Matthew voice and proper fallback chain.

Cardinal Rule 1: It has to actually work.
Cardinal Rule 13: No more Rachel voice pretending to be Brockston.
"""

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Ensure python_core is in path so voice_service is importable
_here = Path(__file__).resolve().parent
_python_core = _here.parent if _here.name != "python_core" else _here
for _p in [str(_python_core), str(_python_core / "core")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from voice_service import synthesize_speech as _synth, get_voice_service
    _VOICE_SERVICE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"[TTSBridge] voice_service not available: {e}")
    _VOICE_SERVICE_AVAILABLE = False


def synthesize_speech(text: str, being: str = "brockston"):
    """
    Synthesize speech for a Christman AI family member.
    Routes to ElevenLabs → AWS Polly → gTTS in priority order.

    Args:
        text: Text to speak
        being: Family member (brockston, derek, alphavox, sierra, etc.)

    Returns:
        bytes: MP3 audio or None on failure
    """
    if not _VOICE_SERVICE_AVAILABLE:
        logger.error("[TTSBridge] VoiceService not available — cannot synthesize")
        return None

    try:
        audio = _synth(text, being=being)
        if audio:
            logger.info(f"[TTSBridge] Speech synthesized for {being}")
        return audio
    except Exception as e:
        logger.error(f"[TTSBridge] Speech synthesis failed: {e}", exc_info=True)
        return None


# ==============================================================================
# © 2025 Everett Nathaniel Christman & The Christman AI Project
# Luma Cognify AI — AWS Sponsored Startup
# ==============================================================================

