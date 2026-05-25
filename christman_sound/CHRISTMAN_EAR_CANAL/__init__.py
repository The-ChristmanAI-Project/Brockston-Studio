"""CHRISTMAN_EAR_CANAL — hearing, speech, tone, phoneme, and voice-profile adapters."""

from .SPEAK import speak
from .TONE import analyze_tone
from .EAR import capture, listen
from .PHONEMES import label_phonemes, phonemes_to_visemes
from .VOICE_PROFILE import capture_voice_profile, list_voice_profiles, load_voice_profile

__all__ = [
    "speak",
    "analyze_tone",
    "capture",
    "listen",
    "label_phonemes",
    "phonemes_to_visemes",
    "capture_voice_profile",
    "list_voice_profiles",
    "load_voice_profile",
]
