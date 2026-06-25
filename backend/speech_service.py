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
        Christman-Sound XTTS when a being reference WAV exists, else macOS say.
        Zero paid APIs. (Rule 15)
        """
        import asyncio
        import subprocess
        import tempfile
        import os
        from pathlib import Path

        being = (voice_id or "default").lower().strip()
        loop = asyncio.get_event_loop()

        express_audio = await loop.run_in_executor(
            None, lambda: self._audio_from_voice_center_express(text, being)
        )
        if express_audio:
            return express_audio

        christman_audio = await loop.run_in_executor(
            None, lambda: self._synthesize_christman_sound(text, being)
        )
        if christman_audio:
            return christman_audio

        voice = "Daniel"
        if voice_id and voice_id not in ("default", ""):
            voice = voice_id

        aiff_path = tempfile.mktemp(suffix=".aiff")
        mp3_path = tempfile.mktemp(suffix=".mp3")

        try:
            r = subprocess.run(
                ["say", "-v", voice, "-o", aiff_path, text[:600]],
                capture_output=True,
                timeout=30,
            )
            if r.returncode != 0 or not Path(aiff_path).exists():
                raise RuntimeError(f"say failed: {r.stderr.decode()[:200]}")

            r = subprocess.run(
                ["ffmpeg", "-y", "-i", aiff_path,
                 "-codec:a", "libmp3lame", "-qscale:a", "2", mp3_path],
                capture_output=True,
                timeout=30,
            )
            if r.returncode != 0 or not Path(mp3_path).exists():
                raise RuntimeError(f"ffmpeg failed: {r.stderr.decode()[:200]}")

            audio = Path(mp3_path).read_bytes()
            logger.warning("[TTS] Falling back to macOS 'say' for being=%s (no good Christman ref) — %dKB", being, len(audio) // 1024)
            return audio

        finally:
            for p in (aiff_path, mp3_path):
                try:
                    os.unlink(p)
                except Exception:
                    pass

    def _audio_from_voice_center_express(self, text: str, being: str) -> bytes | None:
        """Voice_Creation_Center express cache — pre-rendered phrases."""
        import subprocess
        import tempfile
        from pathlib import Path

        try:
            from backend.christman_sound_config import try_express_audio

            raw = try_express_audio(text, being)
            if not raw:
                return None
            return self._to_mp3_bytes(raw)
        except Exception as exc:
            logger.debug("[TTS] Voice_Creation_Center express miss: %s", exc)
            return None

    @staticmethod
    def _to_mp3_bytes(audio: bytes) -> bytes | None:
        """Convert WAV/raw bytes to MP3 for the IDE player."""
        import subprocess
        import tempfile
        from pathlib import Path

        if audio[:4] == b"\xff\xfb" or audio[:3] == b"ID3":
            return audio
        wav_path = tempfile.mktemp(suffix=".wav")
        mp3_path = tempfile.mktemp(suffix=".mp3")
        try:
            Path(wav_path).write_bytes(audio)
            r = subprocess.run(
                ["ffmpeg", "-y", "-i", wav_path, "-codec:a", "libmp3lame", "-qscale:a", "2", mp3_path],
                capture_output=True,
                timeout=45,
            )
            if r.returncode != 0 or not Path(mp3_path).exists():
                return None
            return Path(mp3_path).read_bytes()
        finally:
            for p in (wav_path, mp3_path):
                try:
                    import os
                    os.unlink(p)
                except Exception:
                    pass

    def _synthesize_christman_sound(self, text: str, being: str) -> bytes | None:
        """Try Christman Voice SDK; return MP3 bytes or None to fall back."""
        import subprocess
        import tempfile
        from pathlib import Path

        try:
            from backend.christman_sound_config import (
                ensure_sound_paths,
                find_reference_wav,
                load_being_manifest,
            )

            ensure_sound_paths()
            manifest = load_being_manifest(being)
            ref = find_reference_wav(being)
            if not ref:
                logger.info("[TTS] No specific reference for being=%s — using fallback ref (or will hit macOS say)", being)
                return None

            # Prefer direct local christman_voice_sdk XTTSEngine (now wired since user confirmed local christman_sound present)
            # This uses the exact reference WAV you provided for the being (e.g. Kimi) for real voice cloning.
            try:
                from christman_voice_sdk.engines.xtts_engine import XTTSEngine
                engine = XTTSEngine()
                engine.load_voice(ref)
                synth_result = engine.synthesize(text[:600], language="en")
                if synth_result and getattr(synth_result, "audio", None) is not None:
                    import numpy as np
                    from scipy.io.wavfile import write as write_wav
                    import tempfile
                    from pathlib import Path as PPath
                    tmp = PPath(tempfile.mktemp(suffix=".wav"))
                    sr = getattr(synth_result, "sample_rate", 22050)
                    audio_arr = np.asarray(synth_result.audio)
                    if audio_arr.dtype != np.int16:
                        audio_arr = (audio_arr * 32767).astype(np.int16)
                    write_wav(str(tmp), sr, audio_arr)
                    audio = self._to_mp3_bytes(tmp.read_bytes())
                    tmp.unlink(missing_ok=True)
                    if audio:
                        logger.info(
                            "[TTS] Direct local XTTSEngine %dKB being=%s ref=%s",
                            len(audio) // 1024, being, ref.name
                        )
                        return audio
            except Exception as exc:
                logger.debug("[TTS] Direct XTTSEngine failed for %s: %s", being, exc)

            # Fallback to the EAR_CANAL SPEAK wrapper (may still hit import issues)
            try:
                from CHRISTMAN_EAR_CANAL.SPEAK import speak
                result = speak(text[:600], reference_audio=ref, allow_fallback=False)
                wav_path = result.get("wav")
                if wav_path and Path(wav_path).exists():
                    audio = self._to_mp3_bytes(Path(wav_path).read_bytes())
                    if audio:
                        logger.info(
                            "[TTS] Voice_Creation_Center→Christman-Sound %dKB being=%s pack=%s ref=%s",
                            len(audio) // 1024,
                            being,
                            (manifest or {}).get("pack_id"),
                            ref.name,
                        )
                        return audio
            except Exception as exc:
                logger.debug("[TTS] EAR_CANAL SPEAK failed: %s", exc)

            logger.info("[TTS] No usable Christman audio for being=%s despite ref; will use macOS say", being)
            return None
        except Exception as exc:
            logger.debug("[TTS] Christman-Sound unavailable: %s", exc)
            return None

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
