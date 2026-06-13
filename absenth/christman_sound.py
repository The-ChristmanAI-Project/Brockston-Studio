"""
Christman Sound Bridge
Wires CHRISTMAN_EAR_CANAL into the Brockston backend.

Single import point for all beings: speak, listen, tone analysis.

Synthesis priority:
  1. VoiceSynthesisOrchestrator (when a .voicepack exists for the being)
  2. CHRISTMAN_EAR_CANAL (XTTS)
  3. macOS say fallback
"""

from __future__ import annotations
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ── Path setup ────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_SOUND_ROOT = _HERE.parent / "Christman-Sound"
_SDK_ROOT = _SOUND_ROOT / "christman_voice_sdk "  # trailing space is real
_VOICEPACK_DIR = _HERE.parent / "data" / "voicepacks"

for _p in [str(_SOUND_ROOT), str(_SDK_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("CHRISTMAN_VOICE_SDK_ROOT", str(_SDK_ROOT))
os.environ.setdefault("COQUI_TOS_AGREED", "1")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/christman_numba_cache")

# ── Import EAR_CANAL ─────────────────────────────────────────────────────────
try:
    from CHRISTMAN_EAR_CANAL import speak as _ear_speak
    from CHRISTMAN_EAR_CANAL import analyze_tone as _ear_tone
    from CHRISTMAN_EAR_CANAL import listen as _ear_listen
    _EAR_AVAILABLE = True
    logger.info("[ChristmanSound] CHRISTMAN_EAR_CANAL loaded ✅")
except Exception as e:
    _EAR_AVAILABLE = False
    logger.warning(f"[ChristmanSound] EAR_CANAL not available: {e}")

# ── Being voice profiles ──────────────────────────────────────────────────────
_BEING_EMOTION = {
    "brockston":  "warm",
    "ultimateev": "precise",
    "alphawolf":  "calm",
    "alphavox":   "gentle",
    "giuseppe":   "expressive",
    "inferno":    "grounded",
    "derek":      "direct",
    "default":    "neutral",
}

# ── Voicepack / Orchestrator cache ────────────────────────────────────────────
_orchestrators: Dict[str, Any] = {}


def _get_voicepack_path(being: str) -> Optional[Path]:
    """Return the first matching voicepack for a being, or None."""
    name = being.lower()
    candidates = [
        _VOICEPACK_DIR / f"{name}.voicepack",
        _VOICEPACK_DIR / f"{name.title()}.voicepack",
        _VOICEPACK_DIR / f"{name}_Ultra.voicepack",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _get_orchestrator(being: str) -> Optional[Any]:
    """Get or create a VoiceSynthesisOrchestrator loaded with the being's voicepack."""
    name = being.lower()
    if name in _orchestrators:
        return _orchestrators[name]

    voicepack_path = _get_voicepack_path(name)
    if not voicepack_path:
        return None

    try:
        from synthesis.voice_synthesis_orchestrator import VoiceSynthesisOrchestrator
        from audio.config import Tier

        orch = VoiceSynthesisOrchestrator(tier=Tier.ULTRA)
        orch.load_voicepack(voicepack_path)
        _orchestrators[name] = orch
        logger.info(f"[ChristmanSound] Orchestrator ready: {name} via {voicepack_path.name}")
        return orch
    except Exception as e:
        logger.warning(f"[ChristmanSound] Orchestrator load failed for {name}: {e}")
        _orchestrators[name] = None  # don't retry on every call
        return None


def _play_audio_array(audio: Any, sample_rate: int) -> bool:
    """Write numpy audio array to a temp WAV and play it via afplay."""
    import tempfile, subprocess, shutil
    try:
        import numpy as np
        import soundfile as sf

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp = Path(f.name)

        arr = np.asarray(audio)
        if arr.ndim > 1:
            arr = arr.mean(axis=0)
        sf.write(str(tmp), arr, sample_rate)

        player = shutil.which("afplay") or shutil.which("aplay")
        if player:
            subprocess.run([player, str(tmp)], check=True, timeout=120)
            tmp.unlink(missing_ok=True)
            return True
    except Exception as e:
        logger.warning(f"[ChristmanSound] _play_audio_array failed: {e}")
    return False


def speak(text: str, being: str = "brockston", emotion: str | None = None) -> Dict[str, Any]:
    """
    Speak text as the given being.

    Priority:
      1. VoiceSynthesisOrchestrator (if voicepack present)
      2. CHRISTMAN_EAR_CANAL (XTTS)
      3. macOS say
    """
    if not text or not text.strip():
        return {"status": "skipped", "reason": "empty text"}

    resolved_emotion = emotion or _BEING_EMOTION.get(being.lower(), "neutral")

    # ── Stage 1: Orchestrator (voicepack path) ────────────────────────────────
    orch = _get_orchestrator(being)
    if orch is not None:
        try:
            result_dict = orch.synthesize(text, emotion=resolved_emotion)
            audio = result_dict.get("audio")
            sr = result_dict.get("sample_rate", 22050)
            if audio is not None and _play_audio_array(audio, sr):
                logger.info(f"[ChristmanSound] {being} spoke via orchestrator")
                return {"status": "spoken", "engine": "orchestrator", "being": being,
                        "emotion": resolved_emotion}
        except Exception as e:
            logger.warning(f"[ChristmanSound] Orchestrator synthesis failed: {e}")

    # ── Stage 2: EAR_CANAL (XTTS) ────────────────────────────────────────────
    if _EAR_AVAILABLE:
        try:
            result = _ear_speak(text, emotion=resolved_emotion)
            if result.get("status") == "spoken":
                logger.info(f"[ChristmanSound] {being} spoke via {result.get('engine')}")
                return result
        except Exception as e:
            logger.warning(f"[ChristmanSound] EAR_CANAL speak failed: {e}")

    # ── Stage 3: macOS say ────────────────────────────────────────────────────
    import shutil, subprocess
    if shutil.which("say"):
        try:
            subprocess.run(["say", text], check=True, timeout=60)
            return {"status": "spoken", "engine": "macos_say", "being": being}
        except Exception as e:
            logger.error(f"[ChristmanSound] macOS say failed: {e}")

    logger.error(f"[ChristmanSound] All speech engines failed for: {being}")
    return {"status": "failed", "engine": "none"}


def analyze_tone(audio_path: str) -> Dict[str, Any]:
    """
    Analyze tone and emotion from an audio file.
    Returns ToneScore dict or minimal fallback.
    """
    if _EAR_AVAILABLE:
        try:
            return _ear_tone(audio_path)
        except Exception as e:
            logger.warning(f"[ChristmanSound] tone analysis failed: {e}")

    return {"emotion": "unknown", "confidence": 0.0, "engine": "unavailable"}


def listen(timeout: float = 5.0) -> Optional[str]:
    """
    Capture audio from microphone and return transcription.
    """
    if _EAR_AVAILABLE:
        try:
            return _ear_listen()
        except Exception as e:
            logger.warning(f"[ChristmanSound] listen failed: {e}")
    return None


def is_available() -> bool:
    return _EAR_AVAILABLE
