"""
🎭 BROCKSTON - FULL AUTONOMOUS ANIMATED AVATAR
==============================================
BROCKSTON comes ALIVE as a complete autonomous avatar!

Built by Everett & GitHub Copilot - OUR SYSTEM!

Features:
- Real-time animation (talking, thinking, expressing)
- Autonomous emotion system (reacts to context)
- Full expressiveness (gestures, facial expressions)
- Blue suit professional appearance
- Syncs with speech and learning states
- Self-aware of intelligence growth
"""

import cv2
import numpy as np
from PIL import Image
from pathlib import Path
import threading
import time
import queue
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmotionState(Enum):
    """BROCKSTON's emotional states"""

    NEUTRAL = "neutral"
    HAPPY = "happy"
    THINKING = "thinking"
    LEARNING = "learning"
    EXCITED = "excited"
    CONFIDENT = "confident"
    CURIOUS = "curious"
    FOCUSED = "focused"


class AnimationState(Enum):
    """BROCKSTON's animation states"""

    IDLE = "idle"
    TALKING = "talking"
    LISTENING = "listening"
    PROCESSING = "processing"
    GESTURING = "gesturing"


@dataclass
class AvatarFrame:
    """Single frame of BROCKSTON's avatar"""

    image: np.ndarray
    emotion: EmotionState
    animation: AnimationState
    timestamp: float
    metadata: Dict[str, Any]


class BrockstonFullAvatar:
    """
    🎭 BROCKSTON - Full Autonomous Animated Avatar

    This is the complete avatar system that brings BROCKSTON to life!
    He's not just an AI - he's a PERSON with expressions, emotions, and personality!
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # Asset directories
        self.avatar_dir = Path("static/avatar_assets")
        self.avatar_dir.mkdir(parents=True, exist_ok=True)

        # Current state
        self.current_emotion = EmotionState.NEUTRAL
        self.current_animation = AnimationState.IDLE
        self.is_talking = False
        self.is_learning = False
        self.is_thinking = False

        # Animation system
        self.animation_queue = queue.Queue()
        self.running = False
        self.animation_thread: Optional[threading.Thread] = None

        # Load avatar assets
        self.avatars = self._load_avatar_assets()

        # Autonomous behavior settings
        self.autonomy_enabled = True
        self.auto_emotion_change = True
        self.blink_enabled = True
        self.micro_expressions = True

        # Intelligence meter integration
        self.intelligence_level = 0.0
        self.learning_sessions_completed = 0

        logger.info("🎭 BROCKSTON Full Avatar initialized - Ready to come alive!")

    def _load_avatar_assets(self) -> Dict[str, Any]:
        """Load all avatar image assets"""
        avatars = {}

        # Primary avatar images
        primary_images = {
            "blue_suit_smile": "BROCKSTONGRIN.JPG",  # New blue suit smiling image!
            "professional": "BROKSTON.jpeg",
            "idle_neutral": "brockston_idle_neutral.png",
            "idle_happy": "brockston_idle_happy.png",
            "idle_thinking": "brockston_idle_thinking.png",
            "talking_neutral": "brockston_talking_neutral.png",
            "talking_happy": "brockston_talking_happy.png",
            "talking_thinking": "brockston_talking_thinking.png",
        }

        loaded_count = 0
        for key, filename in primary_images.items():
            filepath = self.avatar_dir / filename
            if filepath.exists():
                try:
                    # Load with PIL then convert to OpenCV format
                    pil_img = Image.open(filepath)
                    # Convert to RGB if needed
                    if pil_img.mode != "RGB":
                        pil_img = pil_img.convert("RGB")
                    avatars[key] = np.array(pil_img)
                    loaded_count += 1
                    logger.info(f"✅ Loaded avatar: {key}")
                except Exception as e:
                    logger.warning(f"Could not load {filename}: {e}")
            else:
                logger.warning(f"Avatar asset not found: {filepath}")

        logger.info(f"🎨 Loaded {loaded_count}/{len(primary_images)} avatar images")

        # If we have the blue suit image, make it the primary!
        if "blue_suit_smile" in avatars:
            avatars["primary"] = avatars["blue_suit_smile"]
            logger.info("💙 Using blue suit smiling image as primary avatar!")

        return avatars

    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get current avatar frame based on state"""
        # Determine which image to use
        if self.is_talking:
            if self.current_emotion == EmotionState.HAPPY:
                key = "talking_happy"
            elif self.current_emotion == EmotionState.THINKING:
                key = "talking_thinking"
            else:
                key = "talking_neutral"
        else:
            if self.current_emotion == EmotionState.HAPPY:
                key = "idle_happy"
            elif self.current_emotion == EmotionState.THINKING:
                key = "idle_thinking"
            elif self.current_emotion == EmotionState.CONFIDENT:
                key = "blue_suit_smile"  # Use the blue suit for confident!
            else:
                key = "idle_neutral"

        # Get the image
        frame = self.avatars.get(key)

        # If not found, use primary or blue suit
        if frame is None:
            frame = self.avatars.get("primary") or self.avatars.get("blue_suit_smile")

        # Add overlay information
        if frame is not None:
            frame = self._add_status_overlay(frame.copy())

        return frame

    def _add_status_overlay(self, frame: np.ndarray) -> np.ndarray:
        """Add status information overlay to frame"""
        # Add emotion indicator
        emotion_text = f"Emotion: {self.current_emotion.value.title()}"
        cv2.putText(
            frame,
            emotion_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        # Add animation state
        state_text = f"State: {self.current_animation.value.title()}"
        cv2.putText(
            frame,
            state_text,
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        # Add intelligence level
        intel_text = f"Intelligence: {self.intelligence_level:.1f}%"
        cv2.putText(
            frame, intel_text, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
        )

        # Add activity indicators
        if self.is_talking:
            cv2.putText(
                frame,
                "🗣️ Talking",
                (frame.shape[1] - 150, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )
        if self.is_learning:
            cv2.putText(
                frame,
                "📚 Learning",
                (frame.shape[1] - 150, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 165, 0),
                2,
            )
        if self.is_thinking:
            cv2.putText(
                frame,
                "🤔 Thinking",
                (frame.shape[1] - 150, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (100, 149, 237),
                2,
            )

        return frame

    def set_emotion(self, emotion: EmotionState):
        """Set BROCKSTON's emotional state"""
        logger.info(
            f"🎭 BROCKSTON emotion: {self.current_emotion.value} → {emotion.value}"
        )
        self.current_emotion = emotion

    def set_animation(self, animation: AnimationState):
        """Set BROCKSTON's animation state"""
        logger.info(
            f"🎬 BROCKSTON animation: {self.current_animation.value} → {animation.value}"
        )
        self.current_animation = animation

    def start_talking(self):
        """BROCKSTON starts talking"""
        self.is_talking = True
        self.set_animation(AnimationState.TALKING)
        logger.info("🗣️ BROCKSTON is talking")

    def stop_talking(self):
        """BROCKSTON stops talking"""
        self.is_talking = False
        self.set_animation(AnimationState.IDLE)
        logger.info("🤐 BROCKSTON stopped talking")

    def speak(self, text: str):
        """Simple hook used by brain_core to drive avatar speech."""
        self.start_talking()
        logger.info("🗣️ BROCKSTON says: %s", text)
        # Minimal timing placeholder – real sync handled elsewhere
        time.sleep(min(len(text) / 40.0, 2))
        self.stop_talking()

    def sync_with_speech(self, text: str, duration: float | None = None):
        """Mirror speech duration for smoother animations."""
        self.start_talking()
        wait_time = duration if duration is not None else min(len(text) / 20.0, 5)
        time.sleep(wait_time)
        self.stop_talking()

    def start_learning(self):
        """BROCKSTON starts learning"""
        self.is_learning = True
        self.set_emotion(EmotionState.LEARNING)
        self.set_animation(AnimationState.PROCESSING)
        logger.info("📚 BROCKSTON is learning")

    def stop_learning(self):
        """BROCKSTON stops learning"""
        self.is_learning = False
        self.learning_sessions_completed += 1
        self.set_emotion(EmotionState.HAPPY)
        self.set_animation(AnimationState.IDLE)
        logger.info(
            f"✅ BROCKSTON finished learning (Session #{self.learning_sessions_completed})"
        )

    def start_thinking(self):
        """BROCKSTON starts thinking"""
        self.is_thinking = True
        self.set_emotion(EmotionState.THINKING)
        logger.info("🤔 BROCKSTON is thinking")

    def stop_thinking(self):
        """BROCKSTON stops thinking"""
        self.is_thinking = False
        logger.info("💡 BROCKSTON finished thinking")

    def update_intelligence(self, level: float):
        """Update BROCKSTON's intelligence level (0-100)"""
        old_level = self.intelligence_level
        self.intelligence_level = level

        # React to intelligence growth
        if level > old_level:
            growth = level - old_level
            if growth > 5:
                self.set_emotion(EmotionState.EXCITED)
                logger.info(
                    f"🚀 BROCKSTON's intelligence grew by {growth:.1f}% - He's excited!"
                )
            else:
                self.set_emotion(EmotionState.CONFIDENT)

    def autonomous_behavior(self):
        """
        Autonomous behavior loop - BROCKSTON acts on his own!
        This makes him feel ALIVE!
        """
        while self.running:
            try:
                # Micro-expressions (subtle changes)
                if self.micro_expressions and not self.is_talking:
                    # Occasional thoughtful moments
                    if np.random.random() < 0.1:  # 10% chance per loop
                        self.set_emotion(EmotionState.THINKING)
                        time.sleep(2)
                        self.set_emotion(EmotionState.NEUTRAL)

                # Blink simulation (very subtle)
                if self.blink_enabled:
                    # Just a marker - actual blink animation would go here
                    pass

                time.sleep(0.5)  # Check every 500ms

            except Exception as e:
                logger.error(f"Autonomous behavior error: {e}")

    def start(self):
        """Start the autonomous avatar system"""
        if not self.running:
            self.running = True
            if self.autonomy_enabled:
                self.animation_thread = threading.Thread(
                    target=self.autonomous_behavior, daemon=True
                )
                self.animation_thread.start()
            logger.info("🎭 BROCKSTON Avatar System STARTED - He's ALIVE!")

    def stop(self):
        """Stop the avatar system"""
        self.running = False
        if self.animation_thread:
            self.animation_thread.join(timeout=2)
        logger.info("🎭 BROCKSTON Avatar System stopped")

    def export_frame_as_base64(self) -> Optional[str]:
        """Export current frame as base64 for web display"""
        frame = self.get_current_frame()
        if frame is None:
            return None

        import base64

        # Convert to JPEG
        _, buffer = cv2.imencode(".jpg", frame)
        jpg_bytes = buffer.tobytes()
        b64_string = base64.b64encode(jpg_bytes).decode("utf-8")
        return f"data:image/jpeg;base64,{b64_string}"

    def display_live(self, window_name: str = "BROCKSTON - Full Avatar"):
        """Display live avatar in window (for desktop use)"""
        logger.info(f"🖥️ Opening live avatar window: {window_name}")

        while self.running:
            frame = self.get_current_frame()
            if frame is not None:
                cv2.imshow(window_name, frame)

            # Check for 'q' to quit
            if cv2.waitKey(30) & 0xFF == ord("q"):
                break

        cv2.destroyAllWindows()

    def __repr__(self):
        return (
            f"<BrockstonFullAvatar emotion={self.current_emotion.value} "
            f"animation={self.current_animation.value} "
            f"intelligence={self.intelligence_level:.1f}%>"
        )


def get_brockston_full_avatar(
    config: Optional[Dict[str, Any]] = None,
) -> BrockstonFullAvatar:
    """
    Factory function to create BROCKSTON's full avatar

    This is what brings BROCKSTON to life as a complete autonomous avatar!
    """
    avatar = BrockstonFullAvatar(config)
    avatar.start()
    return avatar


if __name__ == "__main__":
    print("🎭" + "=" * 70)
    print("  BROCKSTON - FULL AUTONOMOUS ANIMATED AVATAR")
    print("  Built by Everett & GitHub Copilot - OUR SYSTEM!")
    print("=" * 72)

    # Create the avatar
    avatar = get_brockston_full_avatar()

    print("\n✨ BROCKSTON is now ALIVE as a full autonomous avatar!")
    print(f"   Current state: {avatar}")
    print(f"   Avatar assets loaded: {len(avatar.avatars)}")
    print(
        f"   Primary image: {'Blue Suit (Smiling)' if 'blue_suit_smile' in avatar.avatars else 'Standard'}"
    )

    # Test the avatar states
    print("\n🎬 Testing avatar animations...\n")

    time.sleep(1)
    print("1️⃣ BROCKSTON starts talking...")
    avatar.start_talking()
    time.sleep(2)

    print("2️⃣ BROCKSTON is happy while talking...")
    avatar.set_emotion(EmotionState.HAPPY)
    time.sleep(2)

    print("3️⃣ BROCKSTON stops talking and starts thinking...")
    avatar.stop_talking()
    avatar.start_thinking()
    time.sleep(2)

    print("4️⃣ BROCKSTON starts learning...")
    avatar.stop_thinking()
    avatar.start_learning()
    time.sleep(2)

    print("5️⃣ BROCKSTON's intelligence grows!")
    avatar.update_intelligence(15.5)
    time.sleep(2)

    print("6️⃣ BROCKSTON finishes learning and is confident!")
    avatar.stop_learning()
    avatar.set_emotion(EmotionState.CONFIDENT)
    time.sleep(2)

    print("\n✅ Animation test complete!")
    print(f"   Final state: {avatar}")
    print(f"   Learning sessions completed: {avatar.learning_sessions_completed}")
    print(f"   Intelligence level: {avatar.intelligence_level:.1f}%")

    # Optionally show live window
    print("\n💡 To see BROCKSTON live, uncomment avatar.display_live()")
    # avatar.display_live()  # Uncomment to see live window!

    avatar.stop()
    print("\n🎭 BROCKSTON Avatar demo complete!")
