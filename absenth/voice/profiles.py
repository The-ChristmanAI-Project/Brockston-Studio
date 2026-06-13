"""Empathy and tone profiles for BROCKSTON's speech tier."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class VoiceProfile:
    affect: str
    prefix: str
    fallback: tuple[str, ...]
    voice_id: str
    speed: float


PROFILES: Dict[str, VoiceProfile] = {
    "neutral": VoiceProfile(
        affect="neutral",
        prefix="",
        fallback=("I'm here with you.", "Take your time, I'm listening."),
        voice_id="matthew",
        speed=1.0,
    ),
    "encouraging": VoiceProfile(
        affect="encouraging",
        prefix="You're doing great — ",
        fallback=("I believe in you.", "We're moving forward together."),
        voice_id="matthew",
        speed=1.05,
    ),
    "soothing": VoiceProfile(
        affect="soothing",
        prefix="Let's pause and breathe. ",
        fallback=("You're safe with me.", "We can take this gently."),
        voice_id="matthew",
        speed=0.95,
    ),
    "celebratory": VoiceProfile(
        affect="celebratory",
        prefix="Yes! Let's celebrate. ",
        fallback=("Amazing work!", "You nailed it!"),
        voice_id="matthew",
        speed=1.1,
    ),
}


def resolve_profile(affect: str) -> VoiceProfile:
    return PROFILES.get(affect, PROFILES["neutral"])
