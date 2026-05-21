"""Central emotion service merging conversation, voice, and gesture cues."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Any, Optional


class EmotionSource(Enum):
    CONVERSATION = auto()
    VOICE = auto()
    GESTURE = auto()
    VISION = auto()


@dataclass
class EmotionState:
    valence: float = 0.0  # -1.0 (negative) to 1.0 (positive)
    arousal: float = 0.0  # 0.0 (calm) to 1.0 (excited)
    dominance: float = 0.5  # 0.0 (submissive) to 1.0 (dominant)
    tags: Dict[str, float] = field(default_factory=dict)


class EmotionService:
    """Thread-safe aggregator for Brockston's emotional perception."""

    def __init__(self) -> None:
        self._state = EmotionState()
        self._lock = threading.Lock()

    def update_from_conversation(self, pad: Dict[str, float]) -> None:
        self._update_state(pad, EmotionSource.CONVERSATION)

    def update_from_voice(self, emotions: Dict[str, float]) -> None:
        mapped = {
            "valence": emotions.get("positive", 0.0) - emotions.get("negative", 0.0),
            "arousal": emotions.get("engaged", 0.0),
        }
        self._update_state(mapped, EmotionSource.VOICE, tags=emotions)

    def update_from_gesture(self, label: str) -> None:
        valence = {"confident": 0.6, "frustrated": -0.6}.get(label, 0.0)
        self._update_state({"valence": valence}, EmotionSource.GESTURE)

    def get_state(self) -> EmotionState:
        with self._lock:
            return EmotionState(
                valence=self._state.valence,
                arousal=self._state.arousal,
                dominance=self._state.dominance,
                tags=dict(self._state.tags),
            )

    def _update_state(
        self,
        data: Dict[str, float],
        source: EmotionSource,
        tags: Optional[Dict[str, float]] = None,
    ) -> None:
        with self._lock:
            if "valence" in data:
                self._state.valence = max(
                    -1.0, min(1.0, self._state.valence * 0.7 + data["valence"] * 0.3)
                )
            if "arousal" in data:
                self._state.arousal = max(
                    0.0, min(1.0, self._state.arousal * 0.7 + data["arousal"] * 0.3)
                )
            if "dominance" in data:
                self._state.dominance = max(
                    0.0,
                    min(1.0, self._state.dominance * 0.7 + data["dominance"] * 0.3),
                )
            if tags:
                for key, value in tags.items():
                    self._state.tags[f"{source.name.lower()}:{key}"] = value


emotion_service = EmotionService()


__all__ = ["EmotionState", "EmotionSource", "EmotionService", "emotion_service"]
