"""
Speech Recognition Engine
-------------------------
Core speech recognition processing for BROCKSTON's voice interface.
"""

import logging
import speech_recognition as sr
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("speech_recognition_engine")


class SpeechRecognitionEngine:
    """Advanced speech recognition with multiple backends"""

    def __init__(self, backend: str = "google"):
        """
        Initialize speech recognition engine

        Args:
            backend: Recognition backend ('google', 'sphinx', 'whisper')
        """
        self.backend = backend
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Optimal recognition settings
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5
        self.recognizer.pause_threshold = 1.2
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.5

        logger.info(f"SpeechRecognitionEngine initialized with {backend} backend")

    def calibrate(self, duration: float = 2.0):
        """Calibrate microphone for ambient noise"""
        logger.info(f"Calibrating microphone for {duration}s...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=duration)
        logger.info(
            f"Calibration complete. Energy threshold: {self.recognizer.energy_threshold}"
        )

    def listen(
        self, timeout: float = 10.0, phrase_time_limit: float = 30.0
    ) -> Optional[str]:
        """
        Listen for speech and return recognized text

        Args:
            timeout: Maximum time to wait for speech to start
            phrase_time_limit: Maximum length of a phrase

        Returns:
            Recognized text or None if recognition failed
        """
        try:
            with self.microphone as source:
                logger.debug("Listening for speech...")
                audio = self.recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_time_limit
                )

            logger.debug("Processing speech...")

            if self.backend == "google":
                text = self.recognizer.recognize_google(audio)
            elif self.backend == "sphinx":
                text = self.recognizer.recognize_sphinx(audio)
            else:
                text = self.recognizer.recognize_google(audio)  # fallback

            logger.info(f"Recognized: {text}")
            return text

        except sr.WaitTimeoutError:
            logger.warning("Listening timeout - no speech detected")
            return None
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return None
        except Exception as e:
            logger.error(f"Recognition error: {e}")
            return None

    def listen_continuous(self, callback, timeout: float = None):
        """
        Listen continuously and call callback with recognized text

        Args:
            callback: Function to call with recognized text
            timeout: Optional timeout in seconds
        """
        logger.info("Starting continuous listening...")

        def audio_callback(recognizer, audio):
            try:
                text = recognizer.recognize_google(audio)
                callback(text)
            except sr.UnknownValueError:
                pass
            except Exception as e:
                logger.error(f"Continuous recognition error: {e}")

        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)

        stop_listening = self.recognizer.listen_in_background(
            self.microphone, audio_callback
        )

        return stop_listening

    def set_energy_threshold(self, threshold: int):
        """Set custom energy threshold for recognition"""
        self.recognizer.energy_threshold = threshold
        logger.info(f"Energy threshold set to {threshold}")

    def get_audio_data(self, timeout: float = 10.0) -> Optional[sr.AudioData]:
        """Get raw audio data without recognition"""
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=timeout)
            return audio
        except Exception as e:
            logger.error(f"Failed to capture audio: {e}")
            return None


# Convenience function for simple recognition
def recognize_speech(timeout: float = 10.0) -> Optional[str]:
    """Simple speech recognition function"""
    engine = SpeechRecognitionEngine()
    engine.calibrate(duration=1.0)
    return engine.listen(timeout=timeout)


def get_speech_recognition_engine(**kwargs) -> SpeechRecognitionEngine:
    """Get a speech recognition engine instance"""
    return SpeechRecognitionEngine(**kwargs)


__all__ = [
    "SpeechRecognitionEngine",
    "recognize_speech",
    "get_speech_recognition_engine",
]

# ==============================================================================
# © 2025 Everett Nathaniel Christman
# The Christman AI Project — Luma Cognify AI
# All rights reserved. Unauthorized use, replication, or derivative training
# of this material is prohibited.
#
# Core Directive: "How can I help you love yourself more?"
# Autonomy & Alignment Protocol v3.0
# ==============================================================================
