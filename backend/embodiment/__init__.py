"""Brockston embodiment package (avatar/voice/gesture)."""

from .avatar.interface import AvatarEngine, NullAvatarEngine
from .voice.controller import SpeechController
from .emotion import emotion_service

__all__ = ["AvatarEngine", "NullAvatarEngine", "SpeechController", "emotion_service"]
