"""Avatar engine contracts so Brockston can run with or without visuals."""

from __future__ import annotations

from typing import Protocol, runtime_checkable, Optional, Any


@runtime_checkable
class AvatarEngine(Protocol):
    """Interface implemented by visual avatars and headless stand-ins."""

    def speak(self, text: str) -> None:
        ...

    def sync_with_speech(self, text: str, duration: Optional[float] = None) -> None:
        ...

    def set_emotion(self, emotion: Any) -> None:
        ...

    def get_current_frame(self):
        ...

    def stop(self) -> None:
        ...


class NullAvatarEngine:
    """No-op avatar that preserves interfaces when visuals are disabled."""

    def speak(self, text: str) -> None:  # pragma: no cover - trivial
        return None

    def sync_with_speech(self, text: str, duration: Optional[float] = None) -> None:
        return None

    def set_emotion(self, emotion: Any) -> None:
        return None

    def get_current_frame(self):  # pragma: no cover - trivial
        return None

    def stop(self) -> None:
        return None


__all__ = ["AvatarEngine", "NullAvatarEngine"]
