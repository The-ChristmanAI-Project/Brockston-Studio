"""
CHRISTMAN_EAR_CANAL
===================

Shared hearing, speech, tone, phoneme, voice-profile, and OCR adapters for
the Christman Family of Autonomous Beings.

This package does not replace the original modules. It gives Derek, AlphaVox,
AlphaWolf, Brockston, Geo, Seraphinia, and future beings one clean import path.
"""

# The actual modules live inside the CHRISTMAN_EAR_CANAL sub-package, not at
# this package's top level. Re-export from there so callers can keep importing
# `from christman_sound import speak, capture, listen, ...` like the docstring
# above promises.
from .CHRISTMAN_EAR_CANAL.EAR import capture, listen
from .CHRISTMAN_EAR_CANAL.OCR import scan_document, scan_screen
from .CHRISTMAN_EAR_CANAL.PHONEMES import label_phonemes, phonemes_to_visemes
from .CHRISTMAN_EAR_CANAL.SPEAK import speak
from .CHRISTMAN_EAR_CANAL.TONE import analyze_tone
from .CHRISTMAN_EAR_CANAL.VOICE_PROFILE import (
    capture_voice_profile,
    list_voice_profiles,
    load_voice_profile,
)

__all__ = [
    "analyze_tone",
    "capture",
    "capture_voice_profile",
    "label_phonemes",
    "list_voice_profiles",
    "listen",
    "load_voice_profile",
    "phonemes_to_visemes",
    "scan_document",
    "scan_screen",
    "speak",
]
