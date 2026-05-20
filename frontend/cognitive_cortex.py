"""
BROCKSTON Cognitive Cortex - Full Speech-to-Speech Integration
=============================================================
This module connects all advanced capabilities:
- Enhanced speech recognition (HEARING)
- Natural language understanding (THINKING)
- Voice synthesis (SPEAKING)
- Self-learning and reasoning (INTELLIGENCE)
- Code generation and repair (PROBLEM SOLVING)

This is the BRAIN that makes BROCKSTON truly intelligent.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add static folder to path for advanced modules
static_path = Path(__file__).parent.parent / "static"
sys.path.insert(0, str(static_path))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CognitiveCortex:
    """
    The central intelligence system that coordinates:
    - Speech recognition (hearing)
    - Natural language understanding (comprehension)
    - Reasoning and intent detection (thinking)
    - Knowledge retrieval (memory)
    - Voice synthesis (speaking)
    - Code generation and repair (problem solving)
    - Self-learning (evolution)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.components: Dict[str, Any] = {}
        self.conversation_history: List[Dict[str, Any]] = []
        self.is_initialized = False

        logger.info("🧠 Initializing BROCKSTON Cognitive Cortex...")
        self._initialize_components()

    def _initialize_components(self):
        """Load all cognitive modules"""

        # 1. SPEECH RECOGNITION (HEARING)
        try:
            from enhanced_speech_recognition import EnhancedSpeechRecognition

            self.components["speech_recognition"] = EnhancedSpeechRecognition()
            logger.info("✓ Speech Recognition (HEARING) loaded")
        except Exception as e:
            logger.warning(f"⚠ Speech Recognition not available: {e}")

        # 2. CONVERSATION ENGINE (UNDERSTANDING)
        try:
            from conversation_engine import ConversationEngine

            self.components["conversation"] = ConversationEngine()
            logger.info("✓ Conversation Engine loaded")
        except Exception as e:
            logger.warning(f"⚠ Conversation Engine not available: {e}")

        # 3. NATURAL LANGUAGE UNDERSTANDING
        try:
            from nlu_core import NLUCore

            self.components["nlu"] = NLUCore()
            logger.info("✓ Natural Language Understanding loaded")
        except (ImportError, ModuleNotFoundError) as e:
            logger.warning(f"⚠ NLU not available: {e}")
        except Exception as e:
            logger.warning(f"⚠ NLU initialization failed: {e}")

        # 4. INTENT ENGINE (WHAT USER WANTS)
        try:
            self.components["intent"] = IntentEngine()
            logger.info("✓ Intent Engine loaded")
        except Exception as e:
            logger.warning(f"⚠ Intent Engine not available: {e}")

        # 5. REASONING ENGINE (LOGICAL THINKING)
        try:
            from reasoning_engine import ReasoningEngine

            self.components["reasoning"] = ReasoningEngine()
            logger.info("✓ Reasoning Engine loaded")
        except Exception as e:
            logger.warning(f"⚠ Reasoning Engine not available: {e}")

        # 6. KNOWLEDGE ENGINE (MEMORY & LEARNING)
        try:
            from knowledge_engine import KnowledgeEngine

            self.components["knowledge"] = KnowledgeEngine()
            logger.info("✓ Knowledge Engine loaded")
        except Exception as e:
            logger.warning(f"⚠ Knowledge Engine not available: {e}")

        # 7. VOICE SYNTHESIS (SPEAKING) - Use existing speech module
        try:
            from speech import SpeechService

            self.components["voice"] = SpeechService(self.config.get("speech", {}))
            logger.info("✓ Voice Synthesis (SPEAKING) loaded")
        except Exception as e:
            logger.warning(f"⚠ Voice Synthesis not available: {e}")

        # 8. CODE GENERATOR (PROBLEM SOLVING)
        try:
            from code_generator import AdvancedCodeGenerator

            self.components["code_generator"] = AdvancedCodeGenerator()
            logger.info("✓ Code Generator loaded")
        except Exception as e:
            logger.warning(f"⚠ Code Generator not available: {e}")

        # 9. AUTO REPAIR (SELF-FIXING)
        try:
            from auto_repair import AutoRepair

            self.components["auto_repair"] = AutoRepair()  # No config needed
            logger.info("✓ Auto Repair loaded")
        except Exception as e:
            logger.warning(f"⚠ Auto Repair not available: {e}")

        # 10. EMOTION DETECTION (EMPATHY)
        try:
            from crisis_emotion import analyze_emotion

            self.components["emotion"] = {"analyze": analyze_emotion}
            logger.info("✓ Emotion Detection loaded")
        except Exception as e:
            logger.warning(f"⚠ Emotion Detection not available: {e}")

        self.is_initialized = True
        logger.info(
            f"🧠 Cognitive Cortex initialized with {len(self.components)} components"
        )

    async def process_speech_input(
        self, audio_data: bytes, sample_rate: int = 16000
    ) -> Dict[str, Any]:
        """
        Process speech input and generate intelligent response

        Args:
            audio_data: Raw audio bytes
            sample_rate: Audio sample rate

        Returns:
            {
                'transcript': str,          # What user said
                'intent': str,             # What user wants
                'response_text': str,      # BROCKSTON's reply
                'response_audio': bytes,   # Voice audio
                'emotion': str,            # Detected emotion
                'confidence': float        # How sure we are
            }
        """
        result = {
            "transcript": "",
            "intent": "unknown",
            "response_text": "",
            "response_audio": None,
            "emotion": "neutral",
            "confidence": 0.0,
        }

        try:
            # STEP 1: HEAR (Speech to Text)
            if "speech_recognition" in self.components:
                speech_result = self.components[
                    "speech_recognition"
                ].process_audio_data(audio_data, sample_rate)
                result["transcript"] = speech_result.get("text", "")
                result["confidence"] = speech_result.get("confidence", 0.0)
                logger.info(f"👂 Heard: {result['transcript']}")

            if not result["transcript"]:
                result["response_text"] = "I didn't catch that. Could you repeat?"
                result["response_audio"] = await self._synthesize_speech(
                    result["response_text"]
                )
                return result

            # STEP 2: UNDERSTAND (Intent Detection)
            if "intent" in self.components:
                intent_result = self.components["intent"].detect_intent(
                    result["transcript"]
                )
                result["intent"] = intent_result.get("intent", "unknown")
                logger.info(f"🎯 Intent: {result['intent']}")

            # STEP 3: DETECT EMOTION (Empathy)
            if "emotion" in self.components:
                emotion_result = self.components["emotion"].detect_emotion(
                    result["transcript"]
                )
                result["emotion"] = emotion_result.get("emotion", "neutral")
                logger.info(f"😊 Emotion: {result['emotion']}")

            # STEP 4: THINK (Generate Response)
            result["response_text"] = await self._generate_response(
                result["transcript"], result["intent"], result["emotion"]
            )
            logger.info(f"💭 Response: {result['response_text']}")

            # STEP 5: SPEAK (Text to Speech)
            result["response_audio"] = await self._synthesize_speech(
                result["response_text"], emotion=result["emotion"]
            )

            # STEP 6: LEARN (Store conversation for improvement)
            self._store_conversation(result)

            return result

        except Exception as e:
            logger.error(f"Error processing speech: {e}")
            result["response_text"] = (
                "I encountered an error processing that. Let me try again."
            )
            result["response_audio"] = await self._synthesize_speech(
                result["response_text"]
            )
            return result

    async def _generate_response(
        self, user_input: str, intent: str, emotion: str
    ) -> str:
        """
        Generate intelligent response using all cognitive capabilities
        """
        try:
            # Use conversation engine if available
            if "conversation" in self.components:
                response = self.components["conversation"].generate_response(
                    user_input,
                    intent=intent,
                    emotion=emotion,
                    history=self.conversation_history[-5:],  # Last 5 exchanges
                )
                return response

            # Use reasoning engine for complex queries
            if "reasoning" in self.components and intent in [
                "question",
                "problem",
                "code",
            ]:
                response = self.components["reasoning"].reason(
                    user_input, context={"intent": intent, "emotion": emotion}
                )
                return response

            # Fallback to simple response
            return self._fallback_response(user_input, intent, emotion)

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I'm having trouble formulating a response. Could you rephrase that?"

    def _fallback_response(self, user_input: str, intent: str, emotion: str) -> str:
        """Simple fallback responses when advanced modules unavailable"""

        user_lower = user_input.lower()

        # Greetings
        if any(word in user_lower for word in ["hello", "hi", "hey", "greetings"]):
            return "Hello! I'm BROCKSTON, your AI assistant. How can I help you today?"

        # Capabilities question
        if any(
            word in user_lower for word in ["what can you do", "capabilities", "help"]
        ):
            return """I'm BROCKSTON, a PhD-level AI research system. I can:
- Listen and understand natural speech
- Reason about complex problems
- Generate and repair code
- Learn from our conversations
- Speak naturally with emotion
- Detect your emotional state
- Access and build knowledge

What would you like me to help with?"""

        # Code-related
        if intent == "code" or any(
            word in user_lower for word in ["code", "program", "fix", "debug"]
        ):
            return "I can help with code! Please describe what you need - whether it's writing new code, fixing bugs, or explaining existing code."

        # Questions
        if intent == "question" or "?" in user_input:
            return f"That's an interesting question about {user_input[:50]}... Let me think about that and provide you with a detailed answer."

        # Default
        return f"I understand you said: {user_input}. I'm processing that with my cognitive systems. Could you provide more details?"

    async def _synthesize_speech(
        self, text: str, emotion: str = "neutral"
    ) -> Optional[bytes]:
        """Convert text to speech audio"""
        try:
            if "voice" in self.components:
                # Map emotions to voice moods
                mood_map = {
                    "happy": "excited",
                    "sad": "calm",
                    "angry": "serious",
                    "neutral": "confident",
                }
                mood = mood_map.get(emotion, "confident")

                audio_bytes = self.components["voice"].text_to_speech(
                    text, voice="Matthew", mood=mood  # Can be made configurable
                )
                return audio_bytes
            return None
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            return None

    def _store_conversation(self, result: Dict[str, Any]):
        """Store conversation for learning and context"""
        self.conversation_history.append(
            {
                "user": result["transcript"],
                "assistant": result["response_text"],
                "intent": result["intent"],
                "emotion": result["emotion"],
                "confidence": result["confidence"],
            }
        )

        # Keep only last 100 exchanges
        if len(self.conversation_history) > 100:
            self.conversation_history = self.conversation_history[-100:]

    async def process_text_input(self, text: str) -> Dict[str, Any]:
        """
        Process text input (like chat) and generate response with voice

        Args:
            text: User's text input

        Returns:
            Same structure as process_speech_input
        """
        result = {
            "transcript": text,
            "intent": "unknown",
            "response_text": "",
            "response_audio": None,
            "emotion": "neutral",
            "confidence": 1.0,
        }

        try:
            # Detect intent
            if "intent" in self.components:
                intent_result = self.components["intent"].detect_intent(text)
                result["intent"] = intent_result.get("intent", "unknown")

            # Detect emotion
            if "emotion" in self.components:
                emotion_result = self.components["emotion"].detect_emotion(text)
                result["emotion"] = emotion_result.get("emotion", "neutral")

            # Generate response
            result["response_text"] = await self._generate_response(
                text, result["intent"], result["emotion"]
            )

            # Synthesize speech
            result["response_audio"] = await self._synthesize_speech(
                result["response_text"], emotion=result["emotion"]
            )

            # Learn
            self._store_conversation(result)

            return result

        except Exception as e:
            logger.error(f"Error processing text: {e}")
            result["response_text"] = "I encountered an error. Please try again."
            return result

    def get_status(self) -> Dict[str, Any]:
        """Get status of all cognitive components"""
        return {
            "initialized": self.is_initialized,
            "components": {name: "loaded" for name in self.components.keys()},
            "conversation_count": len(self.conversation_history),
            "capabilities": {
                "hearing": "speech_recognition" in self.components,
                "understanding": "nlu" in self.components
                or "conversation" in self.components,
                "reasoning": "reasoning" in self.components,
                "knowledge": "knowledge" in self.components,
                "speaking": "voice" in self.components,
                "emotion": "emotion" in self.components,
                "code": "code_generator" in self.components,
                "self_repair": "auto_repair" in self.components,
            },
        }


# Singleton instance
_cortex_instance = None


def get_cognitive_cortex(config: Optional[Dict[str, Any]] = None) -> CognitiveCortex:
    """Get or create the cognitive cortex singleton"""
    global _cortex_instance
    if _cortex_instance is None:
        _cortex_instance = CognitiveCortex(config)
    return _cortex_instance
