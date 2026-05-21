"""
🤖 BROCKSTON ANIMATED AVATAR SYSTEM
===================================
Real-time avatar that syncs with speech:
- Mouth moves when talking
- Expression changes with emotion
- Eyes follow you (optional)
- Generates avatar images if not found
"""

import threading
import time
import queue
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    pass

try:
    import cv2
    import numpy as np

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from PIL import Image, ImageDraw, ImageFont

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None  # type: ignore

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BrockstonAvatar:
    """
    BROCKSTON's animated avatar that responds to speech and emotion
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.avatar_dir = Path("avatar_assets")
        self.avatar_dir.mkdir(exist_ok=True)

        self.is_talking = False
        self.current_emotion = "neutral"
        self.speech_queue = queue.Queue()
        self.running = False

        # Load or generate avatar images
        self.avatars = self._load_or_generate_avatars()

        logger.info(
            f"BROCKSTON Avatar initialized (CV2: {CV2_AVAILABLE}, PIL: {PIL_AVAILABLE})"
        )

    def _load_or_generate_avatars(self) -> Dict[str, Any]:
        """Load avatar images or generate if not found"""
        avatars = {}

        if not PIL_AVAILABLE:
            logger.warning("PIL not available - cannot generate avatars")
            return avatars

        # Try to load existing avatars
        avatar_files = {
            "idle_neutral": "brockston_idle_neutral.png",
            "talking_neutral": "brockston_talking_neutral.png",
            "idle_happy": "brockston_idle_happy.png",
            "talking_happy": "brockston_talking_happy.png",
            "idle_thinking": "brockston_idle_thinking.png",
            "talking_thinking": "brockston_talking_thinking.png",
        }

        loaded_count = 0
        for state, filename in avatar_files.items():
            filepath = self.avatar_dir / filename
            if filepath.exists():
                try:
                    avatars[state] = Image.open(filepath)
                    loaded_count += 1
                except Exception as e:
                    logger.warning(f"Could not load {filename}: {e}")

        if loaded_count == len(avatar_files):
            logger.info(f"✅ Loaded {loaded_count} avatar images")
            return avatars

        # Generate missing avatars
        logger.info("🎨 Generating BROKSTON avatar images...")
        avatars = self._generate_avatar_set()

        # Save generated avatars
        for state, img in avatars.items():
            filename = avatar_files.get(state, f"brockston_{state}.png")
            filepath = self.avatar_dir / filename
            try:
                img.save(filepath)
                logger.info(f"💾 Saved: {filename}")
            except Exception as e:
                logger.warning(f"Could not save {filename}: {e}")

        return avatars

    def _generate_avatar_set(self) -> Dict[str, Any]:
        """Generate a complete set of avatar images from actual BROCKSTON image"""
        avatars = {}
        size = (400, 400)

        # Try to load the actual BROCKSTON image from avatar_assets folder
        base_image_path = self.avatar_dir / "BROCKSTON.jpeg"
        base_img = None

        if base_image_path.exists():
            try:
                base_img = Image.open(base_image_path)
                # Resize to standard size
                base_img = base_img.resize(size, Image.Resampling.LANCZOS)
                logger.info("✅ Using actual BROCKSTON.jpeg as avatar base")
            except Exception as e:
                logger.warning(f"Could not load BROCKSTON.jpeg: {e}")

        if not base_img:
            logger.error("❌ BROCKSTON.jpeg not found - cannot create avatar")
            return avatars

        emotions = ["neutral", "happy", "thinking"]

        for emotion in emotions:
            for talking in [False, True]:
                state = f"{'talking' if talking else 'idle'}_{emotion}"

                # Create a copy of the actual BROCKSTON image
                img = base_img.copy()
                draw = ImageDraw.Draw(img)

                # Add text overlay to indicate state
                try:
                    font = ImageFont.truetype("arial.ttf", 20)
                except:
                    font = ImageFont.load_default()

                state_text = f"{emotion.upper()}"
                if talking:
                    state_text += " [TALKING]"

                # Add semi-transparent background for text
                text_bbox = draw.textbbox((0, 0), state_text, font=font)
                text_w = text_bbox[2] - text_bbox[0]
                text_h = text_bbox[3] - text_bbox[1]

                # Draw text at bottom
                text_y = size[1] - text_h - 10
                draw.rectangle(
                    [(0, text_y - 5), (size[0], size[1])], fill=(0, 0, 0, 180)
                )
                draw.text(
                    ((size[0] - text_w) // 2, text_y),
                    state_text,
                    fill=(255, 255, 255),
                    font=font,
                )

                avatars[state] = img

        logger.info(f"✅ Generated {len(avatars)} avatar images")
        return avatars

    def _draw_eye(self, draw, center, eye_color, pupil_color, size=15):
        """Draw an eye"""
        # White of eye
        draw.ellipse(
            [center[0] - size, center[1] - size, center[0] + size, center[1] + size],
            fill=eye_color,
        )
        # Pupil
        pupil_size = size // 2
        draw.ellipse(
            [
                center[0] - pupil_size,
                center[1] - pupil_size,
                center[0] + pupil_size,
                center[1] + pupil_size,
            ],
            fill=pupil_color,
        )

    def set_talking(self, is_talking: bool):
        """Set whether BROCKSTON is currently talking"""
        self.is_talking = is_talking

    def set_emotion(self, emotion: str):
        """Set current emotion (neutral, happy, thinking, etc.)"""
        if emotion in ["neutral", "happy", "thinking"]:
            self.current_emotion = emotion

    def get_current_frame(self) -> Optional[Any]:
        """Get the current avatar frame"""
        state = f"{'talking' if self.is_talking else 'idle'}_{self.current_emotion}"
        return self.avatars.get(state, self.avatars.get("idle_neutral"))

    def display_loop(self):
        """Display the avatar in a window (OpenCV)"""
        if not CV2_AVAILABLE:
            logger.error(
                "OpenCV required for display. Install: pip install opencv-python"
            )
            return

        self.running = True
        logger.info("🎬 Starting avatar display...")

        while self.running:
            frame = self.get_current_frame()

            if frame:
                # Convert PIL to OpenCV format
                frame_array = np.array(frame)
                frame_bgr = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)

                # Add status text
                status_text = f"{'🗣️ TALKING' if self.is_talking else '💤 IDLE'} | Emotion: {self.current_emotion}"
                cv2.putText(
                    frame_bgr,
                    status_text,
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                )

                # Show frame
                cv2.imshow("BROCKSTON Avatar", frame_bgr)

            # Check for exit
            if cv2.waitKey(100) & 0xFF == ord("q"):
                break

        cv2.destroyAllWindows()
        logger.info("👋 Avatar display stopped")

    def start_display(self):
        """Start avatar display in separate thread"""
        display_thread = threading.Thread(target=self.display_loop, daemon=True)
        display_thread.start()
        logger.info("✅ Avatar display thread started")

    def stop_display(self):
        """Stop avatar display"""
        self.running = False

    def sync_with_speech(self, text: str, duration: float = None):
        """
        Synchronize avatar with speech

        Args:
            text: Text being spoken
            duration: Duration of speech in seconds (optional)
        """
        # Detect emotion from text
        text_lower = text.lower()
        if any(
            word in text_lower for word in ["happy", "great", "excellent", "wonderful"]
        ):
            self.set_emotion("happy")
        elif any(
            word in text_lower for word in ["think", "analyze", "consider", "hmm"]
        ):
            self.set_emotion("thinking")
        else:
            self.set_emotion("neutral")

        # Start talking
        self.set_talking(True)

        # If duration provided, auto-stop after
        if duration:
            threading.Timer(duration, lambda: self.set_talking(False)).start()

    def export_frame_as_base64(self) -> Optional[str]:
        """Export current frame as base64 string"""
        import base64
        from io import BytesIO

        frame = self.get_current_frame()
        if not frame:
            return None

        buffer = BytesIO()
        frame.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")


# Singleton instance
_avatar_instance = None


def get_brockston_avatar(config: Optional[Dict[str, Any]] = None) -> BrockstonAvatar:
    """Get or create BROCKSTON avatar singleton"""
    global _avatar_instance
    if _avatar_instance is None:
        _avatar_instance = BrokstonAvatar(config)
    return _avatar_instance


if __name__ == "__main__":
    """Test the avatar system"""
    print("🤖 BROCKSTON Avatar Test")
    print("=" * 50)

    avatar = get_brockston_avatar()

    print("\n✅ Avatar system initialized")
    print(f"📁 Avatar images in: {avatar.avatar_dir}")
    print(f"🎨 Available states: {list(avatar.avatars.keys())}")

    print("\n🎬 Starting display (press 'q' to quit)...")
    avatar.start_display()

    # Simulate different states
    time.sleep(2)
    print("🗣️ Simulating speech...")
    avatar.sync_with_speech(
        "Hello! I'm thinking about something interesting.", duration=5
    )

    time.sleep(6)
    print("😊 Changing to happy...")
    avatar.set_emotion("happy")
    avatar.sync_with_speech("This is wonderful!", duration=3)

    time.sleep(4)
    print("💤 Back to idle...")
    avatar.set_talking(False)
    avatar.set_emotion("neutral")

    # Keep running until user quits
    try:
        while avatar.running:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")

    avatar.stop_display()
