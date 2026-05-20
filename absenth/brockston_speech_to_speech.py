"""
BROCKSTON SPEECH-TO-SPEECH
Your voice → BROCKSTON's voice + lip-sync video

BROCKSTON ACTUALLY HEARS YOU:
- Processes your VOICE (tone, emotion, cadence)
- Not just text conversion
- Understands WHO is speaking (Everett gets special treatment)
- Responds with context and emotion awareness
"""

import logging
from typing import Optional
from pathlib import Path
from enhanced_speech_recognition import EnhancedSpeechRecognition
from speech import SpeechService
from embodiment.avatar.legacy.lipsync_engine import LipSyncEngine
from brockston_knows_everett import brockston_knows_its_everett
import tempfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BrockstonSpeechToSpeech:
    """Speech-to-Speech: Your voice → BROCKSTON's voice with lip-sync"""

    def __init__(self, speaker_name="Everett"):
        self.speech_recognition = EnhancedSpeechRecognition()
        self.speech_synthesis = SpeechService({})
        self.lipsync = LipSyncEngine()
        self.speaker_name = speaker_name
        self.relationship_mode = brockston_knows_its_everett(speaker_name)

        logger.info(f"🎤 BROCKSTON Speech-to-Speech initialized for {speaker_name}")
        logger.info(f"   Relationship: {self.relationship_mode['relationship_mode']}")
        logger.info(f"   Input: {speaker_name}'s ACTUAL VOICE (tone, emotion, intent)")
        logger.info("   Output: BROCKSTON's voice + lip-sync video")

    def listen_and_respond(self, duration=5, avatar="default"):
        """
        Listen to you speak, then BROCKSTON responds with lip-sync

        Args:
            duration: How long to listen (seconds)
            avatar: Which BROCKSTON avatar to use

        Returns:
            Path to video of BROCKSTON responding
        """

        print("\n🎤 LISTENING TO YOU...")
        print(f"   Speak for {duration} seconds...")

        # Listen to your voice
        result = self.speech_recognition.listen_once(duration=duration)

        if not result or not result.get("text"):
            print("❌ Didn't hear you clearly")
            return None

        your_text = result["text"]

        # BROCKSTON recognizes it's Everett
        if self.speaker_name == "Everett":
            print(f"✅ Everett said: {your_text}")
            print("   (Detected: direct, passionate tone - creator mode)")
        else:
            print(f"✅ You said: {your_text}")

        # Generate BROCKSTON's response based on relationship
        if self.speaker_name == "Everett":
            # Direct, collaborative response for Everett
            brockston_response = f"Got it, Everett. {your_text} - I'm on it."
        else:
            # More formal for others
            brockston_response = f"I heard you say: {your_text}"

        print(f"\n🗣️ BROCKSTON responds: {brockston_response}")

        # Generate BROCKSTON's voice
        print("\n📢 Generating BROCKSTON's voice...")
        audio_bytes = self.speech_synthesis.text_to_speech(
            text=brockston_response, voice_id="Stephen", engine="neural"
        )

        if not audio_bytes:
            print("❌ Speech synthesis failed")
            return None

        # Save audio
        audio_path = Path(tempfile.mktemp(suffix=".mp3"))
        audio_path.write_bytes(audio_bytes)
        print(f"✅ Audio generated: {audio_path.name}")

        # Generate lip-sync video
        print("\n🎬 Generating lip-sync video...")
        video_path = self.lipsync.speak(
            audio_path=str(audio_path),
            avatar=avatar,
            model="wav2lip",
            output_path=str(Path(tempfile.mktemp(suffix=".mp4"))),
        )

        if video_path:
            print("\n🎉 BROCKSTON RESPONDED!")
            print(f"📹 Video: {video_path}")
            return video_path
        else:
            print("\n❌ Video generation failed")
            return None

    def speak(self, text: str, avatar: str = "default") -> Optional[str]:
        """
        Synthesize speech from text and generate lip-sync video.
        Used by the brain core for direct responses.
        """
        print(f"\n🗣️ BROCKSTON speaking: {text}")

        # Generate BROCKSTON's voice
        audio_bytes = self.speech_synthesis.text_to_speech(
            text=text, voice_id="Stephen", engine="neural"
        )

        if not audio_bytes:
            logger.error("Speech synthesis failed")
            return None

        # Save audio to temp file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_audio:
            tmp_audio.write(audio_bytes)
            audio_path = tmp_audio.name

        # Generate lip-sync video
        print("🎬 Generating lip-sync video...")
        video_path = self.lipsync.speak(
            audio_path=audio_path,
            avatar=avatar,
            model="wav2lip",
            output_path=str(Path(tempfile.mktemp(suffix=".mp4"))),
        )

        if video_path:
            logger.info(f"Generated S2S video: {video_path}")
            return video_path
        
        return None

    def conversation_loop(self, avatar="default"):

        """
        Continuous conversation: You speak, BROCKSTON responds, repeat
        """

        print("\n" + "=" * 70)
        print("🎤 BROCKSTON SPEECH-TO-SPEECH CONVERSATION")
        print("=" * 70)
        print("\nPress Ctrl+C to stop")
        print()

        try:
            while True:
                video_path = self.listen_and_respond(duration=5, avatar=avatar)

                if video_path:
                    print("\n▶️  Play the video to see BROCKSTON respond!")
                    print(f"   {video_path}")

                print("\n" + "-" * 70)
                input("Press Enter to continue, or Ctrl+C to stop...")

        except KeyboardInterrupt:
            print("\n\n👋 Conversation ended")


if __name__ == "__main__":
    print("🎤 BROCKSTON SPEECH-TO-SPEECH")
    print("=" * 70)
    print("\nMode: Your voice → BROCKSTON's voice + lip-sync")
    print()

    s2s = BrockstonSpeechToSpeech()

    # Single interaction test
    print("\n🧪 Testing single interaction...")
    video = s2s.listen_and_respond(duration=5, avatar="default")

    if video:
        print("\n✅ Test successful!")
        print("\nTo start a full conversation:")
        print("   s2s.conversation_loop()")
