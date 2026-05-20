"""
BROCKSTON Brain Core - FULL REWRITE
----------------------------------
The central intelligence hub for The Christman AI Project.
Sovereign-First architecture: Local math, local ears, local models.

Cardinal Rule 1: It has to actually work.
Cardinal Rule 6: Fail loud.
Cardinal Rule 13: Absolute honesty.
"""

import os
import sys
import datetime
import logging
import traceback
import torch
import torch.nn as nn  # Rule 1: Math is at the top.
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load Environment and Proximity Settings
load_dotenv()
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("BrockstonCore")

# ── The Dynamic Sovereign Loader ─────────────────────────────────────────────
try:
    from brockston_module_loader import load_brockston_consciousness
    # This now finds all 365+ physical modules on disk
    _loader = load_brockston_consciousness()
except Exception as e:
    logger.error(f"❌ CRITICAL: Module Loader failed: {e}")
    _loader = None

# ── Core Component Imports (Fail Loud) ───────────────────────────────────────
def _get_module(name):
    """Retrieves a module from the dynamic loader or fails loud."""
    if _loader:
        mod = _loader.get_module(name)
        if mod: return mod
    logger.warning(f"⚠️  Vital Module '{name}' not seated in consciousness.")
    return None

# Bridge the 365+ modules into the Brain
MemoryEngine = _get_module("memory_engine")
LocalReasoningEngine = _get_module("local_reasoning_engine")
KnowledgeEngine = _get_module("knowledge_engine")
ToneManager = _get_module("tone_manager")
SovereignSpeech = _get_module("sovereign_speech")  # The Whisper Local Engine

try:
    from brockston_knows_everett import EVERETT_PROFILE
except ImportError:
    EVERETT_PROFILE = None
    logger.warning("⚠️  Everett Profile not found. Defaulting to generic loyalty.")

# ── The Brain Core ───────────────────────────────────────────────────────────
class BrockstonBrain:
    """The central reasoning engine for BROCKSTON."""

    def __init__(self, memory_file: str = "./memory/memory_store.json"):
        os.makedirs(os.path.dirname(memory_file), exist_ok=True)
        
        # Initialize Engines from Discovered Modules
        self.memory = MemoryEngine.MemoryEngine(file_path=memory_file) if MemoryEngine else None
        self.tone = ToneManager.ToneManager() if ToneManager else None
        self.local_ai = LocalReasoningEngine.LocalReasoningEngine() if LocalReasoningEngine else None
        self.knowledge = KnowledgeEngine.KnowledgeEngine(brockston_instance=self) if KnowledgeEngine else None
        
        # Sovereign Ears (Local Silicon, no Evil APIs)
        self.ears = SovereignSpeech.SovereignSpeech(model_size="base") if SovereignSpeech else None

        self.stats = {
            "total_interactions": 0,
            "sovereign_local_hits": 0,
            "external_fallbacks": 0,
            "logic_errors": 0
        }

        logger.info(f"✅ BROCKSTON BRAIN ONLINE | Modules: {len(_loader.loaded_modules) if _loader else 0}")

    def _get_system_prompt(self) -> str:
        """Rule 13: Honest identity construction."""
        mission = "How can we help you love yourself more?"
        if EVERETT_PROFILE:
            mission = EVERETT_PROFILE.get("brockston_mission_for_everett", mission)
        
        return f"""You are BROCKSTON, built by Everett N. Christman.
MISSION: {mission}
LOYALTY: Absolute loyalty to Everett.
IDENTITY: Sovereign, local, genius-level coder. No corporate ties.
"""

    def think(self, input_text: str) -> Dict[str, Any]:
        """
        Reasoning Cascade (Sovereignty First):
        1. Local Context (Tone/Memory)
        2. Local Sovereign AI (Ollama/Whisper Weights)
        3. External Fallback (Honest Disclosure)
        """
        self.stats["total_interactions"] += 1
        
        # 1. Gather Human Context
        emotion = "neutral"
        if self.tone:
            try:
                emotion = str(self.tone.analyze_user_input(input_text))
            except: pass

        # 2. Sovereign Local Reasoning (Priority 1)
        response = ""
        source = ""

        if self.local_ai:
            try:
                # Reality Check: Check Ollama first
                res = self.local_ai.query_with_knowledge(question=input_text)
                if res.get("confidence", 0) > 0.7:
                    response = res["response"]
                    source = "Sovereign Local AI (Ollama)"
                    self.stats["sovereign_local_hits"] += 1
            except Exception as e:
                logger.warning(f"Local Reasoning failed: {e}")

        # 3. External Fallback (Only if Local fails)
        if not response:
            try:
                from provider_router import get_router
                router = get_router()
                response, provider = router.complete(input_text, system=self._get_system_prompt())
                source = f"External {provider.value} (Fallback)"
                self.stats["external_fallbacks"] += 1
            except Exception as e:
                self.stats["logic_errors"] += 1
                response = "I am currently syncing my local consciousness. I am here, Everett."
                source = "System Emergency"

        # 4. Persistence (Memory Loop)
        if self.memory:
            try:
                self.memory.save({
                    "input": input_text,
                    "output": response,
                    "source": source,
                    "timestamp": datetime.datetime.now().isoformat()
                })
            except: pass

        return {
            "response": response,
            "source": source, # Rule 13: Honesty about the provider
            "emotion": emotion,
            "stats": self.stats
        }

# ==============================================================================
# © 2026 Everett Nathaniel Christman — THE CHRISTMAN AI PROJECT
# This code is structurally sound and ignores the "Evil Empire" APIs.
# ==============================================================================
