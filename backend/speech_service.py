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
        # Wire to mcp-media-ingestor live ear bridge first (real-time improved ear with energy/tone).
        # This is the high-quality student "hear" path for the beings when the sensory bus is running.
        try:
            import httpx
            r = await httpx.AsyncClient(timeout=1.5).get("http://localhost:8765/latest")
            data = r.json()
            if data.get("text"):
                # Rich output from our processor: includes energy + tone now
                tone_info = f" [e:{data.get('energy')} t:{data.get('tone')}]" if data.get('energy') else ""
                return f"{data.get('text')}{tone_info}"
        except Exception:
            pass

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
        Convert text to speech using macOS say + ffmpeg.
        Zero cost. No API key. Works offline. (Rule 15)
        """
        import subprocess
        import tempfile
        import os
        from pathlib import Path

        voice = "Daniel"
        if voice_id and voice_id not in ("default", ""):
            voice = voice_id

        aiff_path = tempfile.mktemp(suffix=".aiff")
        mp3_path  = tempfile.mktemp(suffix=".mp3")

        try:
            # Step 1 — macOS say → AIFF
            r = subprocess.run(
                ["say", "-v", voice, "-o", aiff_path, text[:600]],
                capture_output=True, timeout=30,
            )
            if r.returncode != 0 or not Path(aiff_path).exists():
                raise RuntimeError(f"say failed: {r.stderr.decode()[:200]}")

            # Step 2 — AIFF → MP3 via ffmpeg
            r = subprocess.run(
                ["ffmpeg", "-y", "-i", aiff_path,
                 "-codec:a", "libmp3lame", "-qscale:a", "2", mp3_path],
                capture_output=True, timeout=30,
            )
            if r.returncode != 0 or not Path(mp3_path).exists():
                raise RuntimeError(f"ffmpeg failed: {r.stderr.decode()[:200]}")

            audio = Path(mp3_path).read_bytes()
            logger.info(f"[TTS] Synthesized {len(audio)//1024}KB for '{text[:40]}...'")
            return audio

        finally:
            for p in (aiff_path, mp3_path):
                try:
                    os.unlink(p)
                except Exception:
                    pass

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
