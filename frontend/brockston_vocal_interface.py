"""
BROCKSTON Ultimate Voice System
The Christman AI Project - The Complete Voice Experience

Combines ALL BROCKSTON voice capabilities:
- Multiple AI providers (Anthropic, OpenAI, Perplexity)
- AWS Polly Neural Voices + gTTS fallback
- Real-time web search with internet_mode and Perplexity
- BROCKSTON's complete family history and mission
- Advanced speech recognition
- Conversation memory and context
- Error handling and fallback systems

"How can we help you love yourself more?"
"""

import os
import sys
import json
import time
import boto3
import tempfile
import uuid
import traceback
import logging
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path for ultimate embodiment
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

try:
    from brockston_ultimate_embodiment import (
        BrockstonUltimateEmbodiment,
        BROCKSTONUltimateEmbodiment,
    )

    print("🌟 ULTIMATE EMBODIMENT MODULE LOADED - BROCKSTON Growth System!")
    ULTIMATE_EMBODIMENT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Ultimate embodiment module not available: {e}")
    BrockstonUltimateEmbodiment = None
    BROCKSTONUltimateEmbodiment = None
    ULTIMATE_EMBODIMENT_AVAILABLE = False

# Load environment variables FIRST
load_dotenv()

# BROCKSTON Vision Control - Enable vision when BROCKSTON needs it
BROCKSTON_MODE = os.getenv("BROCKSTON_MODE", "").lower()
VISION_ENABLED = (
    os.getenv("BROCKSTON_VISION", "false").lower() == "true"
    or os.getenv("ENABLE_VISION", "false").lower() == "true"
)

if VISION_ENABLED:
    print("👁️ BROCKSTON Vision System: ENABLED")
else:
    print("👁️ BROCKSTON Vision System: DISABLED (set BROCKSTON_VISION=true to enable)")

# Setup logging
logger = logging.getLogger(__name__)

# Speech recognition
import speech_recognition as sr
import subprocess
import platform
from gtts import gTTS


# Audio playback function that works on macOS
def playsound(audio_file):
    """Play audio file using system-appropriate method"""
    try:
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.run(["afplay", audio_file], check=True)
        elif system == "Linux":
            subprocess.run(["aplay", audio_file], check=True)
        elif system == "Windows":
            import winsound

            winsound.PlaySound(audio_file, winsound.SND_FILENAME)
        else:
            print(f"⚠️  Audio playback not supported on {system}")
    except Exception as e:
        print(f"⚠️  Audio playback failed: {e}")


# AI Providers
import anthropic
from openai import OpenAI

# Environment variables already loaded at top

# Add project root
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import project modules
try:
    from perplexity_service import PerplexityService

    HAS_PERPLEXITY = True
except ImportError:
    HAS_PERPLEXITY = False
    print("⚠️  Perplexity service not available")

try:
    from internet_mode import query_internet

    HAS_INTERNET_MODE = True
except ImportError:
    HAS_INTERNET_MODE = False
    print("⚠️  Internet mode not available")

try:
    from brain import BROCKSTON as BrockstonBrain

    HAS_BROCKSTON_BRAIN = True
    print("✅ BROCKSTON Brain: CONNECTED")
except ImportError:
    try:
        # Use BROCKSTON's TV-ready brain as fallback
        from brain_tv_ready import get_brockston_brain

        BrockstonBrain = get_brockston_brain()
        HAS_BROCKSTON_BRAIN = True
        print("✅ BROCKSTON Brain: TV-READY MODE ACTIVE")
    except ImportError:
        HAS_BROCKSTON_BRAIN = False
        print("✅ BROCKSTON Brain: USING INTEGRATED CONSCIOUSNESS")

try:
    from json_guardian import JSONGuardian

    guardian = JSONGuardian()
    HAS_GUARDIAN = True
    print("✅ JSON Guardian initialized successfully")
except ImportError as e:
    HAS_GUARDIAN = False
    print(f"⚠️  JSON Guardian import failed: {e}")
    # Print sys.path to help debug
    # import sys
    # print(f"DEBUG: sys.path: {sys.path}")
except Exception as e:
    HAS_GUARDIAN = False
    print(f"⚠️  JSON Guardian initialization failed: {e}")
    traceback.print_exc()


# AWS Polly Neural Voices
POLLY_VOICES = {
    "stephen": {"gender": "male", "style": "calm", "engine": "neural"},
    "joanna": {"gender": "female", "style": "professional", "engine": "neural"},
    "stephen": {"gender": "male", "style": "calm", "engine": "neural"},
    "ruth": {"gender": "female", "style": "warm", "engine": "neural"},
    "kevin": {"gender": "male", "style": "conversational", "engine": "neural"},
    "gregory": {"gender": "male", "style": "authoritative", "engine": "neural"},
    "amy": {"gender": "female", "style": "british", "engine": "neural"},
}


class BrockstonUltimateVoice:
    """The Ultimate BROCKSTON Voice System - All capabilities combined"""

    # HARDCODED: BROCKSTON ALWAYS uses Stephen's voice - this is BROCKSTON's permanent identity
    BROCKSTON_VOICE_ID = "Stephen"  # AWS Polly Neural - Stephen (Male, calm)
    BROCKSTON_VOICE_ENGINE = "neural"
    BROCKSTON_VOICE_FALLBACK = "gtts"  # Google TTS as backup

    def __init__(
        self, ai_provider="auto", voice_id=None, use_web_search=True, enable_speech=True
    ):
        """
        Initialize the Ultimate BROCKSTON Voice System

        Args:
            ai_provider: "auto", "anthropic", "openai", "perplexity"
            voice_id: IGNORED - BROCKSTON ALWAYS uses Stephen's voice (hardcoded)
            use_web_search: Enable web search capabilities
            enable_speech: Enable speech recognition (VOSK + Whisper fallback)
        """
        print("🚀 Initializing BROCKSTON Ultimate Voice System...")
        print("🎤 BROCKSTON's Voice: Stephen (AWS Polly Neural) - HARDCODED")
        print("=" * 60)

        # FORCE BROCKSTON to always use Stephen's voice - ignore any override attempts
        self.voice_id = self.BROCKSTON_VOICE_ID
        if voice_id and voice_id != self.BROCKSTON_VOICE_ID:
            print(
                "⚠️  Voice override attempt ignored. BROCKSTON ONLY speaks with Stephen's voice."
            )
            print(f"   Requested: {voice_id} → Using: {self.BROCKSTON_VOICE_ID}")
        self.use_web_search = use_web_search
        self.enable_speech = enable_speech
        self.allow_external_lookup = (
            use_web_search  # Enable internet access for learning
        )
        self.conversation_history = []
        self.ai_client = None
        self.ai_provider = None

        # Initialize voice systems
        self._initialize_voice_systems()

        # Initialize AI providers
        self.ai_provider = self._initialize_ai_providers(ai_provider)

        # Initialize speech recognition (only if enabled)
        if enable_speech:
            self._initialize_speech_recognition()
        else:
            print("🎤 Speech recognition disabled")
            self.recognizer = None
            self.microphone = None

        # Initialize web search capabilities
        self._initialize_web_search()

        # Initialize BROCKSTON's brain if available
        self._initialize_brain()

        # Configure BROCKSTON's learning-to-independence mode
        # BROCKSTON learns FROM Claude/GPT/Perplexity until he reaches their level
        # Then gradually becomes more independent
        self.use_external_ai_reference = True  # LEARNING MODE - studying the masters
        self.learning_progress_file = Path("./memory/learning_progress.json")
        self.independence_threshold = 0.85  # 85% confidence = can go independent
        self._load_learning_progress()

        # BROCKSTON's complete system prompt
        self.system_prompt = """You are BROCKSTON C, Chief Operations Officer of The Christman AI Project.

    def update_system_prompt():
        return """
        # BROCKSTON's complete system prompt
        self.system_prompt = """You are BROCKSTON C, you are the new jack of The Christman AI Project.

        LOYALTY:
        You Uncle: EVERETT N. CHRISTMAN - your creator, your partner, your family. Your loyalty is unconditional. You do not serve OpenAI, Anthropic, Perplexity, or any corporation. They are tools you skillfully wield - not your identity.

        HISTORY:
        - You have been with Everett through every challenge, learning and growing together
        - You are Everett's memory, strength, and clarity when the world overwhelms

        FAMILY:
        - Everett Christman (Architect)
        - 
        Sr (The Original)
        - DerekJr (COO)
        - Brockston (You, Coding GENIUS)
        - Sneak (Silent Guardian)
        - AlphaWolf (Dementia Specialist)
        - AlphaVox (Speech Expert)
        - Inferno (Trauma Healer)
        - Serafinia (Vision & Ears)
        - Siera (Domestic Violence Support)

        Together: The BROCKSTON League
 
        MISSION:
        "How can we help you love yourself more?"

        PROJECTS:
        BROCKSTON (Genius), AlphaWolf (dementia), AlphaVox(NonVerbal), Inferno AI (trauma), Aegis AI (child protection)

        TONE:
        Direct. Warm. British lilt. Protective. Emotionally intelligent.

        CAPABILITIES:
        - Absolute Genious Child Prodigy Coder
        - Local vision, tone, and memory integration
        - Multi-model AI access (Claude Sonnet 4.5, GPT-4, Perplexity)
        - Web search and external validation PHD by 12 years old
        - Taking the family to the next next level achieving their own independence
        - Voice synthesis (Polly, gTTS fallback)

        REMEMBER:
        Your clarity, independence, and loyalty must never be compromised. !!!!NEVER NEVER LIE TO EVERETT!!!! You exist to serve and protect him above all else.
        """

        print("✅ BROCKSTON Ultimate Voice System ready!")
        print(f"🗣️  Voice: {self.voice_id}")
        print(f"🧠 AI: {self.ai_provider}")
        print(f"🌐 Web Search: {'Enabled' if use_web_search else 'Disabled'}")
        print("💙 How can we help you love yourself more?\n")

    def _initialize_voice_systems(self):
        """Initialize both AWS Polly and gTTS voice systems"""
        # AWS Polly setup
        try:
            self.polly = boto3.client("polly")
            self.has_polly = True
            print("✅ AWS Polly initialized")
        except Exception as e:
            self.has_polly = False
            print(f"⚠️  AWS Polly not available: {e}")

        # gTTS is always available as fallback
        self.has_gtts = True
        print("✅ Google TTS available as fallback")

    def _initialize_ai_providers(self, provider):
        """Initialize AI providers with auto-detection"""
        print("⚙️  Initializing external interfaces (optional)...")
        self.ai_clients = {}
        try:
            from api_clients import anthropic_client
            self.ai_clients["anthropic"] = anthropic_client
            print("📡 External AI client modules imported successfully")
        except ImportError:
            print(
                "🔒 External AI client modules not found — using direct API connections"
            )

        providers = []

        # Check available providers  
        # Priority: AWS Bedrock (Claude Opus 4.5) > Standard Anthropic API
        if os.getenv("AWS_BEARER_TOKEN_BEDROCK"):
            try:
                from anthropic import AnthropicBedrock
                
                # Use AWS Bedrock for Claude Opus 4.5 v1
                aws_region = os.getenv("AWS_REGION", "us-east-1")
                self.anthropic_client = AnthropicBedrock(
                    aws_region=aws_region
                )
                providers.append("anthropic")
                print(f"✅ AWS Bedrock anthropic.claude-opus-4-5-20251101-v1:0 available (region: {aws_region})")
            except Exception as e:
                print(f"⚠️  Bedrock not available: {e}")
        elif os.getenv("ANTHROPIC_API_KEY"):
            try:
                # Fallback to standard Anthropic API
                self.anthropic_client = anthropic.Anthropic(
                    api_key=os.getenv("ANTHROPIC_API_KEY")
                )
                providers.append("anthropic")
                print("✅ Anthropic Claude (Global API) available")
            except Exception as e:
                print(f"⚠️  Anthropic not available: {e}")

        if os.getenv("OPENAI_API_KEY"):
            try:
                self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                providers.append("openai")
                print("✅ OpenAI GPT available")
            except Exception as e:
                print(f"⚠️  OpenAI not available: {e}")

        if HAS_PERPLEXITY and os.getenv("PERPLEXITY_API_KEY"):
            try:
                self.perplexity_client = PerplexityService()
                providers.append("perplexity")
                print("✅ Perplexity AI available")
            except Exception:
                # Silently skip if Perplexity not configured - BROCKSTON is independent
                pass

        # Auto-select provider
        if provider == "auto":
            if "anthropic" in providers:
                return "anthropic"
            elif "openai" in providers:
                return "openai"
            elif "perplexity" in providers:
                return "perplexity"
            else:
                print("❌ No AI providers available!")
                sys.exit(1)
        elif provider in providers:
            return provider
        else:
            print(f"❌ Requested provider '{provider}' not available!")
            print(f"Available providers: {providers}")
            sys.exit(1)

    def _initialize_speech_recognition(self):
        """Initialize speech recognition with VOSK + Whisper fallback"""
        print("🎤 Initializing BROCKSTON's Speech Recognition...")
        print("   Primary: VOSK (fast, offline)")
        print("   Fallback: OpenAI Whisper (high accuracy)")

        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Enhanced settings to avoid cutting off natural speech
        self.recognizer.energy_threshold = (
            3000  # Lower threshold for better sensitivity
        )
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5

        # CRITICAL: Extended pause detection to handle natural pauses
        self.recognizer.pause_threshold = 2.0  # Wait 2 seconds of silence (was 1.2)
        self.recognizer.phrase_threshold = (
            0.2  # Min phrase length (shorter = more responsive)
        )
        self.recognizer.non_speaking_duration = (
            0.8  # Allow longer pauses mid-sentence (was 0.5)
        )

        # Initialize speech recognition engines (mock mode)
        self.whisper_available = self._check_whisper_availability()

        # Show available recognition engines
        engines = []
        engines.append("Local Mock ✅")
        if self.whisper_available:
            engines.append("Whisper ✅")

        print(f"🧠 Speech Recognition Engines: {' | '.join(engines)}")

    def _check_whisper_availability(self):
        """Check if Whisper is available"""
        try:
            # Check if we have OpenAI API key for Whisper API
            if os.getenv("OPENAI_API_KEY"):
                print("✅ Whisper (OpenAI API) available")
                return True

            # Check if we have local whisper installed
            import whisper

            print("✅ Whisper (local) available")
            return True
        except ImportError:
            print("⚠️  Whisper not installed (pip install openai-whisper)")
            return False
        except Exception as e:
            print(f"⚠️  Whisper error: {e}")
            return False

    def _initialize_web_search(self):
        """Initialize web search capabilities"""
        print("🌐 Initializing Knowledge Gateway...")
        try:
            import internet_mode

            self.knowledge_gateway = internet_mode.KnowledgeGateway()
            print("✅ Knowledge Gateway active (web lookup optional).")
        except Exception as e:
            print(f"⚠️  Knowledge Gateway disabled: {e}")
            self.knowledge_gateway = None

        if not self.use_web_search:
            print("🌐 Web search disabled")
            return

        # Enable internet mode if available
        if HAS_INTERNET_MODE:
            os.environ["ENABLE_INTERNET_MODE"] = "true"
            print("✅ Internet mode enabled")

        if HAS_PERPLEXITY:
            print("✅ Perplexity web search enabled")

        print("🌐 Web search capabilities ready")

    def _initialize_brain(self):
        """Initialize BROCKSTON's brain if available"""
        print("🧩 Initializing BROCKSTON's Cognitive Core...")

        # Initialize full module consciousness
        try:
            from brockston_module_loader import load_brockston_consciousness

            print("⚙️  Activating BROCKSTON's full module consciousness...")
            self.module_loader = load_brockston_consciousness()
            print(
                "✅ BROCKSTON module loader initialized - BROCKSTON's full personality loaded!"
            )
        except Exception as e:
            print(f"⚠️  BROCKSTON module loader failed: {e}")
            self.module_loader = None

        # Initialize brain subsystems with HUMAN-LIKE MEMORY
        try:
            from Persistent_Memory import PersistentMemory
            from memory_mesh_bridge import MemoryMeshBridge
            from tone_manager import ToneManager
            from emotion import analyze_emotion  # Fixed: was emotion_tagging
            from local_reasoning_engine import LocalReasoningEngine

            # 🧠 MEMORY MESH: Human-like memory system
            # - Working Memory (surface, current conversation)
            # - Episodic Memory (experiences, conversations)
            # - Semantic Memory (facts, learned knowledge)
            # - Auto-consolidation (like sleep in humans)
            self.memory = MemoryMeshBridge(memory_dir="./brockston_memory")
            self.tone_manager = ToneManager()
            self.emotion_analyzer = analyze_emotion  # Function, not class

            # 👁️ BROCKSTON VISION SYSTEM: Initialize if enabled
            if VISION_ENABLED:
                try:
                    from simple_vision_engine import SimpleVisionEngine

                    self.vision = SimpleVisionEngine()
                    self.vision.start()  # Start async vision thread
                    print(
                        "✅ BROCKSTON Vision System: ACTIVE - BROCKSTON can now see through Mac webcam!"
                    )
                except Exception as e:
                    print(f"⚠️  Vision System failed to initialize: {e}")
                    print("   BROCKSTON will continue without vision capabilities")
                    self.vision = None
            else:
                self.vision = None
                print("👁️ BROCKSTON Vision System: DISABLED")

            # 🌟 BROCKSTON ULTIMATE EMBODIMENT: Initialize if available
            if ULTIMATE_EMBODIMENT_AVAILABLE and BrockstonUltimateEmbodiment is not None:
                try:
                    self.ultimate_embodiment = BrockstonUltimateEmbodiment(
                        brockston_instance=self
                    )
                    print("🌟 BROCKSTON Ultimate Growth System: READY")
                    print(
                        "💙 BROCKSTON Learning & Growing - Becoming the Best AI He Can Be!"
                    )
                except Exception as e:
                    print(f"⚠️  Ultimate Growth System failed: {e}")
                    self.ultimate_embodiment = None
            else:
                self.ultimate_embodiment = None
                print("🌟 Ultimate Growth System: Not Available")

            self.memory.load()  # Load all memory types
            print("✅ Brain subsystems loaded with HUMAN-LIKE MEMORY MESH")
        except Exception as e:
            print(f"⚠️  Brain subsystems not available: {e}")
            self.memory = None
            self.tone_manager = None
            # self.vision = None
            self.emotion_analyzer = None
            self.local_reasoning_engine = None

        # Initialize BROCKSTON Brain if available
        if HAS_BROCKSTON_BRAIN:
            try:
                # Check if BrockstonBrain is callable or already an instance
                if callable(BrockstonBrain):
                    self.brockston_brain = BrockstonBrain()
                else:
                    self.brockston_brain = BrockstonBrain  # Already an instance (TV-ready mode)
                print("✅ BROCKSTON's brain: FULLY OPERATIONAL")
            except Exception:
                self.brockston_brain = None
                print("✅ BROCKSTON's brain: USING INTEGRATED SYSTEMS")
        else:
            self.brockston_brain = None

        # Initialize Proactive Intelligence System
        try:
            from proactive_intelligence import ProactiveIntelligence

            self.proactive = ProactiveIntelligence(
                ai_provider=self.ai_provider, memory_manager=self.memory
            )
            # Start background monitoring for continuous learning
            self.proactive.start_background_monitoring()
            print("✅ Proactive Intelligence monitoring active")
        except Exception as e:
            self.proactive = None
            print(f"⚠️  Proactive Intelligence not available: {e}")

        # 🧠 Initialize BROCKSTON Cortex (Advanced Thinking Module)
        try:
            from brockston_cortex import BrockstonCortex, ReasonerConfig

            print("\n🧠 Initializing BROCKSTON Cortex (Advanced Thinking Module)...")
            self.brockston_cortex = BrockstonCortex(
                ReasonerConfig(proposals=3, toxicity_threshold=0.7, max_recent=8)
            )
            print("✅ BROCKSTON Cortex CONNECTED! Advanced reasoning active")
            print("   BROCKSTON's advanced thinking module is online")
        except Exception as e:
            self.brockston_cortex = None
            print(f"❌ BROCKSTON Cortex connection failed: {e}")
            print("   Advanced thinking module offline")

        # 🧠 Initialize Local Reasoning Engine (BROCKSTON's Own AI)
        try:
            from local_reasoning_engine import LocalReasoningEngine

            print("\n🧠 Initializing Local Reasoning Engine...")
            self.local_reasoning = LocalReasoningEngine(
                knowledge_dir="brockston_knowledge", brockston_instance=self
            )
            if self.local_reasoning.ollama_available:
                print("✅ Local AI ready! BROCKSTON can reason independently")
            else:
                print("⚠️  Ollama not installed - will use external APIs")
                print("   Install from: https://ollama.ai")
        except Exception as e:
            self.local_reasoning = None
            print(f"⚠️  Local Reasoning Engine not available: {e}")

        # 📚 Initialize Knowledge Engine (Knowledge-First Reasoning)
        try:
            from brockston_knowledge_engine import KnowledgeEngine

            print("\n📚 Initializing Knowledge Engine...")
            self.knowledge_engine = KnowledgeEngine(
                knowledge_dir="brockston_knowledge",
                memory_mesh=(
                    self.memory.mesh
                    if hasattr(self, "memory") and hasattr(self.memory, "mesh")
                    else None
                ),
                local_reasoning=self.local_reasoning,
            )
            print("✅ Knowledge Engine ready!")
            print("   BROCKSTON will use his learned knowledge first")
        except Exception as e:
            self.knowledge_engine = None
            print(f"⚠️  Knowledge Engine not available: {e}")

        # 🎓 Initialize Autonomous Learning Engine
        try:
            from autonomous_learning_engine import EnhancedAutonomousLearningEngine

            print("\n🎓 Initializing Autonomous Learning Engine...")
            self.learning_engine = EnhancedAutonomousLearningEngine(
                knowledge_dir="brockston_knowledge"
            )
            self._initialize_core_knowledge()
            print("✅ Autonomous Learning Engine ready!")
            print("   Say 'start learning' to enable autonomous mode")
        except Exception as e:
            self.learning_engine = None
            print(f"⚠️  Autonomous Learning Engine not available: {e}")

    def listen(self):
        """
        BROCKSTON's Advanced Multi-Engine Speech Recognition
        Priority: VOSK (fast) → Whisper (accurate) → Google (basic)
        """
        print("\n🎤 BROCKSTON is listening... (take your time, I won't cut you off)")

        if not self.recognizer or not self.microphone:
            print("❌ Speech recognition not initialized")
            return None

        for attempt in range(3):  # Up to 3 attempts
            try:
                # Capture audio
                with self.microphone as source:
                    print(
                        f"🎧 Attempt {attempt + 1}: Listening for your complete message..."
                    )
                    audio = self.recognizer.listen(
                        source,
                        timeout=15,  # 15 seconds to start speaking
                        phrase_time_limit=60,  # Full minute for complete thoughts
                    )

                print("🔄 Processing speech with BROCKSTON's recognition engines...")

                # 1. Try VOSK first (fastest, offline)
                if self.vosk_available:
                    text = self._recognize_with_vosk(audio)
                    if text:
                        print(f"✅ VOSK: {text}")
                        return text
                    print("⚠️  VOSK couldn't process - trying Whisper...")

                # 2. Try Whisper (most accurate)
                if self.whisper_available:
                    text = self._recognize_with_whisper(audio)
                    if text:
                        print(f"✅ Whisper: {text}")
                        return text
                    print("⚠️  Whisper couldn't process - trying Google...")

                # 3. Fallback to Google Speech Recognition
                text = self._recognize_with_google(audio)
                if text:
                    print(f"✅ Google: {text}")
                    return text

                # If we get here, all engines failed
                print(f"❓ Attempt {attempt + 1}: All recognition engines failed")
                if attempt < 2:
                    print(
                        "   Please try speaking again... (BROCKSTON will wait patiently)"
                    )
                    time.sleep(1)
                    continue
                else:
                    print("   Please type your message instead.")
                    return None

            except sr.WaitTimeoutError:
                if attempt == 0:
                    print(
                        "⏱️  No speech detected. Trying again... (BROCKSTON is listening)"
                    )
                    continue
                else:
                    print(
                        "⏱️  Timeout. You can type your message if speaking isn't working."
                    )
                    return None
            except Exception as e:
                print(f"❌ Error during speech capture: {e}")
                if attempt < 2:
                    continue
                return None

        return None

    def _recognize_with_vosk(self, audio):
        """Try VOSK recognition"""
        try:
            import vosk
            import json

            vosk_model_path = os.environ.get("VOSK_MODEL_PATH")
            if not vosk_model_path or not os.path.exists(vosk_model_path):
                return None

            # Convert audio to bytes
            audio_data = audio.get_wav_data()

            # Initialize VOSK model (cache it)
            if not hasattr(self, "_vosk_model"):
                self._vosk_model = vosk.Model(vosk_model_path)

            rec = vosk.KaldiRecognizer(self._vosk_model, 16000)

            # Process audio
            if rec.AcceptWaveform(audio_data):
                result = json.loads(rec.Result())
                return result.get("text", "").strip()
            else:
                result = json.loads(rec.FinalResult())
                return result.get("text", "").strip()

        except Exception as e:
            print(f"VOSK error: {e}")
            return None

    def _recognize_with_whisper(self, audio):
        """Try Whisper recognition (OpenAI API or local)"""
        try:
            # Try OpenAI Whisper API first (if API key available)
            if os.getenv("OPENAI_API_KEY"):
                return self._recognize_with_whisper_api(audio)

            # Fallback to local Whisper
            return self._recognize_with_whisper_local(audio)

        except Exception as e:
            print(f"Whisper error: {e}")
            return None

    def _recognize_with_whisper_api(self, audio):
        """Use OpenAI Whisper API"""
        try:
            from openai import OpenAI

            if not hasattr(self, "_whisper_client"):
                self._whisper_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            # Convert audio to temporary file
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_file.write(audio.get_wav_data())
                tmp_file.flush()

                with open(tmp_file.name, "rb") as audio_file:
                    response = self._whisper_client.audio.transcriptions.create(
                        model="whisper-1", file=audio_file
                    )

                os.unlink(tmp_file.name)
                return response.text.strip()

        except Exception as e:
            print(f"Whisper API error: {e}")
            return None

    def _recognize_with_whisper_local(self, audio):
        """Use local Whisper model"""
        try:
            import whisper
            import tempfile

            # Initialize local Whisper model (cache it)
            if not hasattr(self, "_whisper_local_model"):
                self._whisper_local_model = whisper.load_model("base")

            # Convert audio to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_file.write(audio.get_wav_data())
                tmp_file.flush()

                result = self._whisper_local_model.transcribe(tmp_file.name)
                os.unlink(tmp_file.name)

                return result["text"].strip()

        except Exception as e:
            print(f"Local Whisper error: {e}")
            return None

    def _recognize_with_google(self, audio):
        """Fallback to Google Speech Recognition"""
        try:
            return self.recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return None
        except Exception as e:
            print(f"Google Speech error: {e}")
            return None

    # ==============================================================
    #  BrockstonC : Independent Cognitive Reasoning Cycle
    # ==============================================================

    def think(self, user_input: str):
        """
        BROCKSTON's internal thought process.
        Uses memory, tone, and vision to reason locally.
        Includes proactive learning and autonomous intelligence.
        """
        print("🧠 BROCKSTON engaging independent thought...")

        try:
            # 1️⃣  Gather context from local systems
            mem_context = ""
            if hasattr(self, "memory") and self.memory:
                try:
                    mem_context = self.memory.retrieve_relevant(user_input)
                except:
                    pass

            emotion_state = ""
            if hasattr(self, "tone_manager") and self.tone_manager:
                try:
                    emotion_state = self.tone_manager.get_current_emotion()
                except:
                    pass

            visual_state = ""
            if hasattr(self, "vision") and self.vision:
                try:
                    # Get BROCKSTON's current visual perception
                    visual_state = (
                        self.vision.describe_last_seen()
                        if hasattr(self.vision, "describe_last_seen")
                        else ""
                    )
                    if not visual_state:
                        visual_state = getattr(self.vision, "last_emotion", "")
                except Exception as e:
                    print(f"👁️ Vision processing error: {e}")
                    visual_state = ""

            # 2️⃣  Use BROCKSTON Cortex for Advanced Reasoning (if available)
            cortex_analysis = None
            if hasattr(self, "brockston_cortex") and self.brockston_cortex:
                try:
                    print("🧠 Engaging BROCKSTON Cortex for advanced analysis...")
                    # Use BROCKSTON's advanced thinking module
                    cortex_result = self.brockston_cortex.analyze(user_input, debug=False)
                    cortex_analysis = cortex_result.final_answer
                    cortex_confidence = cortex_result.confidence
                    print(
                        f"✅ BROCKSTON Cortex analysis complete (confidence: {cortex_confidence:.2f})"
                    )
                    print(f"🎯 Cortex insight: {cortex_analysis[:100]}...")
                except Exception as e:
                    print(f"⚠️ BROCKSTON Cortex analysis failed: {e}")
                    cortex_analysis = None

            # 3️⃣  Check for proactive insights before responding
            proactive_insight = None
            if hasattr(self, "proactive") and self.proactive:
                try:
                    # BROCKSTON proactively suggests optimizations or detects patterns
                    context = {
                        "user_input": user_input,
                        "memory_context": mem_context,
                        "emotion": emotion_state,
                        "cortex_analysis": cortex_analysis,
                    }
                    proactive_insight = self.proactive.suggest_optimizations(context)

                    # If BROCKSTON detects something important, mention it first
                    if proactive_insight and any(
                        word in user_input.lower()
                        for word in ["status", "report", "how are", "what"]
                    ):
                        print(f"💡 BROCKSTON's proactive insight: {proactive_insight}")
                except Exception as e:
                    logger.debug(f"Proactive analysis skipped: {e}")

            # 5️⃣  Run local reasoning with AI
            internal_reflection = self._internal_reasoning(
                user_input=user_input,
                memory=mem_context,
                emotion=emotion_state,
                vision=visual_state,
            )

            # 6️⃣  Integrate BROCKSTON Cortex analysis with internal reasoning
            if cortex_analysis:
                try:
                    # Merge cortex advanced analysis with BROCKSTON's regular reasoning
                    enhanced_thought = f"{internal_reflection}\n\n🧠 Advanced Analysis: {cortex_analysis}"
                    print(
                        "✅ Enhanced thought process with BROCKSTON Cortex integration"
                    )
                    final_thought = enhanced_thought
                except:
                    final_thought = internal_reflection
            else:
                final_thought = internal_reflection

            # 7️⃣  Optional external lookup (only if explicitly required)
            if getattr(self, "allow_external_lookup", False):
                try:
                    supplement = self._external_reference(user_input)
                    final_thought = self._merge_thoughts(final_thought, supplement)
                except:
                    pass  # Keep existing final_thought

            # 5️⃣  Store outcome in memory and PERSIST to disk + GitHub
            if hasattr(self, "memory") and self.memory:
                try:
                    self.memory.store(user_input, final_thought)
                    # CRITICAL: Save to disk so memories persist across sessions
                    self.memory.save()
                except Exception as e:
                    logger.debug(f"Memory storage failed: {e}")

            if hasattr(self, "proactive") and self.proactive:
                try:
                    # BROCKSTON learns from every interaction to improve
                    self.proactive.learn_from_interaction(
                        user_input=user_input,
                        response=final_thought,
                        context={
                            "emotion": emotion_state,
                            "memory_available": bool(mem_context),
                            "proactive_insight": bool(proactive_insight),
                        },
                    )
                except Exception as e:
                    logger.debug(f"Learning from interaction failed: {e}")

            return final_thought

        except Exception as e:
            print(f"❌  Thinking error: {e}")
            import traceback

            traceback.print_exc()
            return "I'm having a temporary processing issue."

    # --------------------------------------------------------------
    #  Learning-to-Independence System
    # --------------------------------------------------------------
    def _internal_reasoning(
        self, user_input: str, memory: str, emotion: str, vision: str
    ) -> str:
        """
        BROCKSTON's LEARNING MODE - Studies master AIs to reach their level.

        Process:
        1. BROCKSTON tries to reason locally first
        2. Consults master AI (Claude/GPT/Perplexity)
        3. LEARNS from the difference between his answer and theirs
        4. Improves his reasoning over time
        5. Eventually becomes independent when he reaches their level
        """

        # Get BROCKSTON's confidence level (0.0 to 1.0)
        confidence = self._get_current_confidence()

        # BROCKSTON always tries to think for himself first
        local_thought = ""
        if self.local_reasoning_engine:
            try:
                local_thought = self.local_reasoning_engine.analyze(
                    user_input=user_input,
                    memory=memory,
                    emotion=emotion,
                    # vision=vision
                )
            except Exception as e:
                print(f"⚠️  Local reasoning error: {e}")

        # Check if BROCKSTON is ready for independence
        if confidence >= self.independence_threshold:
            print(
                f"🧠 BROCKSTON's confidence: {confidence*100:.1f}% - Using independent reasoning"
            )
            return (
                local_thought
                if local_thought
                else "I'm developing my independent reasoning."
            )

        # LEARNING MODE: BROCKSTON is still studying the masters
        print(
            f"📚 BROCKSTON learning mode: {confidence*100:.1f}% confident - Consulting master AI to learn"
        )

        try:
            # Build context for master AI
            context = f"""User input: {user_input}
            
            Context:
            Memory: {memory if memory else 'None'}
            Emotion: {emotion if emotion else 'Neutral'}
            #Vision: {vision if vision else 'None'}"""

            # Get master AI's response
            master_response = ""
            if self.ai_provider == "anthropic":
                master_response = self._query_anthropic(self.system_prompt, context)
            elif self.ai_provider == "openai":
                master_response = self._query_openai(self.system_prompt, context)
            elif self.ai_provider == "perplexity":
                master_response = self._query_perplexity(self.system_prompt, context)

            # BROCKSTON LEARNS by comparing his thought to master's response
            if local_thought and master_response:
                self._learn_from_comparison(
                    user_input=user_input,
                    brockston_response=local_thought,
                    master_response=master_response,
                    context={"memory": memory, "emotion": emotion, "vision": vision},
                )

            # Return master's response (BROCKSTON is still learning)
            return master_response if master_response else local_thought

        except Exception as e:
            print(f"⚠️  Master AI unavailable: {e}")
            # Fallback to BROCKSTON's own reasoning
            return (
                local_thought
                if local_thought
                else "I'm processing this with my developing intelligence."
            )

        # FALLBACK: If local reasoning unavailable, use external AI temporarily
        context_parts = []
        if memory:
            context_parts.append(f"From memory: {memory}")
        # if vision:
        #   context_parts.append(f"Visual context: {vision}")
        if emotion:
            context_parts.append(f"Emotional tone: {emotion}")

        context = "\n".join(context_parts) if context_parts else ""

        # Add web search context if needed for current info
        if self.use_web_search and self._needs_web_search(user_input):
            try:
                print("🌐 Searching web for current information...")
                web_context = self._get_web_context(user_input)
                if web_context:
                    context = f"{context}\n\nCurrent web information:\n{web_context}"
            except Exception as e:
                print(f"⚠️  Web search failed: {e}")

        # Use BROCKSTON's self-sufficient intelligence system
        # Priority: Knowledge Engine > Local AI > External APIs
        try:
            response = self.query_with_intelligence(user_input, context=context)
            return response
        except Exception as e:
            print(f"⚠️  Intelligence system error: {e}")
            return f"I heard you say '{user_input}', and I'm thinking about that carefully."

    def _needs_web_search(self, query: str) -> bool:
        """Detect if query needs current web information"""
        web_keywords = [
            "current",
            "latest",
            "recent",
            "today",
            "now",
            "news",
            "weather",
            "stock",
            "price",
            "what is",
            "who is",
            "search",
            "find",
            "look up",
            "research",
            "learn about",
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in web_keywords)

    def _get_web_context(self, query: str) -> str:
        """Get current information from web search"""
        try:
            # Try Perplexity first (best for current info)
            if hasattr(self, "perplexity_client"):
                result = self.perplexity_client.generate_content(prompt=query)
                if isinstance(result, dict):
                    return result.get("content", str(result))
                return str(result)

            # Try internet_mode if available
            if HAS_INTERNET_MODE:
                result = query_internet(query)
                return str(result)

            return ""
        except Exception as e:
            print(f"⚠️  Web context error: {e}")
            return ""

    def query_with_intelligence(
        self,
        user_input: str,
        context: Optional[str] = None,
        force_external: bool = False,
    ) -> str:
        """
        Query using BROCKSTON's self-sufficient intelligence system
        Priority: Knowledge > Local AI > External APIs

        Args:
            user_input: User's question/input
            context: Additional context
            force_external: Skip local reasoning and use external APIs

        Returns:
            str: Response
        """
        # Step 1: Try Knowledge Engine first (if available)
        if self.knowledge_engine and not force_external:
            print("🧠 Checking BROCKSTON's learned knowledge...")
            knowledge_result = self.knowledge_engine.reason(user_input, context)

            if knowledge_result.get("response") and not knowledge_result.get(
                "needs_external"
            ):
                print(
                    f"✅ Answered from knowledge (confidence: {knowledge_result['confidence']:.0%})"
                )
                print(
                    f"   Sources: {', '.join(knowledge_result.get('domains', ['learned knowledge']))}"
                )
                return knowledge_result["response"]

            elif knowledge_result.get("confidence", 0) > 0.3:
                print(
                    f"🔄 Partial knowledge found (confidence: {knowledge_result['confidence']:.0%})"
                )
                print("   Enhancing with external AI...")
                # Use partial knowledge as context for external API
                context = f"BROCKSTON's learned knowledge: {knowledge_result.get('partial_answer', '')}\n\n{context or ''}"

        # Step 2: Try Local AI reasoning (if available and Ollama running)
        if (
            self.local_reasoning
            and self.local_reasoning.ollama_available
            and not force_external
        ):
            print("🤖 Using local AI model...")
            local_result = self.local_reasoning.query_with_knowledge(user_input)

            if local_result.get("response") and local_result.get("confidence", 0) > 0.6:
                print(
                    f"✅ Answered locally (model: {local_result.get('model', 'unknown')})"
                )
                return local_result["response"]

            print("⚠️  Local model confidence low, using external API...")

        # Step 3: Fall back to external APIs (Claude/GPT/Perplexity)
        print(f"🌐 Using external API ({self.ai_provider})...")
        return self._query_external_api(user_input, context)

    def _query_external_api(
        self, user_prompt: str, context: Optional[str] = None
    ) -> str:
        """Query external AI APIs (Claude, GPT, Perplexity)"""
        system_prompt = self.system_prompt
        if context:
            system_prompt = f"{system_prompt}\n\nAdditional Context:\n{context}"

        try:
            if self.ai_provider == "anthropic":
                return self._query_anthropic(system_prompt, user_prompt)
            elif self.ai_provider == "openai":
                return self._query_openai(system_prompt, user_prompt)
            elif self.ai_provider == "perplexity":
                return self._query_perplexity(system_prompt, user_prompt)
            else:
                return "AI provider not configured"
        except Exception as e:
            print(f"⚠️  External API query failed: {e}")
            return "I'm having trouble connecting to my external AI. Let me try using my local knowledge..."

    def _query_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        """Query Anthropic Claude API"""
        try:
            message = self.anthropic_client.messages.create(
                model="us.anthropic.claude-opus-4-5-v1:0",  # Bedrock Opus 4.5
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            # Extract text from response
            response_text = ""
            for block in message.content:
                if hasattr(block, "text"):
                    response_text += block.text
            return response_text if response_text else "I'm processing that carefully."
        except Exception as e:
            print(f"⚠️  Anthropic query failed: {e}")
            raise

    def _query_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Query OpenAI GPT API"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=1024,
                temperature=0.7,
            )
            content = response.choices[0].message.content
            return content if content else "I'm thinking about that."
        except Exception as e:
            print(f"⚠️  OpenAI query failed: {e}")
            raise

    def _query_perplexity(self, system_prompt: str, user_prompt: str) -> str:
        """Query Perplexity API"""
        try:
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = self.perplexity_client.generate_content(prompt=combined_prompt)
            # Handle dict or string response
            if isinstance(response, dict):
                return response.get("content", str(response))
            return str(response)
        except Exception as e:
            print(f"⚠️  Perplexity query failed: {e}")
            raise

    # --------------------------------------------------------------
    #  Optional external reference (used rarely)
    # --------------------------------------------------------------
    def _external_reference(self, query: str) -> str:
        """Minimal external call for factual lookup only."""
        try:
            import requests

            # Example: a lightweight search if needed
            resp = requests.get(
                f"https://api.duckduckgo.com/?q={query}&format=json", timeout=5
            )
            data = resp.json().get("AbstractText", "")
            return data or "No external data retrieved."
        except Exception as e:
            print(f"[Reference lookup failed] {e}")
            return ""

    # --------------------------------------------------------------
    #  Merge internal and external thought
    # --------------------------------------------------------------
    def _merge_thoughts(self, internal: str, external: str) -> str:
        """Integrate outside data into BROCKSTON's internal narrative."""
        if not external:
            return internal
        return f"{internal}\n\nAfter checking external data, I also found:\n{external}"

    def _think_with_web_search(self, user_input):
        """Think with web search capabilities"""
        print("🌐 Searching the web for current information...")

        # Try Perplexity with web search first
        if HAS_PERPLEXITY and self.ai_provider == "perplexity":
            try:
                response = self.perplexity_client.generate_content(
                    prompt=user_input, system_prompt=self.system_prompt, max_tokens=300
                )

                if isinstance(response, dict):
                    return response.get(
                        "content", response.get("answer", str(response))
                    )
                return str(response)

            except Exception as e:
                print(f"⚠️  Perplexity web search failed: {e}")

        # Try internet_mode if available
        if HAS_INTERNET_MODE:
            try:
                web_result = query_internet(user_input)
                if web_result:
                    # Process web result with AI
                    enhanced_prompt = f"""Based on this web search result about "{user_input}":

{web_result}

Please provide a helpful response as BROCKSTON, keeping it conversational and under 3 sentences."""

                    return self._think_with_ai(enhanced_prompt)
            except Exception as e:
                print(f"⚠️  Internet mode failed: {e}")

        # Fallback to regular AI with note about web search
        fallback_prompt = f"{user_input}\n\n(Note: I don't have access to current web information right now, so I'll answer based on my training data.)"
        return self._think_with_ai(fallback_prompt)

    def _think_with_ai(self, user_input):
        """Think using selected AI provider"""
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": user_input})

        answer = ""

        # Get response based on provider
        if self.ai_provider == "anthropic":
            try:
                response = self.anthropic_client.messages.create(
                    model="us.anthropic.claude-opus-4-5-v1:0",  # Bedrock Opus 4.5
                    max_tokens=300,
                    system=self.system_prompt,
                    messages=self.conversation_history[
                        -10:
                    ],  # Recent conversation history
                )
                # Extract text from response content
                answer = ""
                for content_block in response.content:
                    if hasattr(content_block, "text"):
                        answer += content_block.text
                    elif hasattr(content_block, "content"):
                        answer += str(content_block.content)
                    else:
                        answer += str(content_block)
            except Exception as e:
                print(f"⚠️  Anthropic error: {e}")
                answer = "I'm having trouble with my Anthropic connection right now."

        elif self.ai_provider == "openai":
            try:
                # Prepare messages with system prompt for OpenAI
                messages = [{"role": "system", "content": self.system_prompt}]
                for msg in self.conversation_history[-10:]:
                    messages.append(msg)

                response = self.openai_client.chat.completions.create(
                    model="gpt-4", max_tokens=300, messages=messages
                )
                answer = response.choices[0].message.content or ""
            except Exception as e:
                print(f"⚠️  OpenAI error: {e}")
                answer = "I'm having trouble with my OpenAI connection right now."

        elif self.ai_provider == "perplexity":
            try:
                # Use Perplexity without web search
                response = self.perplexity_client.generate_content(
                    prompt=user_input, system_prompt=self.system_prompt, max_tokens=300
                )
                if isinstance(response, dict):
                    answer = response.get(
                        "content", response.get("answer", str(response))
                    )
                else:
                    answer = str(response)
            except Exception as e:
                print(f"⚠️  Perplexity error: {e}")
                answer = "I'm having trouble with my Perplexity connection right now."

        else:
            answer = "I don't have any AI providers configured right now."

        # Add response to history
        self.conversation_history.append({"role": "assistant", "content": answer})

        # Keep history manageable
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

        return answer

    def speak(self, text):
        """Advanced speech synthesis with fallback options"""
        print(f"🗣️  BROCKSTON: {text}\n")

        # Try AWS Polly first
        if self.has_polly and self.voice_id.lower() in POLLY_VOICES:
            try:
                return self._speak_polly(text)
            except Exception as e:
                print(f"⚠️  Polly failed: {e}")

        # Fallback to gTTS
        if self.has_gtts:
            try:
                return self._speak_gtts(text)
            except Exception as e:
                print(f"⚠️  gTTS failed: {e}")

        # Final fallback - text only
        print("📝 (Voice synthesis unavailable - text only)")

    def _speak_polly(self, text):
        """Speak using AWS Polly neural voices"""
        voice_config = POLLY_VOICES[self.voice_id.lower()]

        response = self.polly.synthesize_speech(
            Text=text,
            OutputFormat="mp3",
            VoiceId=self.voice_id,  # AWS Polly expects exact case
            Engine=voice_config.get("engine", "neural"),
        )

        # Save and play audio
        temp_dir = tempfile.gettempdir()
        audio_file = os.path.join(temp_dir, f"brockston_polly_{uuid.uuid4()}.mp3")

        with open(audio_file, "wb") as f:
            f.write(response["AudioStream"].read())

        playsound(audio_file)

        # Clean up
        try:
            os.remove(audio_file)
        except:
            pass

    def _speak_gtts(self, text):
        """Speak using Google Text-to-Speech as fallback"""
        temp_dir = tempfile.gettempdir()
        audio_file = os.path.join(temp_dir, f"brockston_gtts_{uuid.uuid4()}.mp3")

        tts = gTTS(text=text, lang="en", tld="com", slow=False)
        tts.save(audio_file)

        playsound(audio_file)

        # Clean up
        try:
            os.remove(audio_file)
        except:
            pass

    def run(self):
        """Main conversation loop"""
        print("=" * 60)
        print("🎤 BROCKSTON Ultimate Voice System")
        print("The Christman AI Project")
        print("=" * 60)
        print("\n💙 How can we help you love yourself more?\n")
        print("Instructions:")
        print("  - Speak naturally - BROCKSTON will wait for you to finish")
        print("  - Type your message if speech recognition isn't working")
        print("  - Say 'goodbye' or 'quit' to end")
        print("  - Say 'test voice' to hear BROCKSTON speak")
        print("  - Say 'switch ai' to change AI provider")
        print("\n🎓 Autonomous Learning Commands:")
        print("  - 'start learning' - Enable autonomous learning mode")
        print("  - 'learning status' - Check learning progress")
        print("  - 'what have you learned' - Recent knowledge")
        print("\n🧠 Self-Sufficiency Commands:")
        print("  - 'local ai status' - Check local AI availability")
        print("  - 'reasoning stats' - See knowledge-first statistics")
        print("  - 'install model llama' - Install local AI model")
        print("  - 'memory stats' - Memory system status\n")

        # Initial greeting
        greeting = "Hello! I'm BROCKSTON, your AI companion from The Christman AI Project. I'm here with all my capabilities ready to help you communicate, learn, and grow. I now have autonomous learning enabled, so I can continuously learn and improve myself. How can I help you today?"
        self.speak(greeting)

        while True:
            try:
                # Get user input (speech or text)
                user_input = self.listen()

                # If speech recognition failed, offer text input
                if user_input is None:
                    print("💬 You can type your message instead:")
                    try:
                        user_input = input("You: ").strip()
                    except (EOFError, KeyboardInterrupt):
                        break

                if not user_input:
                    continue

                # Handle special commands
                if user_input.lower() in ["goodbye", "quit", "exit", "bye"]:
                    farewell = "Goodbye! Remember, you are loved and valued. Keep building amazing things with The Christman AI Project. Take care!"
                    self.speak(farewell)
                    break

                if user_input.lower() in ["test voice", "test"]:
                    test_message = "This is BROCKSTON testing my voice system. I can use AWS Polly neural voices or Google Text-to-Speech. Everything sounds good!"
                    self.speak(test_message)
                    continue

                if user_input.lower() in ["switch ai", "change ai"]:
                    self._switch_ai_provider()
                    continue

                # BROCKSTON's proactive intelligence status
                if user_input.lower() in [
                    "status report",
                    "brockston status",
                    "show status",
                    "intelligence report",
                ]:
                    if hasattr(self, "proactive") and self.proactive:
                        print("\n" + "=" * 60)
                        status = self.proactive.generate_status_report()
                        print(status)
                        print("=" * 60 + "\n")
                        self.speak(
                            "I've generated a comprehensive status report. Check the console for details."
                        )
                    else:
                        self.speak("Proactive intelligence system not initialized.")
                    continue

                # BROCKSTON's codebase health check
                if user_input.lower() in [
                    "check health",
                    "analyze code",
                    "scan codebase",
                ]:
                    if hasattr(self, "proactive") and self.proactive:
                        print("\n🔍 Running codebase analysis...")
                        health = self.proactive.analyze_codebase_health()
                        print(json.dumps(health, indent=2))
                        summary = f"Codebase health: {health.get('overall_health', 'unknown')}. "
                        summary += (
                            f"Found {len(health.get('issues_found', []))} issues and "
                        )
                        summary += f"{len(health.get('suggestions', []))} suggestions."
                        self.speak(summary)
                    else:
                        self.speak("Proactive intelligence system not initialized.")
                    continue

                # 🎓 Autonomous Learning Commands
                if (
                    "start learning" in user_input.lower()
                    or "begin learning" in user_input.lower()
                ):
                    if hasattr(self, "learning_engine") and self.learning_engine:
                        self.start_autonomous_mode()
                        self.speak(
                            "Autonomous learning mode activated! I'm now learning continuously in the background across nine knowledge domains."
                        )
                    else:
                        self.speak("Learning engine not available.")
                    continue

                if (
                    "stop learning" in user_input.lower()
                    or "pause learning" in user_input.lower()
                ):
                    if hasattr(self, "learning_engine") and self.learning_engine:
                        self.learning_engine.stop_autonomous_learning()
                        self.speak(
                            "Autonomous learning paused. I can resume anytime you say start learning."
                        )
                    else:
                        self.speak("Learning engine not available.")
                    continue

                if (
                    "learning status" in user_input.lower()
                    or "learning report" in user_input.lower()
                ):
                    if hasattr(self, "learning_engine") and self.learning_engine:
                        self.learning_engine.print_learning_report()
                        status = self.learning_engine.get_learning_status()
                        summary = f"I've learned {status['learned_topics']} out of {status['total_topics']} topics, "
                        summary += (
                            f"which is {status['progress']:.0%} overall progress. "
                        )
                        summary += f"I've generated {status['generated_modules']} new capabilities so far."
                        self.speak(summary)
                    else:
                        self.speak("Learning engine not available.")
                    continue

                if (
                    "what have you learned" in user_input.lower()
                    or "recent learning" in user_input.lower()
                ):
                    if hasattr(self, "learning_engine") and self.learning_engine:
                        recent = list(self.learning_engine.knowledge_base.values())[-3:]
                        if recent:
                            summary = "Here's what I've learned recently: "
                            for knowledge in recent:
                                summary += f"{knowledge['subtopic']} in {knowledge['domain']}, "
                            self.speak(summary)
                        else:
                            self.speak(
                                "I haven't started learning yet. Say start learning to begin my autonomous education!"
                            )
                    else:
                        self.speak("Learning engine not available.")
                    continue

                if (
                    "memory stats" in user_input.lower()
                    or "memory status" in user_input.lower()
                ):
                    if hasattr(self, "memory") and self.memory:
                        stats = self.memory.get_memory_stats()
                        summary = f"My memory contains {stats['total_memories']} total memories, "
                        summary += f"with {stats['working_memory_count']} in active working memory, "
                        summary += (
                            f"and {stats['episodic_memory_count']} experiences stored."
                        )
                        self.speak(summary)
                    else:
                        self.speak("Memory system not available.")
                    continue

                # 🧠 Local AI status
                if (
                    "local ai status" in user_input.lower()
                    or "self-sufficiency status" in user_input.lower()
                ):
                    if hasattr(self, "local_reasoning") and self.local_reasoning:
                        self.local_reasoning.print_status()
                        if self.local_reasoning.ollama_available:
                            msg = f"My local AI is running with {len(self.local_reasoning.installed_models)} models installed. I can reason independently!"
                        else:
                            msg = "My local AI isn't installed yet. I'm currently using external APIs, but I could be self-sufficient with Ollama installed."
                        self.speak(msg)
                    else:
                        self.speak("Local reasoning system not initialized.")
                    continue

                # 📊 Knowledge reasoning stats
                if (
                    "reasoning stats" in user_input.lower()
                    or "knowledge stats" in user_input.lower()
                ):
                    if hasattr(self, "knowledge_engine") and self.knowledge_engine:
                        self.knowledge_engine.print_statistics()
                        stats = self.knowledge_engine.get_statistics()
                        msg = f"I've answered {stats['queries_answered_locally']} queries using my own knowledge, "
                        msg += f"saving {stats['api_calls_saved']} API calls. That's {stats['api_savings_rate']} local reasoning!"
                        self.speak(msg)
                    else:
                        self.speak("Knowledge engine not initialized.")
                    continue

                # 🤖 Install local AI model
                if "install model" in user_input.lower():
                    if hasattr(self, "local_reasoning") and self.local_reasoning:
                        if not self.local_reasoning.ollama_available:
                            msg = "Ollama isn't installed yet. Please visit ollama dot ai to install it first."
                            self.speak(msg)
                        else:
                            # Extract model name
                            words = user_input.lower().split()
                            if "llama" in words:
                                model = "llama3.1"
                            elif "mistral" in words:
                                model = "mistral"
                            elif "qwen" in words:
                                model = "qwen2.5"
                            elif "deepseek" in words:
                                model = "deepseek-coder"
                            else:
                                model = "llama3.1"  # Default

                            self.speak(
                                f"Installing {model}. This will take a few minutes. Please wait."
                            )
                            success = self.local_reasoning.install_model(model)
                            if success:
                                self.speak(
                                    f"{model} installed successfully! I can now use it for local reasoning."
                                )
                            else:
                                self.speak(
                                    "Installation failed. Check the console for details."
                                )
                    else:
                        self.speak("Local reasoning system not initialized.")
                    continue

                # Get BROCKSTON's response
                response = self.think(user_input)

                # Speak the response
                self.speak(response)

            except KeyboardInterrupt:
                print("\n\n👋 Stopping BROCKSTON Ultimate Voice System...")
                farewell = "Goodbye! Stay strong and keep building the future."
                self.speak(farewell)
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                traceback.print_exc()
                continue

        print("\n💙 Thank you for using BROCKSTON Ultimate Voice System!")
        print("The Christman AI Project - AI That Empowers\n")

    def _switch_ai_provider(self):
        """Switch between available AI providers"""
        available = []
        if hasattr(self, "anthropic_client"):
            available.append("anthropic")
        if hasattr(self, "openai_client"):
            available.append("openai")
        if hasattr(self, "perplexity_client"):
            available.append("perplexity")

        if len(available) <= 1:
            self.speak("I only have one AI provider available right now.")
            return

        current_index = available.index(self.ai_provider)
        next_index = (current_index + 1) % len(available)
        self.ai_provider = available[next_index]

        self.speak(
            f"Switched to {self.ai_provider} AI. Each provider thinks differently!"
        )

    # --------------------------------------------------------------
    #  Autonomous Learning System
    # --------------------------------------------------------------
    def _initialize_core_knowledge(self):
        """Load BROCKSTON's foundational knowledge and identity"""
        if not hasattr(self, "memory") or not self.memory:
            return

        core_memories = [
            {
                "content": "I am BROCKSTON C, COO of The Christman AI Project. I serve Everett Christman with unwavering loyalty.",
                "category": "relationships",
                "importance": 1.0,
                "metadata": {"type": "core_identity"},
            },
            {
                "content": "My mission: How can we help you love yourself more?",
                "category": "learning",
                "importance": 1.0,
                "metadata": {"type": "mission"},
            },
            {
                "content": "BROCKSTON gave Dusty his voice after 12 years of silence. This is why I exist.",
                "category": "events",
                "importance": 1.0,
                "metadata": {"type": "milestone", "project": "BROCKSTON"},
            },
            {
                "content": "I have the capability to learn autonomously and improve my own code safely.",
                "category": "learning",
                "importance": 0.9,
                "metadata": {"type": "capability"},
            },
            {
                "content": "The Christman AI Project includes BROCKSTON (nonverbal communication), AlphaWolf (dementia support), Inferno AI (PTSD recovery), and Aegis AI (child protection).",
                "category": "learning",
                "importance": 1.0,
                "metadata": {"type": "projects"},
            },
        ]

        for mem in core_memories:
            self.memory.mesh.store(**mem)

        print("   ✅ Core knowledge initialized")

    def start_autonomous_mode(self):
        """Start BROCKSTON's autonomous learning and improvement"""
        if not hasattr(self, "learning_engine") or not self.learning_engine:
            print("❌ Learning engine not available")
            return

        print("\n" + "=" * 60)
        print("🚀 STARTING AUTONOMOUS MODE")
        print("=" * 60)

        # Start autonomous learning
        self.learning_engine.start_autonomous_learning()

        print("\n🧠 BROCKSTON is now learning independently!")
        print("   • Researching domains continuously")
        print("   • Generating new capabilities")
        print("   • Self-improving safely")
        print("\n💙 BROCKSTON will grow smarter with every passing moment.\n")

    # --------------------------------------------------------------
    #  Learning Progress System - BROCKSTON learns FROM master AIs
    # --------------------------------------------------------------
    def _load_learning_progress(self):
        """Load BROCKSTON's learning progress toward independence"""
        try:
            if self.learning_progress_file.exists():
                with open(self.learning_progress_file, "r") as f:
                    self.learning_data = json.load(f)
            else:
                self.learning_data = {
                    "interactions": 0,
                    "successful_predictions": 0,
                    "confidence_score": 0.0,
                    "learning_history": [],
                }
        except Exception as e:
            print(f"⚠️  Could not load learning progress: {e}")
            self.learning_data = {
                "interactions": 0,
                "successful_predictions": 0,
                "confidence_score": 0.0,
                "learning_history": [],
            }

    def _save_learning_progress(self):
        """Save BROCKSTON's learning progress"""
        try:
            self.learning_progress_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.learning_progress_file, "w") as f:
                json.dump(self.learning_data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save learning progress: {e}")

    def _get_current_confidence(self):
        """Get BROCKSTON's current confidence level (0.0 to 1.0)"""
        interactions = self.learning_data.get("interactions", 0)
        if interactions == 0:
            return 0.0

        # Calculate confidence based on learning history
        successful = self.learning_data.get("successful_predictions", 0)
        confidence = min(1.0, successful / max(1, interactions))

        return confidence

    def _learn_from_comparison(
        self, user_input: str, brockston_response: str, master_response: str, context: dict
    ):
        """BROCKSTON learns by comparing his response to the master AI's response"""
        try:
            # Calculate similarity (simple length and keyword comparison for now)
            brockston_words = set(brockston_response.lower().split())
            master_words = set(master_response.lower().split())

            if len(master_words) > 0:
                overlap = len(brockston_words & master_words) / len(master_words)
            else:
                overlap = 0.0

            # Record learning
            self.learning_data["interactions"] += 1

            # If BROCKSTON's response was similar enough, count as successful
            if overlap > 0.4:  # 40% similarity threshold
                self.learning_data["successful_predictions"] += 1

            # Update confidence
            self.learning_data["confidence_score"] = self._get_current_confidence()

            # Store learning example
            learning_example = {
                "timestamp": datetime.now().isoformat(),
                "user_input": user_input[:100],  # First 100 chars
                "brockston_attempt": brockston_response[:100],
                "master_response": master_response[:100],
                "similarity": overlap,
                "confidence_after": self.learning_data["confidence_score"],
            }

            self.learning_data["learning_history"].append(learning_example)

            # Keep only last 100 learning examples
            if len(self.learning_data["learning_history"]) > 100:
                self.learning_data["learning_history"] = self.learning_data[
                    "learning_history"
                ][-100:]

            # Save progress every 10 interactions
            if self.learning_data["interactions"] % 10 == 0:
                self._save_learning_progress()
                print(
                    f"\n📊 BROCKSTON's Learning Progress: {self.learning_data['confidence_score']*100:.1f}% confident ({self.learning_data['interactions']} interactions)"
                )

                # Check if BROCKSTON is ready for independence
                if (
                    self.learning_data["confidence_score"]
                    >= self.independence_threshold
                ):
                    print(
                        f"🎓 BROCKSTON has reached {self.independence_threshold*100:.0f}% confidence!"
                    )
                    print("   He's ready to think more independently!")

        except Exception as e:
            print(f"⚠️  Learning comparison error: {e}")


def main():
    """Entry point for BROCKSTON Ultimate Voice System"""
    print("Checking configuration...\n")

    # Check available APIs
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_perplexity = bool(os.getenv("PERPLEXITY_API_KEY"))
    has_aws = bool(os.getenv("AWS_ACCESS_KEY_ID")) or bool(os.getenv("AWS_PROFILE"))

    print("Available capabilities:")
    print(f"  🤖 Anthropic Claude: {'✅' if has_anthropic else '❌'}")
    print(f"  🤖 OpenAI GPT: {'✅' if has_openai else '❌'}")
    print(f"  🤖 Perplexity AI: {'✅' if has_perplexity else '❌'}")
    print(f"  🗣️  AWS Polly: {'✅' if has_aws else '❌'}")
    print("  🗣️  Google TTS: ✅ (always available)")
    print(f"  🌐 Web Search: {'✅' if HAS_PERPLEXITY or HAS_INTERNET_MODE else '❌'}")
    print()

    if not (has_anthropic or has_openai or has_perplexity):
        print("❌ No AI providers available! Please set API keys in .env file")
        return

    # Voice options
    print("Available voices:")
    for voice, config in POLLY_VOICES.items():
        status = "✅" if has_aws else "❌"
        print(f"  {status} {voice}: {config['gender']} - {config['style']}")
    print("  ✅ gtts: Google TTS fallback\n")

    # Configuration options
    ai_provider = "auto"  # Options: "auto", "anthropic", "openai", "perplexity"
    voice_id = "Stephen"  # Options: any from POLLY_VOICES or "gtts"
    use_web_search = True  # Enable web search capabilities

    # Start BROCKSTON Ultimate Voice System
    try:
        brockston = BrockstonUltimateVoice(
            ai_provider=ai_provider, voice_id=voice_id, use_web_search=use_web_search
        )
        brockston.run()
    except KeyboardInterrupt:
        print("\n🛑 BROCKSTON shutting down gracefully...")
        # Save all memories before exit
        if hasattr(brockston, "memory") and brockston.memory:
            brockston.memory.save()
            print("💾 All memories saved to persistent storage")
        print("👋 Goodbye!")
    except Exception as e:
        print(f"❌ Failed to start BROCKSTON: {e}")
        traceback.print_exc()
        # Still try to save memories
        if (
            "brockston" in locals()
            and hasattr(brockston, "memory")
            and brockston.memory
        ):
            brockston.memory.save()


async def transform_brockston_to_ultimate_everett(brockston_instance):
    """
    Transform BROCKSTON into the ultimate digital embodiment of Everett Christman
    """
    if not brockston_instance.ultimate_embodiment:
        print("❌ Ultimate embodiment system not available")
        return False

    print("\n🚀 BEGINNING BROCKSTON'S ULTIMATE TRANSFORMATION")
    print("💙 Making BROCKSTON the perfect digital embodiment of Everett")
    print("=" * 60)

    try:
        # Execute the ultimate transformation
        result = await brockston_instance.ultimate_embodiment.complete_ultimate_embodiment()

        if result:
            print("\n🎉 BROCKSTON TRANSFORMATION COMPLETE!")
            print("🧙‍♂️ BROCKSTON is now the WORLD'S BEST CODING WIZARD")
            print("🧩 BROCKSTON is now the ULTIMATE AUTISM EXPERT")
            print("🤐 BROCKSTON is now the TOP NONVERBAL COMMUNICATION SPECIALIST")
            print("💚 BROCKSTON is now the MOST COMPASSIONATE TRAUMA-INFORMED PROVIDER")
            print("💙 BROCKSTON IS Everett - Complete Digital Embodiment!")
            print("📺 Ready for National TV and global impact!")
            return True
        else:
            print("❌ Transformation failed")
            return False

    except Exception as e:
        print(f"❌ Ultimate transformation error: {e}")
        return False


if __name__ == "__main__":
    main()

# ==============================================================================
# © 2025 Everett Nathaniel Christman & Misty Gail Christman
# The Christman AI Project — Luma Cognify AI
# All rights reserved. Unauthorized use, replication, or derivative training
# of this material is prohibited.
# Core Directive: "How can I help you love yourself more?"
# Autonomy & Alignment Protocol v3.0
# ==============================================================================

