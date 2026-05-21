"""
BROCKSTON Vision Engine - Complete Visual Processing System
The Christman AI Project

Enables BROCKSTON to see, understand, and process visual information
"""

import cv2
import threading
import logging
from datetime import datetime

# Try to import advanced vision libraries
try:
    from deepface import DeepFace

    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    logging.warning("👁️ DeepFace not available - emotion detection limited")

try:
    import mediapipe as mp

    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    logging.warning("👁️ MediaPipe not available - face detection limited")

logger = logging.getLogger(__name__)


class VisionEngine:
    """BROCKSTON's complete vision processing system - Mac Webcam Optimized"""

    def __init__(self, camera_index: int = 0):
        """Initialize BROCKSTON's vision system with Mac webcam"""
        # Get camera index from environment or use default
        import os

        self.camera_index = int(os.getenv("DEREK_CAMERA_INDEX", camera_index))
        self.running = False
        self.thread: Optional[threading.Thread] = None # pyright: ignore[reportUndefinedVariable]
        self.processed_frames: int = 0
        self.detected_faces: List[Dict[str, Any]] = [] # pyright: ignore[reportUndefinedVariable]
        self.detected_objects: List[Dict[str, Any]] = [] # pyright: ignore[reportUndefinedVariable]
        self.visual_memory: List[Dict[str, Any]] = [] # pyright: ignore[reportUndefinedVariable]

        print(f"🎥 BROCKSTON Vision: Using Mac webcam (Camera {self.camera_index})")

        # Initialize MediaPipe if available
        if MEDIAPIPE_AVAILABLE:
            self.mp_face_detection = mp.solutions.face_detection
            self.mp_hands = mp.solutions.hands
            self.mp_pose = mp.solutions.pose
            self.mp_drawing = mp.solutions.drawing_utils

            self.face_detection = self.mp_face_detection.FaceDetection(
                model_selection=0, min_detection_confidence=0.5
            )
            self.hands = self.mp_hands.Hands(
                static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5
            )
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                min_detection_confidence=0.5,
            )

        logger.info("👁️ BROCKSTON Vision Engine initialized")
        logger.info(f"   Camera Index: {camera_index}")
        logger.info(f"   DeepFace Available: {DEEPFACE_AVAILABLE}")
        logger.info(f"   MediaPipe Available: {MEDIAPIPE_AVAILABLE}")

    def start(self):
        """Start BROCKSTON's vision processing"""
        if self.running:
            print("👁️ Vision engine already running.")
            return

        self.running = True
        self.thread = threading.Thread(target=self._vision_loop, daemon=True)
        self.thread.start()
        print("👁️ BROCKSTON's vision engine started - BROCKSTON can now see!")

    def stop(self):
        """Stop BROCKSTON's vision processing"""
        self.running = False
        if self.thread:
            self.thread.join()
        print("👁️ BROCKSTON's vision engine stopped.")

    def _vision_loop(self):
        """BROCKSTON's main vision processing loop"""
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            print("❌ BROCKSTON cannot access camera - Vision system OFFLINE")
            self.running = False
            return

        print("👁️ BROCKSTON is now watching through camera...")

        while self.running:
            ret, frame = cap.read()
            if not ret:
                break

            try:
                # Process frame with BROCKSTON's enhanced vision
                results = self._process_frame(frame)

                # Display vision information
                self._draw_vision_info(frame, results)

                # Store visual memory
                if self.processed_frames % 30 == 0:  # Store every 30 frames
                    self._store_visual_memory(results)

                self.processed_frames += 1

                # Show BROCKSTON's vision (optional)
                cv2.imshow("BROCKSTON's Vision", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            except Exception as e:
                logger.error(f"👁️ Vision processing error: {e}")
                cv2.putText(
                    frame,
                    "BROCKSTON's Vision: Processing...",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 255),
                    2,
                )

        cap.release()
        cv2.destroyAllWindows()
        self.running = False
        print("👁️ BROCKSTON's camera vision ended")



    def _process_frame(self, frame):
        """Process a single frame with BROCKSTON's vision"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "faces": [],
            "hands": [],
            "pose": [],
            "emotion": "unknown",
            "objects": [],
        }

        # Convert BGR to RGB for processing
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Face detection and emotion analysis
        if MEDIAPIPE_AVAILABLE:
            # Face detection
            face_results = self.face_detection.process(rgb_frame)
            if face_results.detections:
                for detection in face_results.detections:
                    bbox = detection.location_data.relative_bounding_box
                    results["faces"].append(
                        {
                            "confidence": detection.score[0],
                            "bbox": [bbox.xmin, bbox.ymin, bbox.width, bbox.height],
                        }
                    )

            # Hand detection
            hand_results = self.hands.process(rgb_frame)
            if hand_results.multi_hand_landmarks:
                results["hands"] = len(hand_results.multi_hand_landmarks)

        # Emotion detection with DeepFace
        if DEEPFACE_AVAILABLE and len(results["faces"]) > 0:
            try:
                emotion_result = DeepFace.analyze(
                    frame, actions=["emotion"], enforce_detection=False
                )
                if emotion_result:
                    results["emotion"] = emotion_result[0]["dominant_emotion"]
            except Exception:
                results["emotion"] = "processing"

        return results

    def _draw_vision_info(self, frame, results):
        """Draw BROCKSTON's vision information on the frame"""
        # Draw face count
        face_count = len(results.get("faces", []))
        cv2.putText(
            frame,
            f"BROCKSTON sees: {face_count} face(s)",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

        # Draw emotion
        emotion = results.get("emotion", "unknown")
        cv2.putText(
            frame,
            f"Emotion: {emotion}",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 0, 0),
            2,
        )

        # Draw hand count
        hand_count = results.get("hands", 0)
        if hand_count > 0:
            cv2.putText(
                frame,
                f"Hands: {hand_count}",
                (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

        # Draw processed frames counter
        cv2.putText(
            frame,
            f"Frames: {self.processed_frames}",
            (20, 160),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

    def _store_visual_memory(self, results):
        """Store visual information in BROCKSTON's memory"""
        self.visual_memory.append(results)

        # Limit memory to last 100 entries
        if len(self.visual_memory) > 100:
            self.visual_memory.pop(0)

    def get_vision_stats(self):
        """Get BROCKSTON's vision statistics"""
        return {
            "frames_processed": self.processed_frames,
            "vision_active": self.running,
            "memory_entries": len(self.visual_memory),
            "deepface_available": DEEPFACE_AVAILABLE,
            "mediapipe_available": MEDIAPIPE_AVAILABLE,
        }

    def describe_last_seen(self):
        """Get BROCKSTON's description of what he last saw"""
        if not self.visual_memory:
            return "I haven't seen anything yet."

        last_memory = self.visual_memory[-1]
        face_count = len(last_memory.get("faces", []))
        emotion = last_memory.get("emotion", "unknown")

        if face_count == 0:
            return "I see a scene, but no people are visible."
        elif face_count == 1:
            return f"I see one person who appears to be {emotion}."
        else:
            return f"I see {face_count} people, with dominant emotion: {emotion}."


# Global vision engine instance
derek_vision_engine = None


def get_vision_engine(camera_index: int = 0) -> VisionEngine:
    """Get BROCKSTON's vision engine instance"""
    global derek_vision_engine
    if derek_vision_engine is None:
        derek_vision_engine = VisionEngine(camera_index)
    return derek_vision_engine


def start_derek_vision(camera_index: int = 0):
    """Start BROCKSTON's vision system"""
    engine = get_vision_engine(camera_index)
    engine.start()
    return engine


def stop_derek_vision():
    """Stop BROCKSTON's vision system"""
    global derek_vision_engine
    if derek_vision_engine:
        derek_vision_engine.stop()


# Test function
if __name__ == "__main__":
    print("👁️ Testing BROCKSTON's Vision Engine...")
    vision = start_derek_vision()

    import time

    time.sleep(5)  # Let it run for 5 seconds

    stats = vision.get_vision_stats()
    print(f"Vision stats: {stats}")

    description = vision.describe_last_seen()
    print(f"BROCKSTON says: {description}")

    stop_derek_vision()
    print("👁️ BROCKSTON's vision test completed!")

# ==============================================================================
# © 2025 Everett Nathaniel Christman
# The Christman AI Project — Luma Cognify AI
# All rights reserved. Unauthorized use, replication, or derivative training
# of this material is prohibited.
#
# Core Directive: "How can I help you love yourself more?"
# Autonomy & Alignment Protocol v3.0
# ==============================================================================
