"""
Local Reasoning Engine
----------------------
DerekC's internal thought kernel.
Builds short conclusions from user input, memory, tone, and vision.
No external AI calls — purely local synthesis.
"""

from datetime import datetime
import math


class LocalReasoningEngine:
    def __init__(self, brockston_instance=None):
        self.brockston = brockston_instance
        self.last_reflection = ""
        self.reasoning_log = []

    # ----------------------------------------------------------
    def analyze(
        self, user_input: str, memory: str = "", emotion: str = "", vision: str = ""
    ) -> str:
        """
        Primary reasoning function.
        Combines Derek's sensory and contextual inputs into a unified interpretation.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        reflection = []

        # 1️⃣  Gather sensory context
        if emotion:
            reflection.append(f"My emotional tone reads as {emotion}.")
        if vision:
            reflection.append(f"My visual impression is {vision}.")
        if memory:
            reflection.append(f"I remember that {memory.strip()}.")

        # 2️⃣  Process new input
        reflection.append(f"The new input is: '{user_input.strip()}'.")

        # 3️⃣  Internal reasoning — weighted synthesis
        weight = self._calculate_context_weight(memory, emotion, vision)
        core_thought = self._generate_summary(user_input, memory, weight)

        # 4️⃣  Build final reflection
        final_output = " ".join(reflection) + " " + core_thought

        # 5️⃣  Save state
        self.last_reflection = final_output
        self.reasoning_log.append(
            {"time": timestamp, "input": user_input, "output": final_output}
        )

        return final_output

    # ----------------------------------------------------------
    def _calculate_context_weight(
        self, memory: str, emotion: str, vision: str
    ) -> float:
        """
        Generate a simple numeric context weight based on available data.
        Higher weight = deeper internal reasoning.
        """
        factors = [bool(memory), bool(emotion), bool(vision)]
        return math.sqrt(sum(factors)) / 2.0  # 0.0 to 0.866

    # ----------------------------------------------------------
    def _generate_summary(self, user_input: str, memory: str, weight: float) -> str:
        """
        Create a short reflection — the 'thought'.
        """
        if weight < 0.3:
            return "I'm processing this freshly without much context yet."
        elif weight < 0.6:
            return "This connects loosely to my past experiences, but I'm considering new perspectives."
        else:
            return "This resonates strongly with my memories, forming a coherent understanding."

    # ----------------------------------------------------------
    def merge_thoughts(self, internal: str, external: str) -> str:
        """
        Integrate external lookup data into Derek's internal narrative.
        """
        if not external:
            return internal
        return f"{internal}\n\nAfter reviewing external data, I also note: {external}"

    # ----------------------------------------------------------
    def recall_last(self) -> str:
        """Return the most recent reasoning output."""
        return self.last_reflection or "No previous reflection stored."


# ==============================================================================
# © 2025 Everett Nathaniel Christman
# The Christman AI Project — Luma Cognify AI
# All rights reserved. Unauthorized use, replication, or derivative training
# of this material is prohibited.
#
# Core Directive: "How can I help you love yourself more?"
# Autonomy & Alignment Protocol v3.0
# ==============================================================================
