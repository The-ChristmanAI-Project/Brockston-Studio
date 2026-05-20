"""BROCKSTON's master learning coordinator."""

import logging
import time

from ai_learning_engine import get_self_improvement_engine
from advanced_learning import AdvancedLearningSystem
from self_modifying_code import get_self_modifying_code_engine
from evolutionary_engine import EvolutionaryAI

logger = logging.getLogger(__name__)


class BrockstonLearningCoordinator:
    """Coordinates BROCKSTON's learning, analysis, and code improvement systems."""

    def __init__(self) -> None:
        self.self_improvement = get_self_improvement_engine()
        self.advanced_learning = AdvancedLearningSystem()
        self.code_modifier = get_self_modifying_code_engine()
        self.evolutionary_ai = EvolutionaryAI(population_size=10, input_size=128, output_size=128)
        self.evolutionary_ai.load_fittest()
        logger.info("BROCKSTON Learning Coordinator initialized with Evolutionary Engine")

    def start_all_systems(self) -> None:
        """Start the engines BROCKSTON uses for continuous learning."""
        try:
            self.self_improvement.start_learning()
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Self-improvement engine failed to start: %s", exc)
        try:
            self.code_modifier.start_auto_mode()
        except Exception as exc:  # pragma: no cover
            logger.error("Code modifier auto-mode failed to start: %s", exc)
        else:
            logger.info("All BROCKSTON learning systems active")

    def daily_learning_cycle(self) -> None:
        """Run BROCKSTON's daily learning workflow."""
        current_time = time.time()

        for (
            source_id,
            source_info,
        ) in self.advanced_learning.external_knowledge_sources.items():
            last_update = source_info.get("last_update", 0)
            update_frequency = source_info.get("update_frequency", 86_400)
            if current_time - last_update < update_frequency:
                continue

            try:
                self.advanced_learning.process_knowledge_update(
                    source_id, source_info, current_time
                )
            except Exception as exc:  # pragma: no cover
                logger.error("Failed knowledge update for %s: %s", source_id, exc)
            else:
                source_info["last_update"] = current_time

        try:
            suggestions = self.self_improvement.get_improvement_suggestions()
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to collect improvement suggestions: %s", exc)
            suggestions = []

        for suggestion in suggestions:
            if suggestion.get("severity") != "high":
                continue
            file_path = suggestion.get("module") or "unknown"
            description = suggestion.get("description", "High severity issue")
            try:
                queued = self.code_modifier.queue_modification(
                    file_path=file_path,
                    issue_description=description,
                    modification_type="bugfix",
                )
                if queued:
                    logger.info("Queued high severity fix for %s", file_path)
            except Exception as exc:  # pragma: no cover
                logger.error("Unable to queue modification for %s: %s", file_path, exc)

        try:
            self.evolutionary_ai.evolve_step()
            self.evolutionary_ai.save_fittest()
            logger.info("Evolutionary cycle complete - best architecture preserved")
        except Exception as exc:
            logger.error("Evolutionary step failed: %s", exc)

        try:
            self.advanced_learning.generate_daily_summary()
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to generate daily summary: %s", exc)
        else:
            logger.info("Daily learning cycle complete")


brockston_coordinator = BrockstonLearningCoordinator()


def start_brockston_learning() -> None:
    """Initialize BROCKSTON's learning systems."""
    brockston_coordinator.start_all_systems()


# ==============================================================================
# © 2025 Everett Nathaniel Christman
# The Christman AI Project — Luma Cognify AI
# All rights reserved. Unauthorized use, replication, or derivative training
# of this material is prohibited.
#
# Core Directive: "How can I help you love yourself more?"
# Autonomy & Alignment Protocol v3.0
# ==============================================================================
