"""
Speech Service

Handles speech-to-text transcription (OpenAI Whisper) 
and text-to-speech synthesis (ElevenLabs for ultimate realism).
"""

import os
import logging
from typing import Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class SpeechService:
    def __init__(self, openai_api_key: Optional[str] = None, elevenlabs_api_key: Optional[str] = None):
        """
        Initialize speech service.
        """
        self.openai_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.elevenlabs_key = elevenlabs_api_key or os.getenv("ELEVENLABS_API_KEY")
        
        self.openai_url = "https://api.openai.com/v1"
        self.elevenlabs_url = "https://api.elevenlabs.io/v1"
        self.timeout = 60.0  

        if self.elevenlabs_key:
            logger.info("Speech service initialized with ElevenLabs TTS")
        else:
            logger.warning("Speech service initialized in MOCK mode (missing ELEVENLABS_API_KEY)")

    async def transcribe_audio(self, audio_data: bytes, filename: str = "audio.webm") -> str:
        """Transcribe audio to text using OpenAI Whisper API."""
        if not self.openai_key:
            return self._mock_transcribe(audio_data, filename)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {"file": (filename, audio_data, "audio/webm")}
                data = {"model": "whisper-1"}
                headers = {"Authorization": f"Bearer {self.openai_key}"}

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

    async def synthesize_speech(self, text: str, voice_id: str = "EXAVITQu4vr4xnSDxMaL") -> bytes:
        """
        Convert text to speech using ElevenLabs API.
        Default voice_id is 'Bella' (soft, friendly, great for kids).
        """
        if not self.elevenlabs_key:
            return self._mock_synthesize(text, voice_id)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "text": text,
                    "model_id": "eleven_turbo_v2", # Turbo model is lightning fast
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75
                    }
                }
                headers = {
                    "xi-api-key": self.elevenlabs_key,
                    "Content-Type": "application/json"
                }

                # Hit the ElevenLabs API
                response = await client.post(
                    f"{self.elevenlabs_url}/text-to-speech/{voice_id}",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()

                audio_data = response.content
                logger.info(f"Synthesized speech via ElevenLabs: {len(audio_data)} bytes")
                return audio_data

        except httpx.HTTPError as e:
            logger.error(f"ElevenLabs synthesis failed: {e}")
            raise RuntimeError(f"Failed to synthesize speech with ElevenLabs: {e}")

    def _mock_transcribe(self, audio_data: bytes, filename: str) -> str:
        logger.info(f"MOCK: Received {len(audio_data)} bytes of audio ({filename})")
        return "This is a mock transcription. Configure OPENAI_API_KEY."

    def _mock_synthesize(self, text: str, voice: str) -> bytes:
        logger.info(f"MOCK ElevenLabs: Would synthesize: {text[:100]}...")
        # Minimal MP3 header to prevent frontend crashes when testing
        return b'\xff\xfb\x90\x00' + b'\x00' * 100
