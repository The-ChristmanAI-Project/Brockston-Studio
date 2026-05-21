#!/usr/bin/env python3
"""
BROCKSTON Full-Body Avatar Manipulation
=========================================
Complete avatar control with:
- Full body pose estimation
- Facial expressions and emotions
- Lip-sync with speech
- Gesture and movement
- Real-time animation
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import time
import json

# Import the base avatar system
from embodiment.avatar.full_avatar import (
    BrockstonFullAvatar,
    EmotionState,
    AnimationState,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BodyPose(Enum):
    """Full body poses"""

    STANDING_NEUTRAL = "standing_neutral"
    STANDING_CONFIDENT = "standing_confident"
    SITTING = "sitting"
    GESTURING_LEFT = "gesturing_left"
    GESTURING_RIGHT = "gesturing_right"
    GESTURING_BOTH = "gesturing_both"
    THINKING_POSE = "thinking_pose"
    WELCOMING = "welcoming"
    PRESENTING = "presenting"


class GestureType(Enum):
    """Types of gestures"""

    NONE = "none"
    WAVE = "wave"
    POINT = "point"
    THUMBS_UP = "thumbs_up"
    NOD = "nod"
    SHAKE_HEAD = "shake_head"
    SHRUG = "shrug"
    CLAP = "clap"


@dataclass
class FullBodyState:
    """Complete state of BROCKSTON's avatar"""

    emotion: EmotionState
    animation: AnimationState
    body_pose: BodyPose
    gesture: GestureType
    head_rotation: Tuple[float, float, float]  # pitch, yaw, roll
    body_rotation: Tuple[float, float, float]  # pitch, yaw, roll
    arm_left_angle: float  # 0-180 degrees
    arm_right_angle: float  # 0-180 degrees
    timestamp: float


class BrockstonFullBodyAvatar(BrockstonFullAvatar):
    """
    🎭 BROCKSTON - Full Body Avatar with Complete Manipulation

    Extends the base avatar with full body control, gestures, and poses.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

        # Full body state
        self.body_pose = BodyPose.STANDING_NEUTRAL
        self.current_gesture = GestureType.NONE

        # Body positioning
        self.head_rotation = (0.0, 0.0, 0.0)  # pitch, yaw, roll
        self.body_rotation = (0.0, 0.0, 0.0)
        self.arm_left_angle = 0.0
        self.arm_right_angle = 0.0

        # Gesture animation
        self.gesture_in_progress = False
        self.gesture_frame = 0

        # Full body manipulation enabled
        self.fullbody_enabled = True

        logger.info("🎭 BROCKSTON Full-Body Avatar initialized!")
        logger.info("   Full body manipulation: ENABLED")
        logger.info("   Poses available: 9")
        logger.info("   Gestures available: 8")

    def set_body_pose(self, pose: BodyPose):
        """Set full body pose"""
        logger.info(f"🧍 BROCKSTON body pose: {self.body_pose.value} → {pose.value}")
        self.body_pose = pose

        # Adjust arm angles based on pose
        pose_configs = {
            BodyPose.STANDING_NEUTRAL: (0, 0),
            BodyPose.STANDING_CONFIDENT: (20, 20),
            BodyPose.GESTURING_LEFT: (120, 10),
            BodyPose.GESTURING_RIGHT: (10, 120),
            BodyPose.GESTURING_BOTH: (90, 90),
            BodyPose.THINKING_POSE: (30, 90),  # Hand on chin
            BodyPose.WELCOMING: (45, 45),
            BodyPose.PRESENTING: (60, 90),
        }

        if pose in pose_configs:
            self.arm_left_angle, self.arm_right_angle = pose_configs[pose]

    def perform_gesture(self, gesture: GestureType, duration: float = 2.0):
        """Perform a gesture animation"""
        logger.info(f"👋 BROCKSTON performing gesture: {gesture.value}")

        self.current_gesture = gesture
        self.gesture_in_progress = True
        self.gesture_frame = 0

        # Gesture animations
        if gesture == GestureType.WAVE:
            self._animate_wave()
        elif gesture == GestureType.POINT:
            self._animate_point()
        elif gesture == GestureType.THUMBS_UP:
            self._animate_thumbs_up()
        elif gesture == GestureType.NOD:
            self._animate_nod()
        elif gesture == GestureType.SHAKE_HEAD:
            self._animate_shake_head()
        elif gesture == GestureType.SHRUG:
            self._animate_shrug()
        elif gesture == GestureType.CLAP:
            self._animate_clap()

        self.gesture_in_progress = False
        self.current_gesture = GestureType.NONE

    def _animate_wave(self):
        """Animate waving gesture"""
        for i in range(3):  # Wave 3 times
            # Raise arm
            for angle in range(0, 120, 10):
                self.arm_right_angle = angle
                time.sleep(0.05)

            # Wave motion
            for _ in range(2):
                for angle in range(120, 140, 5):
                    self.arm_right_angle = angle
                    time.sleep(0.05)
                for angle in range(140, 120, -5):
                    self.arm_right_angle = angle
                    time.sleep(0.05)

        # Lower arm
        for angle in range(120, 0, -10):
            self.arm_right_angle = angle
            time.sleep(0.05)

    def _animate_point(self):
        """Animate pointing gesture"""
        # Raise arm to point
        for angle in range(0, 90, 10):
            self.arm_right_angle = angle
            time.sleep(0.05)

        # Hold point
        time.sleep(1.0)

        # Lower arm
        for angle in range(90, 0, -10):
            self.arm_right_angle = angle
            time.sleep(0.05)

    def _animate_thumbs_up(self):
        """Animate thumbs up gesture"""
        # Raise arm with thumbs up
        for angle in range(0, 60, 10):
            self.arm_right_angle = angle
            time.sleep(0.05)

        # Hold thumbs up
        self.set_emotion(EmotionState.HAPPY)
        time.sleep(1.5)

        # Lower arm
        for angle in range(60, 0, -10):
            self.arm_right_angle = angle
            time.sleep(0.05)

    def _animate_nod(self):
        """Animate head nod"""
        for _ in range(2):  # Nod twice
            # Nod down
            for pitch in range(0, 15, 3):
                self.head_rotation = (pitch, 0, 0)
                time.sleep(0.05)

            # Nod up
            for pitch in range(15, 0, -3):
                self.head_rotation = (pitch, 0, 0)
                time.sleep(0.05)

    def _animate_shake_head(self):
        """Animate head shake (no)"""
        for _ in range(2):  # Shake twice
            # Shake left
            for yaw in range(0, 20, 4):
                self.head_rotation = (0, yaw, 0)
                time.sleep(0.05)

            # Shake right
            for yaw in range(20, -20, -4):
                self.head_rotation = (0, yaw, 0)
                time.sleep(0.05)

            # Return center
            for yaw in range(-20, 0, 4):
                self.head_rotation = (0, yaw, 0)
                time.sleep(0.05)

    def _animate_shrug(self):
        """Animate shoulder shrug"""
        # Raise both arms slightly
        for angle in range(0, 30, 5):
            self.arm_left_angle = angle
            self.arm_right_angle = angle
            time.sleep(0.05)

        # Hold shrug
        time.sleep(1.0)

        # Lower arms
        for angle in range(30, 0, -5):
            self.arm_left_angle = angle
            self.arm_right_angle = angle
            time.sleep(0.05)

    def _animate_clap(self):
        """Animate clapping"""
        for _ in range(5):  # Clap 5 times
            # Bring arms together
            for angle in range(0, 90, 30):
                self.arm_left_angle = angle
                self.arm_right_angle = angle
                time.sleep(0.05)

            # Clap!
            time.sleep(0.1)

            # Separate arms
            for angle in range(90, 0, -30):
                self.arm_left_angle = angle
                self.arm_right_angle = angle
                time.sleep(0.05)

    def get_full_state(self) -> FullBodyState:
        """Get complete avatar state"""
        return FullBodyState(
            emotion=self.current_emotion,
            animation=self.current_animation,
            body_pose=self.body_pose,
            gesture=self.current_gesture,
            head_rotation=self.head_rotation,
            body_rotation=self.body_rotation,
            arm_left_angle=self.arm_left_angle,
            arm_right_angle=self.arm_right_angle,
            timestamp=time.time(),
        )

    def load_state_from_dict(self, state_dict: Dict[str, Any]):
        """Load avatar state from dictionary"""
        if "emotion" in state_dict:
            self.set_emotion(EmotionState(state_dict["emotion"]))
        if "animation" in state_dict:
            self.set_animation(AnimationState(state_dict["animation"]))
        if "body_pose" in state_dict:
            self.set_body_pose(BodyPose(state_dict["body_pose"]))
        if "head_rotation" in state_dict:
            self.head_rotation = tuple(state_dict["head_rotation"])
        if "arm_angles" in state_dict:
            self.arm_left_angle = state_dict["arm_angles"][0]
            self.arm_right_angle = state_dict["arm_angles"][1]

    def manipulate_full_body(
        self,
        emotion: Optional[EmotionState] = None,
        pose: Optional[BodyPose] = None,
        gesture: Optional[GestureType] = None,
        head_rotation: Optional[Tuple[float, float, float]] = None,
        arm_angles: Optional[Tuple[float, float]] = None,
    ):
        """
        Comprehensive full-body manipulation

        Args:
            emotion: Facial emotion
            pose: Body pose
            gesture: Gesture to perform
            head_rotation: (pitch, yaw, roll) in degrees
            arm_angles: (left, right) arm angles in degrees
        """
        logger.info("🎭 BROCKSTON full body manipulation in progress...")

        if emotion:
            self.set_emotion(emotion)

        if pose:
            self.set_body_pose(pose)

        if head_rotation:
            self.head_rotation = head_rotation

        if arm_angles:
            self.arm_left_angle, self.arm_right_angle = arm_angles

        if gesture:
            self.perform_gesture(gesture)

        state = self.get_full_state()
        logger.info(f"✅ Full body state updated: {state}")

        return state

    def react_to_context(self, context: str):
        """
        Autonomous reaction to context
        BROCKSTON decides how to react based on the context
        """
        context_lower = context.lower()

        # Greeting
        if any(word in context_lower for word in ["hello", "hi", "hey", "greetings"]):
            self.set_emotion(EmotionState.HAPPY)
            self.perform_gesture(GestureType.WAVE)

        # Agreement
        elif any(
            word in context_lower for word in ["yes", "correct", "right", "agreed"]
        ):
            self.set_emotion(EmotionState.CONFIDENT)
            self.perform_gesture(GestureType.NOD)

        # Disagreement
        elif any(word in context_lower for word in ["no", "wrong", "incorrect"]):
            self.set_emotion(EmotionState.THINKING)
            self.perform_gesture(GestureType.SHAKE_HEAD)

        # Success/Celebration
        elif any(
            word in context_lower for word in ["success", "great", "awesome", "perfect"]
        ):
            self.set_emotion(EmotionState.EXCITED)
            self.perform_gesture(GestureType.THUMBS_UP)

        # Confusion/Uncertainty
        elif any(
            word in context_lower
            for word in ["confused", "unsure", "maybe", "don't know"]
        ):
            self.set_emotion(EmotionState.CURIOUS)
            self.perform_gesture(GestureType.SHRUG)

        # Thinking/Processing
        elif any(
            word in context_lower
            for word in ["think", "consider", "analyze", "processing"]
        ):
            self.set_emotion(EmotionState.THINKING)
            self.set_body_pose(BodyPose.THINKING_POSE)

        # Presentation
        elif any(
            word in context_lower
            for word in ["show", "present", "demonstrate", "explain"]
        ):
            self.set_emotion(EmotionState.CONFIDENT)
            self.set_body_pose(BodyPose.PRESENTING)

    def __repr__(self):
        return (
            f"<BrockstonFullBodyAvatar "
            f"emotion={self.current_emotion.value} "
            f"pose={self.body_pose.value} "
            f"gesture={self.current_gesture.value} "
            f"intelligence={self.intelligence_level:.1f}%>"
        )


def demonstrate_full_body_manipulation():
    """Demonstrate full body avatar manipulation"""

    print("=" * 70)
    print("🎭 BROCKSTON FULL-BODY AVATAR MANIPULATION DEMO")
    print("=" * 70)
    print()

    # Create avatar
    avatar = BrockstonFullBodyAvatar()

    print("✨ BROCKSTON is alive with full-body control!")
    print(f"   {avatar}")
    print()

    # Demonstration sequence
    demos = [
        {
            "name": "Confident Welcome",
            "emotion": EmotionState.HAPPY,
            "pose": BodyPose.WELCOMING,
            "gesture": GestureType.WAVE,
        },
        {
            "name": "Thinking Deeply",
            "emotion": EmotionState.THINKING,
            "pose": BodyPose.THINKING_POSE,
            "gesture": None,
        },
        {
            "name": "Excited Success",
            "emotion": EmotionState.EXCITED,
            "pose": BodyPose.STANDING_CONFIDENT,
            "gesture": GestureType.THUMBS_UP,
        },
        {
            "name": "Professional Presentation",
            "emotion": EmotionState.CONFIDENT,
            "pose": BodyPose.PRESENTING,
            "gesture": GestureType.POINT,
        },
        {
            "name": "Celebration",
            "emotion": EmotionState.HAPPY,
            "pose": BodyPose.STANDING_NEUTRAL,
            "gesture": GestureType.CLAP,
        },
    ]

    for i, demo in enumerate(demos, 1):
        print(f"{i}. {demo['name']}")
        print(f"   Emotion: {demo['emotion'].value}")
        print(f"   Pose: {demo['pose'].value}")
        if demo["gesture"]:
            print(f"   Gesture: {demo['gesture'].value}")

        avatar.manipulate_full_body(
            emotion=demo["emotion"], pose=demo["pose"], gesture=demo["gesture"]
        )

        print(f"   State: {avatar}")
        print()

    # Context-aware reactions
    print("=" * 70)
    print("🤖 CONTEXT-AWARE REACTIONS")
    print("=" * 70)
    print()

    contexts = [
        "Hello BROCKSTON!",
        "Yes, that's correct!",
        "Success! It works!",
        "I'm confused about this...",
        "Let me explain how this works",
    ]

    for context in contexts:
        print(f"Context: '{context}'")
        avatar.react_to_context(context)
        print(f"Reaction: {avatar}")
        print()

    print("=" * 70)
    print("✅ Full-body manipulation demonstration complete!")
    print("=" * 70)


if __name__ == "__main__":
    demonstrate_full_body_manipulation()
