"""
BROCKSTON Lip-Sync Engine
Makes BROCKSTON's avatar TALK with synchronized lips

Uses the research from:
- brockston_research/Wav2Lip (lightweight, fast)
- brockston_research/MuseTalk (real-time)
- brockston_research/SadTalker (expressions)
"""

from pathlib import Path
import subprocess
import tempfile
import logging

logger = logging.getLogger(__name__)

# Add research repos to path
PROJECT_ROOT = Path(__file__).parent
RESEARCH_DIR = PROJECT_ROOT / "brockston_research"


class LipSyncEngine:
    """Makes BROCKSTON's avatar talk with lip-sync"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.research_dir = RESEARCH_DIR
        self.avatar_dir = PROJECT_ROOT / "static" / "avatar_assets"

        # Available models
        self.models = {
            "wav2lip": self.research_dir / "Wav2Lip",
            "musetalk": self.research_dir / "MuseTalk",
            "sadtalker": self.research_dir / "SadTalker",
        }

        # Check which models are available
        self.available_models = {}
        for name, path in self.models.items():
            if path.exists():
                self.available_models[name] = path
                logger.info(f"✅ {name} available at {path}")
            else:
                logger.warning(f"⚠️  {name} not found at {path}")

        # Default avatar images - BROCKSTON is GORGEOUS!
        self.avatars = {
            "default": self.avatar_dir / "BROCKSTONGRIN.JPG",
            "professional": self.avatar_dir / "BROKSTON.jpeg",
            "brockston": self.avatar_dir / "BROCKSTON.jpeg",
            "idle_happy": self.avatar_dir / "brokston_idle_happy.png",
            "idle_neutral": self.avatar_dir / "brokston_idle_neutral.png",
            "idle_thinking": self.avatar_dir / "brokston_idle_thinking.png",
            "talking_happy": self.avatar_dir / "brokston_talking_happy.png",
            "talking_neutral": self.avatar_dir / "brokston_talking_neutral.png",
            "talking_thinking": self.avatar_dir / "brokston_talking_thinking.png",
        }

        # Check avatars
        for name, path in self.avatars.items():
            if path.exists():
                logger.info(f"🎭 Avatar '{name}' found: {path.name}")
            else:
                logger.warning(f"⚠️  Avatar '{name}' missing: {path}")

    def sync_wav2lip(self, audio_path, avatar_image=None, output_path=None):
        """
        Generate lip-sync video using Wav2Lip

        Args:
            audio_path: Path to audio file (WAV/MP3)
            avatar_image: Path to BROCKSTON's image (default: BROCKSTONGRIN.JPG)
            output_path: Where to save video (default: temp file)

        Returns:
            Path to generated video
        """
        if "wav2lip" not in self.available_models:
            logger.error("❌ Wav2Lip not available")
            return None

        # Use default avatar if not specified
        if avatar_image is None:
            avatar_image = self.avatars["default"]

        # Ensure avatar_image is a Path object
        avatar_image = Path(avatar_image)

        # Generate output path if not specified
        if output_path is None:
            output_path = Path(tempfile.mktemp(suffix=".mp4"))
        else:
            output_path = Path(output_path)

        wav2lip_dir = self.available_models["wav2lip"]
        inference_script = wav2lip_dir / "inference.py"

        if not inference_script.exists():
            logger.error(f"❌ Wav2Lip inference.py not found at {inference_script}")
            return None

        # Create temp directory if needed
        (wav2lip_dir / "temp").mkdir(exist_ok=True)
        (wav2lip_dir / "results").mkdir(exist_ok=True)

        # Build command with absolute paths
        cmd = [
            "python",
            str(inference_script),
            "--checkpoint_path",
            str(wav2lip_dir / "checkpoints" / "wav2lip_gan.pth"),
            "--face",
            str(Path(avatar_image).absolute()),
            "--audio",
            str(Path(audio_path).absolute()),
            "--outfile",
            str(Path(output_path).absolute()),
        ]

        logger.info("🎬 Generating lip-sync video with Wav2Lip...")
        logger.info(f"   Avatar: {avatar_image.name}")
        logger.info(f"   Audio: {audio_path}")

        try:
            result = subprocess.run(
                cmd, cwd=str(wav2lip_dir), capture_output=True, text=True, timeout=120
            )

            if result.returncode == 0 and output_path.exists():
                logger.info(f"✅ Lip-sync video generated: {output_path}")
                return output_path
            else:
                logger.error(f"❌ Wav2Lip failed: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logger.error("❌ Wav2Lip timed out (>120s)")
            return None
        except Exception as e:
            logger.error(f"❌ Wav2Lip error: {e}")
            return None

    def sync_musetalk(self, audio_path, avatar_image=None, output_path=None):
        """
        Generate real-time lip-sync using MuseTalk (faster, 30+ FPS)

        Args:
            audio_path: Path to audio file
            avatar_image: Path to BROCKSTON's image
            output_path: Where to save video

        Returns:
            Path to generated video
        """
        if "musetalk" not in self.available_models:
            logger.error("❌ MuseTalk not available")
            return None

        # Use default avatar if not specified
        if avatar_image is None:
            avatar_image = self.avatars["default"]

        if output_path is None:
            output_path = Path(tempfile.mktemp(suffix=".mp4"))

        musetalk_dir = self.available_models["musetalk"]

        logger.info("🎬 Generating real-time lip-sync with MuseTalk...")
        logger.info(f"   Avatar: {avatar_image.name}")
        logger.info(f"   Audio: {audio_path}")

        # MuseTalk implementation would go here
        # For now, return placeholder
        logger.warning("⚠️  MuseTalk integration coming soon")
        return None

    def speak(self, audio_path, avatar="default", model="wav2lip", output_path=None):
        """
        Make BROCKSTON speak with lip-sync

        Args:
            audio_path: Path to audio file from TTS
            avatar: Which avatar to use ("default", "professional", "happy", etc.)
            model: Which lip-sync model to use ("wav2lip", "musetalk", "sadtalker")
            output_path: Where to save video

        Returns:
            Path to lip-synced video of BROCKSTON speaking
        """
        # Get avatar image
        avatar_image = self.avatars.get(avatar, self.avatars["default"])

        if not avatar_image.exists():
            logger.error(f"❌ Avatar image not found: {avatar_image}")
            return None

        # Choose model
        if model == "wav2lip":
            return self.sync_wav2lip(audio_path, avatar_image, output_path)
        elif model == "musetalk":
            return self.sync_musetalk(audio_path, avatar_image, output_path)
        else:
            logger.error(f"❌ Unknown model: {model}")
            return None

    def introduce_yourself(self):
        """
        BROCKSTON introduces himself with video

        Returns:
            Path to introduction video
        """
        logger.info("🎤 BROCKSTON is introducing himself...")

        # First, generate the audio using speech.py
        try:
            from speech import text_to_speech

            intro_text = """
            Hello! I'm BROCKSTON, your AI assistant. 
            I'm here to help with coding, learning, and support.
            I'm powered by advanced AI and I'm always learning to be better.
            Let's work together to build something amazing!
            """

            # Generate audio
            audio_path = text_to_speech(
                intro_text,
                voice_id="Matthew",
                output_path=str(PROJECT_ROOT / "brockston_intro.mp3"),
            )

            if audio_path and Path(audio_path).exists():
                logger.info(f"✅ Audio generated: {audio_path}")

                # Generate lip-sync video
                video_path = self.speak(
                    audio_path,
                    avatar="default",
                    model="wav2lip",
                    output_path=str(PROJECT_ROOT / "brockston_intro.mp4"),
                )

                if video_path:
                    logger.info(f"🎉 BROCKSTON introduction complete: {video_path}")
                    return video_path
                else:
                    logger.error("❌ Video generation failed")
                    return None
            else:
                logger.error("❌ Audio generation failed")
                return None

        except ImportError as e:
            logger.error(f"❌ Could not import speech module: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Introduction failed: {e}")
            return None


if __name__ == "__main__":
    print("🎭 BROCKSTON Lip-Sync Engine Test")
    print("=" * 70)

    engine = LipSyncEngine()

    print("\n📦 Available Models:")
    for model_name in engine.available_models:
        print(f"   ✅ {model_name}")

    print("\n🎭 Available Avatars:")
    for avatar_name, avatar_path in engine.avatars.items():
        exists = "✅" if avatar_path.exists() else "❌"
        print(f"   {exists} {avatar_name}: {avatar_path.name}")

    print("\n🎬 Ready to make BROCKSTON talk!")
    print("   Use: engine.introduce_yourself()")
    print("   Or: engine.speak(audio_path, avatar='default')")
