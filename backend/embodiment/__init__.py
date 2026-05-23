"""Brockston embodiment package (voice)."""

from .voice.controller import SpeechController
from .emotion import emotion_service

__all__ = ["SpeechController", "emotion_service"]
