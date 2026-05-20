"""Self-Learning and Adaptation Engine for AlphaWolf.

Part of The Christman AI Project - Powered by LumaCognify AI
Originally developed for AlphaVox, adapted for AlphaWolf's cognitive care mission.

This module implements autonomous learning capabilities for AlphaWolf,
allowing the system to improve over time based on user interactions,
adapt its models for dementia and Alzheimer's care, and continuously
enhance its ability to support patients and caregivers.

Mission: Cognitive support that learns, adapts, and never forgets to care.
"""

import os
import logging
import threading
import time
import json
import ast
import ollama  # Added
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from memory_engine import MemoryEngine

logger = logging.getLogger(__name__)

# No OpenAI client needed anymore; ollama interacts directly with the local server
memory_engine = MemoryEngine(file_path="./memory/memory_store.json")

# ... (rest of your existing setup code)

# Updated Embedding/Learning Logic
def learn_from_text(text: str):
    """
    Directly embed crawled text using llama3.2:3b for vector generation.
    """
    if not text or not text.strip():
        logger.warning("Received empty text for learning.")
        return "No text provided"

    try:
        # Using llama3.2:3b for embeddings
        response = ollama.embeddings(
            model="llama3.2:3b",
            prompt=text
        )
        vector = response["embedding"]
        
        memory_engine.save({
            "type": "web_ingest",
            "text": text,
            "vector": vector,
            "source": "alphawolf_learning"
        })
        logger.info(f"✅ AlphaWolf learned from {len(text)} characters of text")
        return "Learning complete"
    except Exception as e:
        logger.error(f"❌ AlphaWolf learning failed: {e}")
        return "Learning failed"

# New Inference method for the CodeAnalyzer
def get_code_fix_suggestion(error_context: str) -> str:
    """
    Uses Qwen2.5-coder:32b to generate a code fix based on the error context.
    """
    prompt = f"Analyze this error and provide a concise code fix: {error_context}"
    try:
        response = ollama.chat(model='qwen2.5-coder:32b', messages=[
            {'role': 'user', 'content': prompt},
        ])
        return response['message']['content']
    except Exception as e:
        logger.error(f"❌ Qwen inference failed: {e}")
        return "Could not generate fix."