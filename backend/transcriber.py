"""
Brockston Studio - Speech Recognition Bridge (Simplified)

Mock speech processing for student development.
No external audio dependencies needed.
"""

import json
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "static/audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

logger.info("✅ Speech recognition bridge initialized (mock mode)")


def transcribe_audio(audio_bytes: bytes, language: str = "en") -> dict:
    """Mock transcription - simulates speech-to-text"""
    logger.info(f"Transcribing {len(audio_bytes)} bytes of audio")
    return {
        "text": "[Speech input placeholder - configure real STT]",
        "confidence": 0.75,
        "language": language,
        "duration": len(audio_bytes) / SAMPLE_RATE if audio_bytes else 0
    }


def synthesize_speech(text: str, voice: str = "default") -> bytes:
    """Mock synthesis - returns minimal MP3 bytes for client playback"""
    logger.info(f"Synthesizing: {text[:50]}...")
    # Return minimal MP3 header so clients don't crash
    mp3_header = b'\xff\xfb\x90\x00' + b'\x00' * 100
    return mp3_header


class PassiveListener:
    """Mock listener - for wake word detection"""
    def __init__(self):
        self.is_listening = False
        logger.info("Passive listener initialized")
    
    def start(self):
        self.is_listening = True
        logger.info("Passive listening started")
    
    def stop(self):
        self.is_listening = False
        logger.info("Passive listening stopped")


class ActiveListener:
    """Mock listener - for active speech capture"""
    def __init__(self):
        self.is_listening = False
        logger.info("Active listener initialized")
    
    def start(self):
        self.is_listening = True
        logger.info("Active listening started")
    
    def stop(self):
        self.is_listening = False
        logger.info("Active listening stopped")
    
    def get_audio(self) -> bytes:
        """Mock - returns empty audio"""
        return b''


# Module-level instances
passive_listener = PassiveListener()
active_listener = ActiveListener()

# ==============================================================================
# © 2025 Everett Nathaniel Christman
# The Christman AI Project — Luma Cognify AI
# All rights reserved.
# Core Directive: "How can I help you love yourself more?"
# ==============================================================================
