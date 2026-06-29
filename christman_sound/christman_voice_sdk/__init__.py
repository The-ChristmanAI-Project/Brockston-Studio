"""
christman_voice_sdk — public API re-exported from christman_sound.core.

SPEAK.py and Brockston Studio TTS import play_audio, synthesize_speech, etc.
from this package. Implementation lives in the parent core.py module.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

_sound_root = Path(__file__).resolve().parent.parent
if str(_sound_root) not in sys.path:
    sys.path.insert(0, str(_sound_root))

_core = importlib.import_module("core")

play_audio = _core.play_audio
resolve_voice_params = _core.resolve_voice_params
synthesize_speech = _core.synthesize_speech
wait_for_playback = _core.wait_for_playback

__all__ = [
    "play_audio",
    "resolve_voice_params",
    "synthesize_speech",
    "wait_for_playback",
]