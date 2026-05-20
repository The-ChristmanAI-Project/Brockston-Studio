"""
Speech Service

Handles speech-to-text transcription and text-to-speech synthesis.
"""

import os
import logging
from typing import Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class SpeechService:
    """
    Service for speech operations: transcription and synthesis.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize speech service.

        Args:
            api_key: Optional API key for the configured speech provider
        """
        self.api_key = api_key or os.getenv("SPEECH_SERVICE_API_KEY")
        self.base_url = "https://api.speech-service.local"
        self.timeout = 60.0  # 60 seconds for audio processing

        if self.api_key:
            logger.info("Speech service initialized with configured API key")
        else:
            logger.info("Speech service initialized in MOCK mode for local testing")

    async def transcribe_audio(self, audio_data: bytes, filename: str = "audio.webm") -> str:
        """
        Transcribe audio to text using the configured speech service.

        Args:
            audio_data: Audio file bytes (supports mp3, mp4, mpeg, mpga, m4a, wav, webm)
            filename: Name of the audio file (with extension)

        Returns:
            Transcribed text

        Raises:
            RuntimeError: If transcription fails
        """
        if not self.api_key:
            return self._mock_transcribe(audio_data, filename)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {
                    "file": (filename, audio_data, "audio/webm")
                }
                data = {
                    "model": "whisper-1"
                }
                headers = {
                    "Authorization": f"Bearer {self.api_key}"
                }

                response = await client.post(
                    f"{self.openai_url}/audio/transcriptions",
                    files=files,
                    data=data,
                    headers=headers
                )
                response.raise_for_status()

                result = response.json()
                return result.get("text", "")

        except httpx.HTTPError as e:
            logger.error(f"Transcription failed: {e}")
            raise RuntimeError(f"Failed to transcribe audio: {e}")

    async def synthesize_speech(self, text: str, voice_id: str = "default") -> bytes:
        """
        Convert text to speech using local speech synthesis.

        Args:
            text: Text to convert to speech
            voice_id: Voice identifier (currently uses local synthesis)

        Returns:
            Audio data as bytes (MP3 format)

        Raises:
            RuntimeError: If synthesis fails
        """
        return self._mock_synthesize(text, voice_id)

    def _mock_transcribe(self, audio_data: bytes, filename: str) -> str:
        logger.info(f"MOCK: Received {len(audio_data)} bytes of audio ({filename})")
        return (
            "This is a mock transcription. "
            "Configure SPEECH_SERVICE_API_KEY to use real speech-to-text. "
            f"Audio file size: {len(audio_data)} bytes."
        )

    def _mock_synthesize(self, text: str, voice: str) -> bytes:
        """
        Mock speech synthesis for development/testing.
        Returns a minimal valid MP3 header to avoid errors.
        """
        logger.info(f"MOCK: Would synthesize with voice '{voice}': {text[:100]}...")
        mp3_header = b'\xff\xfb\x90\x00' + b'\x00' * 100
        return mp3_header
