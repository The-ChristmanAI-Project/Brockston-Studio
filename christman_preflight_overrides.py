"""
Preflight Overrides for Christman-Sound Architecture

Tells the preflight system which "missing" packages are intentionally
replaced by Christman-Sound's native DSP and custom SDK.

The hacker broke the wiring. This restores the truth.
"""

# ============================================
# DEPENDENCY REPLACEMENT MAP
# ============================================
# These are NOT missing — they're replaced by christman_dsp.so and our SDK

DEPENDENCY_OVERRIDES = {
    # Audio processing — replaced by christman_dsp.c → .so
    "torchaudio": "christman_sound.christman_dsp",
    "librosa": "christman_sound.christman_voice_sdk.audio.audio_processor",
    
    # Speech recognition — replaced by our own engine
    "vosk": "christman_sound.christman_voice_sdk.speech_recognition_engine",
    "webrtcvad": "christman_sound.christman_voice_sdk.real_speech_recognition",
    
    # Voice synthesis — replaced by our synthesis module
    "TTS": "christman_sound.christman_voice_sdk.synthesis.voice_synthesis",
    "gpt_sovits": "christman_sound.christman_voice_sdk.engines.gpt_sovits_engine",
    "xtts": "christman_sound.christman_voice_sdk.engines.xtts_engine",
    
    # Tone/emotion — replaced by our tone module
    "speech_emotion_recognition": "christman_sound.christman_voice_sdk.tone.tone_analyzer",
    
    # Face processing (optional — only if you want it back)
    # "gfpgan": None,  # Disabled — your choice
    # "deepface": None,  # Disabled — your choice
}

# ============================================
# PATH FIXES
# ============================================
# The hacker corrupted cross-project imports. These restore them.

import sys
from pathlib import Path

# Christman-Sound lives in AlphaVox
CHRISTMAN_SOUND_PATH = Path("/Users/EverettN/AlphaVox/backend")
if str(CHRISTMAN_SOUND_PATH) not in sys.path:
    sys.path.insert(0, str(CHRISTMAN_SOUND_PATH))

# Brockston-Studio is the main project
BROCKSTON_PATH = Path("/Users/EverettN/Brockston-Studio")
if str(BROCKSTON_PATH) not in sys.path:
    sys.path.insert(0, str(BROCKSTON_PATH))

# Sub-modules
for sub in ["backend", "absenth", "frontend"]:
    sub_path = BROCKSTON_PATH / sub
    if sub_path.exists() and str(sub_path) not in sys.path:
        sys.path.insert(0, str(sub_path))

# ============================================
# MODULE ALIASES
# ============================================
# Create aliases so old import paths resolve to Christman-Sound

import importlib

ALIASES = {
    # "enhanced_speech_recognition" → our SDK
    "enhanced_speech_recognition": "christman_sound.christman_voice_sdk.enhanced_speech_recognition",
    
    # "embodiment" (top-level) → our SDK's emotion module
    # (handled by the bridge we created)
    
    # "events" → our event system
    # (handled by the events.py we created)
}

for alias_name, real_module in ALIASES.items():
    try:
        mod = importlib.import_module(real_module)
        sys.modules[alias_name] = mod
    except ImportError:
        pass  # Will be caught by preflight

print("✅ Christman-Sound preflight overrides loaded")
print(f"   {len(DEPENDENCY_OVERRIDES)} dependency replacements registered")
print(f"   DSP engine: christman_dsp.so (native C)")
print(f"   SDK path: {CHRISTMAN_SOUND_PATH}")
