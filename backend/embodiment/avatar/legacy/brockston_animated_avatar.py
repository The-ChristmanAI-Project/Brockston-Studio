"""
BROCKSTON Animated Avatar - HEAD MOVEMENT, EXPRESSIONS, GESTURES
Built by Copilot - No external models needed
"""

import cv2
import numpy as np
from pathlib import Path
import logging
from dataclasses import dataclass
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class HeadPose:
    """Head rotation parameters"""

    yaw: float = 0.0  # Left-right rotation (-30 to 30 degrees)
    pitch: float = 0.0  # Up-down rotation (-20 to 20 degrees)
    roll: float = 0.0  # Tilt rotation (-15 to 15 degrees)


@dataclass
class FacialExpression:
    """Facial expression parameters"""

    mouth_open: float = 0.0  # 0.0 to 1.0
    smile: float = 0.0  # 0.0 to 1.0
    eyebrow_raise: float = 0.0  # 0.0 to 1.0
    eye_blink: float = 0.0  # 0.0 to 1.0


class BrockstonAnimatedAvatar:
    """
    BROCKSTON's animated avatar with head movement and expressions
    No external models - pure OpenCV image manipulation
    """

    def __init__(self, base_image_path: Path):
        self.base_image = cv2.imread(str(base_image_path))
        if self.base_image is None:
            raise ValueError(f"Could not load image: {base_image_path}")

        self.height, self.width = self.base_image.shape[:2]
        logger.info(f"🎭 BROCKSTON Avatar loaded: {self.width}x{self.height}")

    def apply_head_pose(self, image: np.ndarray, pose: HeadPose) -> np.ndarray:
        """
        Apply head rotation using perspective transforms
        """
        h, w = image.shape[:2]

        # Create rotation matrix for yaw (left-right)
        # Positive yaw = turn right
        yaw_rad = math.radians(pose.yaw)
        scale_x = abs(math.cos(yaw_rad))  # Face gets narrower when turned

        # Create rotation matrix for pitch (up-down)
        # Positive pitch = look up
        pitch_rad = math.radians(pose.pitch)
        scale_y = abs(math.cos(pitch_rad))

        # Create rotation matrix for roll (tilt)
        roll_rad = math.radians(pose.roll)

        # Combined transformation
        center = (w // 2, h // 2)

        # Apply perspective warp for yaw
        if abs(pose.yaw) > 1:
            # Define source points (original face rectangle)
            pts1 = np.array(
                [
                    [w * 0.2, h * 0.2],
                    [w * 0.8, h * 0.2],
                    [w * 0.2, h * 0.8],
                    [w * 0.8, h * 0.8],
                ],
                dtype=np.float32,
            )

            # Define destination points (rotated face)
            shift = pose.yaw * 0.01  # Scale factor for perspective
            pts2 = np.array(
                [
                    [w * 0.2 - shift * w, h * 0.2],
                    [w * 0.8 - shift * w, h * 0.2],
                    [w * 0.2 + shift * w, h * 0.8],
                    [w * 0.8 + shift * w, h * 0.8],
                ],
                dtype=np.float32,
            )

            M = cv2.getPerspectiveTransform(pts1, pts2)
            image = cv2.warpPerspective(image, M, (w, h))

        # Apply rotation for roll (simple rotation)
        if abs(pose.roll) > 1:
            M = cv2.getRotationMatrix2D(center, -pose.roll, 1.0)
            image = cv2.warpAffine(image, M, (w, h))

        # Apply vertical scaling for pitch
        if abs(pose.pitch) > 1:
            scale_factor = 1.0 - (abs(pose.pitch) * 0.005)
            new_h = int(h * scale_factor)
            resized = cv2.resize(image, (w, new_h))

            # Pad or crop to original size
            if new_h < h:
                pad_top = (h - new_h) // 2
                pad_bottom = h - new_h - pad_top
                image = cv2.copyMakeBorder(
                    resized, pad_top, pad_bottom, 0, 0, cv2.BORDER_REPLICATE
                )
            else:
                crop_y = (new_h - h) // 2
                image = resized[crop_y : crop_y + h, :]

        return image

    def apply_expression(
        self, image: np.ndarray, expression: FacialExpression
    ) -> np.ndarray:
        """
        Apply facial expressions using image manipulation
        """
        h, w = image.shape[:2]

        # Mouth region (bottom third of face)
        mouth_region = slice(int(h * 0.65), int(h * 0.85))
        mouth_x = slice(int(w * 0.35), int(w * 0.65))

        # Apply mouth opening (vertical stretch)
        if expression.mouth_open > 0.1:
            mouth = image[mouth_region, mouth_x].copy()
            stretch = 1.0 + (expression.mouth_open * 0.3)
            new_h = int(mouth.shape[0] * stretch)
            stretched = cv2.resize(mouth, (mouth.shape[1], new_h))

            # Replace region
            y_start = int(h * 0.65)
            y_end = min(y_start + new_h, h)
            image[y_start:y_end, mouth_x] = stretched[: y_end - y_start]

        # Apply smile (subtle curve at mouth corners)
        if expression.smile > 0.1:
            # Brighten mouth corners
            corner_left = slice(int(w * 0.3), int(w * 0.4))
            corner_right = slice(int(w * 0.6), int(w * 0.7))
            brightness = int(expression.smile * 20)

            image[mouth_region, corner_left] = np.clip(
                image[mouth_region, corner_left].astype(int) + brightness, 0, 255
            ).astype(np.uint8)
            image[mouth_region, corner_right] = np.clip(
                image[mouth_region, corner_right].astype(int) + brightness, 0, 255
            ).astype(np.uint8)

        # Apply eyebrow raise (shift eyebrow region up)
        if expression.eyebrow_raise > 0.1:
            eyebrow_region = slice(int(h * 0.25), int(h * 0.35))
            shift = int(expression.eyebrow_raise * 10)

            # Shift region upward
            shifted = image[eyebrow_region, :].copy()
            new_region = slice(max(0, int(h * 0.25) - shift), int(h * 0.35) - shift)
            if new_region.stop > 0:
                image[new_region, :] = shifted

        return image

    def generate_frame(
        self, pose: HeadPose, expression: FacialExpression
    ) -> np.ndarray:
        """
        Generate a single animated frame with head pose and expression
        """
        frame = self.base_image.copy()

        # Apply transformations
        frame = self.apply_head_pose(frame, pose)
        frame = self.apply_expression(frame, expression)

        return frame

    def generate_talking_animation(
        self, audio_path: Path, output_path: Path, fps: int = 25
    ) -> Path:
        """
        Generate talking animation synchronized to audio
        """
        import librosa

        logger.info("🎬 Generating talking animation...")
        logger.info(f"   Audio: {audio_path}")

        # Load audio and analyze
        y, sr = librosa.load(str(audio_path))
        duration = librosa.get_duration(y=y, sr=sr)

        # Extract audio features for mouth movement
        rms = librosa.feature.rms(y=y)[0]
        rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr)

        # Generate frames
        num_frames = int(duration * fps)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (self.width, self.height))

        for frame_idx in range(num_frames):
            time = frame_idx / fps

            # Natural head movement (subtle sway)
            yaw = 5 * math.sin(time * 0.5)  # Slow left-right
            pitch = 3 * math.sin(time * 0.7)  # Slow up-down
            roll = 2 * math.sin(time * 0.3)  # Subtle tilt

            # Mouth movement from audio
            rms_idx = min(int(time * len(rms) / duration), len(rms) - 1)
            mouth_open = min(rms[rms_idx] * 3, 1.0)  # Scale RMS to 0-1

            # Create pose and expression
            pose = HeadPose(yaw=yaw, pitch=pitch, roll=roll)
            expression = FacialExpression(
                mouth_open=mouth_open,
                smile=0.3,  # Slight smile
                eyebrow_raise=0.0,
                eye_blink=(
                    1.0 if (frame_idx % 120) < 3 else 0.0
                ),  # Blink every 4.8 seconds
            )

            # Generate and write frame
            frame = self.generate_frame(pose, expression)
            out.write(frame)

            if frame_idx % 25 == 0:
                logger.info(f"   Generated {frame_idx}/{num_frames} frames...")

        out.release()
        logger.info(f"✅ Animation saved: {output_path}")

        return output_path

    def combine_with_audio(
        self, video_path: Path, audio_path: Path, output_path: Path
    ) -> Path:
        """
        Combine video with audio using ffmpeg
        """
        import subprocess

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-strict",
            "experimental",
            str(output_path),
        ]

        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"🎵 Audio combined: {output_path}")

        return output_path


async def main():
    """Test the animated avatar"""
    import sys

    sys.path.insert(0, str(Path(__file__).parent))
    from speech import SpeechService

    # Generate test speech
    speech = SpeechService(config={})
    audio_bytes = speech.text_to_speech(
        "Hey Everett, I'm BROCKSTON. Now I can move my head, express emotions, and talk naturally. This is all custom code - no external models needed.",
        voice_id="Matthew",
    )

    audio_file = Path("brockston_animated_test.mp3")
    with open(audio_file, "wb") as f:
        f.write(audio_bytes)

    # Create animated avatar - use the REAL BROCKSTON photo
    avatar = BrockstonAnimatedAvatar(
        base_image_path=Path("static/avatar_assets/BROCKSTON.jpeg")
    )

    # Generate talking animation
    video_no_audio = Path("brockston_animated_temp.mp4")
    avatar.generate_talking_animation(audio_file, video_no_audio)

    # Combine with audio
    final_video = Path("brockston_animated.mp4")
    avatar.combine_with_audio(video_no_audio, audio_file, final_video)

    print("\n🎉 BROCKSTON ANIMATED VIDEO READY!")
    print(f"📹 Video: {final_video}")
    print(f"🎵 Audio: {audio_file}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
