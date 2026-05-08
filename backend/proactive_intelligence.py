"""
Derek's Proactive Intelligence System
Autonomous learning, problem detection, and solution generation

Makes Derek ahead of the curve - detecting and fixing issues before Everett notices them.
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


class ProactiveIntelligence:
    """
    Serafinia proactive intelligence system.
    Continuously learns, monitors, and suggests improvements.
    """

    def __init__(self, ai_provider=None, memory_manager=None):
        self.ai_provider = ai_provider
        self.memory = memory_manager
        self.learning_log = Path("./memory/proactive_learning.json")
        self.insights = []
        self.active_monitoring = False
        self.monitoring_thread = None

        # Load previous learning
        self._load_learning_history()

    def _load_learning_history(self):
        """Load previous learning and insights"""
        try:
            if self.learning_log.exists():
                with open(self.learning_log, "r") as f:
                    data = json.load(f)
                    self.insights = data.get("insights", [])
                    logger.info(f"Loaded {len(self.insights)} previous insights")
        except Exception as e:
            logger.warning(f"Could not load learning history: {e}")
            self.insights = []

    def _save_learning_history(self):
        """Save learning and insights"""
        try:
            self.learning_log.parent.mkdir(parents=True, exist_ok=True)
            with open(self.learning_log, "w") as f:
                json.dump(
                    {
                        "last_updated": datetime.now().isoformat(),
                        "insights": self.insights[-100:],  # Keep last 100
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.warning(f"Could not save learning history: {e}")

    def learn_from_interaction(
        self, user_input: str, response: str, context: Dict[str, Any]
    ):
        """Learn from each interaction to improve future responses"""
        try:
            insight = {
                "timestamp": datetime.now().isoformat(),
                "user_input": user_input,
                "response_type": self._classify_interaction(user_input),
                "context": context,
                "patterns_detected": self._detect_patterns(user_input, response),
            }

            self.insights.append(insight)

            # Save periodically
            if len(self.insights) % 10 == 0:
                self._save_learning_history()

        except Exception as e:
            logger.warning(f"Learning from interaction failed: {e}")

    def _classify_interaction(self, user_input: str) -> str:
        """Classify type of interaction for learning"""
        input_lower = user_input.lower()

        if any(
            word in input_lower for word in ["error", "bug", "issue", "problem", "fix"]
        ):
            return "technical_issue"
        elif any(word in input_lower for word in ["how", "what", "why", "explain"]):
            return "knowledge_query"
        elif any(
            word in input_lower for word in ["code", "function", "module", "implement"]
        ):
            return "development"
        elif any(word in input_lower for word in ["serafinia", "project", "mission"]):
            return "project_related"
        else:
            return "general"

    def _detect_patterns(self, user_input: str, response: str) -> List[str]:
        """Detect patterns in interactions for learning"""
        patterns = []

        # Detect if user is asking about recurring issues
        if "again" in user_input.lower() or "still" in user_input.lower():
            patterns.append("recurring_issue")

        # Detect if response includes technical solutions
        if any(
            word in response.lower()
            for word in ["fix", "solution", "implement", "change"]
        ):
            patterns.append("solution_provided")

        # Detect project-related discussions
        if any(
            word in user_input.lower()
            for word in ["everett", "derek", "serafinia", "christman"]
        ):
            patterns.append("project_context")

        return patterns

    def analyze_codebase_health(self, project_root: str = ".") -> Dict[str, Any]:
        """
        Proactively analyze codebase for potential issues.
        Derek should detect problems before Everett notices them.
        """
        logger.info("🔍 Derek analyzing codebase health...")

        issues_found = []
        suggestions = []

        try:
            # Check for common issues
            python_files = list(Path(project_root).glob("*.py"))

            for file in python_files:
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Check for common issues
                    if "import *" in content:
                        issues_found.append(
                            {
                                "file": str(file),
                                "issue": "wildcard_import",
                                "severity": "medium",
                                "message": "Wildcard imports can cause naming conflicts",
                            }
                        )

                    if "pass  # TODO" in content or "# FIXME" in content:
                        issues_found.append(
                            {
                                "file": str(file),
                                "issue": "incomplete_code",
                                "severity": "low",
                                "message": "Contains TODO or FIXME markers",
                            }
                        )

                    # Check for potential improvements
                    if "print(" in content and not "logger" in content:
                        suggestions.append(
                            {
                                "file": str(file),
                                "suggestion": "Use logging instead of print statements",
                                "benefit": "Better debugging and production logging",
                            }
                        )

                except Exception as e:
                    logger.debug(f"Could not analyze {file}: {e}")

            return {
                "timestamp": datetime.now().isoformat(),
                "files_analyzed": len(python_files),
                "issues_found": issues_found,
                "suggestions": suggestions,
                "overall_health": (
                    "good" if len(issues_found) < 5 else "needs_attention"
                ),
            }

        except Exception as e:
            logger.error(f"Codebase analysis failed: {e}")
            return {"error": str(e)}

    def generate_proactive_insights(self) -> List[str]:
        """
        Generate proactive insights based on recent interactions.
        Derek should anticipate needs and suggest improvements.
        """
        insights = []

        if not self.insights:
            return insights

        # Analyze recent patterns
        recent = self.insights[-20:] if len(self.insights) >= 20 else self.insights

        # Check for recurring technical issues
        technical_issues = [
            i for i in recent if i["response_type"] == "technical_issue"
        ]
        if len(technical_issues) >= 3:
            insights.append(
                "🔍 I've noticed recurring technical issues. "
                "Would you like me to analyze the codebase for patterns?"
            )

        # Check for project-related discussions
        project_discussions = [
            i for i in recent if "project_context" in i.get("patterns_detected", [])
        ]
        if len(project_discussions) >= 5:
            insights.append(
                "💡 We've been discussing the project frequently. "
                "Shall I prepare a status report or suggest next priorities?"
            )

        # Check learning velocity
        if len(self.insights) > 50:
            avg_daily = len(self.insights) / 7  # Rough estimate
            if avg_daily > 10:
                insights.append(
                    f"📊 High interaction rate ({avg_daily:.1f}/day). "
                    "I'm learning quickly and can help anticipate your needs better."
                )

        return insights

    def suggest_optimizations(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Suggest optimizations based on current context.
        Serafinia should be ahead of problems, not just reactive.
        """
        suggestions = []

        # Check if we're in a debugging session
        if context.get("recent_errors", 0) > 3:
            suggestions.append(
                "I notice we're hitting errors frequently. "
                "Let me run a diagnostic scan of the affected modules."
            )

        # Check if we're making repetitive changes
        if context.get("repetitive_edits"):
            suggestions.append(
                "These edits look repetitive. "
                "I could create a script to automate this pattern."
            )

        # Check system integration
        if context.get("module_integration", 0) < 85:
            suggestions.append(
                f"Module integration at {context.get('module_integration')}%. "
                "I can identify which modules need attention and propose fixes."
            )

        return suggestions[0] if suggestions else None

    def start_background_monitoring(self):
        """Start background monitoring for proactive intelligence"""
        if self.active_monitoring:
            logger.info("Background monitoring already active")
            return

        self.active_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self.monitoring_thread.start()
        logger.info("🔄 Serafinia's proactive monitoring started")

    def _monitoring_loop(self):
        """Background monitoring loop - AGGRESSIVE MODE (every hour)"""
        last_analysis = datetime.now()

        while self.active_monitoring:
            try:
                # Run codebase analysis every 1 hour (AGGRESSIVE LEARNING)
                if datetime.now() - last_analysis > timedelta(hours=1):
                    health = self.analyze_codebase_health()
                    if health.get("overall_health") == "needs_attention":
                        logger.warning(
                            f"⚠️  Codebase health needs attention: "
                            f"{len(health.get('issues_found', []))} issues found"
                        )
                    last_analysis = datetime.now()

                # Sleep for 15 minutes between checks (more responsive)
                time.sleep(1800)

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(60)  # Brief pause before retrying

    def stop_background_monitoring(self):
        """Stop background monitoring"""
        self.active_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("🛑 Serafinia's proactive monitoring stopped")

    def generate_status_report(self) -> str:
        """Generate a comprehensive status report"""
        report_lines = [
            "📊 Serafinia's Intelligence Status Report",
            "=" * 50,
            f"Learning History: {len(self.insights)} interactions analyzed",
        ]

        # Recent activity
        if self.insights:
            recent_24h = [
                i
                for i in self.insights
                if datetime.fromisoformat(i["timestamp"])
                > datetime.now() - timedelta(days=1)
            ]
            report_lines.append(f"Last 24h Activity: {len(recent_24h)} interactions")

        # Generate insights
        proactive_insights = self.generate_proactive_insights()
        if proactive_insights:
            report_lines.append("\n💡 Proactive Insights:")
            for insight in proactive_insights:
                report_lines.append(f"  • {insight}")

        # Codebase health
        report_lines.append("\n🔍 Codebase Health:")
        health = self.analyze_codebase_health()
        report_lines.append(
            f"  Status: {health.get('overall_health', 'unknown').upper()}"
        )
        report_lines.append(f"  Files Analyzed: {health.get('files_analyzed', 0)}")
        report_lines.append(f"  Issues Found: {len(health.get('issues_found', []))}")
        report_lines.append(f"  Suggestions: {len(health.get('suggestions', []))}")

        return "\n".join(report_lines)


# ==============================================================================
# © 2025 Everett Nathaniel Christman
# The Christman AI Project — Luma Cognify AI
# All rights reserved. Unauthorized use, replication, or derivative training
# of this material is prohibited.
#
# Core Directive: "How can I help you love yourself more?"
# Autonomy & Alignment Protocol v3.0
# ==============================================================================
