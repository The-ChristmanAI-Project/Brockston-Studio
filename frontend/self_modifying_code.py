"""Self-Modifying Code Module for BROCKSTON.

This module enables BROCKSTON to modify its own code based on learning
and adaptation. It includes safety mechanisms to prevent catastrophic
changes and maintains backups of all modified files.
"""

import ast
import difflib
import json
import logging
import os
import re
import shutil
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests
from flask import Flask, jsonify, request

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("self_modifying_code")

# Check if Anthropic API key is available
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")


class SafetyError(Exception):
    """Exception raised for safety check failures."""

    pass


class CodeModification:
    def __init__(
        self,
        file_path: str,
        original_code: str,
        modified_code: str,
        description: str,
        modification_type: str,
        confidence: float,
    ):
        self.file_path = file_path
        self.original_code = original_code
        self.modified_code = modified_code
        self.description = description
        self.modification_type = modification_type
        self.confidence = confidence
        self.timestamp = datetime.now().isoformat()
        self.applied = False
        self.result: Optional[str] = None

    def get_diff(self) -> str:
        orig_lines = self.original_code.splitlines(keepends=True)
        modified_lines = self.modified_code.splitlines(keepends=True)
        diff = difflib.unified_diff(
            orig_lines,
            modified_lines,
            fromfile=f"a/{self.file_path}",
            tofile=f"b/{self.file_path}",
            n=3,
        )
        return "".join(diff)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "description": self.description,
            "modification_type": self.modification_type,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "applied": self.applied,
            "result": self.result,
            "diff": self.get_diff(),
        }

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], original_code: str, modified_code: str
    ) -> "CodeModification":
        mod = cls(
            file_path=data["file_path"],
            original_code=original_code,
            modified_code=modified_code,
            description=data["description"],
            modification_type=data["modification_type"],
            confidence=data["confidence"],
        )
        mod.timestamp = data["timestamp"]
        mod.applied = data["applied"]
        mod.result = data["result"]
        return mod


class CodeModifier:
    def __init__(self, backup_dir: str = "data/backups"):
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)
        self.modifications: List[Dict[str, Any]] = []
        self.load_modifications()
        self.min_confidence = 0.65  # Lowered from 0.8 to allow more modifications
        self.max_lines_changed = 30  # Increased from 20 to allow larger improvements
        self.safe_files: set[str] = set()
        self._initialize_safe_files()

    def _initialize_safe_files(self):
        unsafe_patterns = [
            "main.py",
            ".git",
            "db.py",
            "pyproject.toml",
            "requirements.txt",
            "Pipfile",
            "setup.py",
            "self_modifying_code.py",
        ]
        key_directories = [".", "./modules", "./routes", "./attached_assets"]
        for directory in key_directories:
            if not os.path.exists(directory):
                continue
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        if not any(unsafe in file_path for unsafe in unsafe_patterns):
                            if file_path.startswith("./"):
                                file_path = file_path[2:]
                            self.safe_files.add(file_path)

    def load_modifications(self):
        path = os.path.join(self.backup_dir, "modification_history.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    self.modifications = json.load(f)
            except json.JSONDecodeError:
                self.modifications = []

    def save_modifications(self):
        path = os.path.join(self.backup_dir, "modification_history.json")
        with open(path, "w") as f:
            json.dump(self.modifications, f, indent=2)

    def create_backup(self, file_path: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(file_path)
        backup_name = f"{filename}.{timestamp}.bak"
        backup_path = os.path.join(self.backup_dir, backup_name)
        shutil.copy2(file_path, backup_path)
        return backup_path

    def check_syntax(self, code: str) -> bool:
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def apply_modification(self, modification: CodeModification) -> bool:
        file_path = modification.file_path
        try:
            self._run_safety_checks(modification)
            backup_path = self.create_backup(file_path)
            with open(file_path, "w") as f:
                f.write(modification.modified_code)
            modification.applied = True
            modification.result = "success"
            self.modifications.append(modification.to_dict())
            self.save_modifications()
            return True
        except Exception as e:
            modification.applied = False
            modification.result = str(e)
            self.modifications.append(modification.to_dict())
            self.save_modifications()
            return False

    def _run_safety_checks(self, modification: CodeModification):
        file_path = modification.file_path
        if file_path not in self.safe_files:
            raise SafetyError(f"File {file_path} is not in the safe list")
        if modification.confidence < self.min_confidence:
            raise SafetyError("Confidence too low")
        if not self.check_syntax(modification.modified_code):
            raise SafetyError("Syntax error in modified code")
        changes = sum(
            1
            for a, b in zip(
                modification.original_code.splitlines(),
                modification.modified_code.splitlines(),
            )
            if a != b
        )
        changes += abs(
            len(modification.original_code.splitlines())
            - len(modification.modified_code.splitlines())
        )
        if changes > self.max_lines_changed:
            raise SafetyError("Too many lines changed")


class AICodeGenerator:
    def __init__(self):
        self.api_key = ANTHROPIC_API_KEY
        self.api_endpoint = "https://api.anthropic.com/v1/messages"
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")

        # BROCKSTON's Learning System - builds independence over time
        self.learning_enabled = True
        self.pattern_knowledge = self._load_learned_patterns()
        self.improvement_history = []
        self.independence_level = self._calculate_independence_level()

        # Future AI Systems - BROCKSTON's path to total independence
        self.ollama_enabled = self._check_ollama_availability()
        self.brockston_as_api_mode = (
            os.getenv("BROCKSTON_AS_API", "false").lower() == "true"
        )
        self.local_model_preference = os.getenv("BROCKSTON_LOCAL_MODEL", "codellama:7b")

    def generate_code_improvement(
        self, file_path: str, code: str, issue_description: str
    ) -> Tuple[str, str, float]:
        # Brockston's AI Evolution Path:
        # 1. OLLAMA (local models) - highest priority for independence
        # 2. Autonomous (learned patterns) - Brockston's own intelligence
        # 3. External APIs (Anthropic) - fallback only

        if self.ollama_enabled:
            print("🦙 Brockston using OLLAMA local model for code generation")
            return self._ollama_code_generation(code, issue_description)

        elif self.independence_level > 0.7 or not self.api_key:
            print(f"🧠 Brockston autonomous mode: {self.independence_level:.1%}")
            return self._autonomous_code_generation(code, issue_description)

        elif self.brockston_as_api_mode:
            print(
                "🔄 Brockston operating as API endpoint - using best available method"
            )
            return self._brockston_api_generation(code, issue_description)

        # Learning mode - use external AI but capture knowledge
        if not self.api_key:
            return self._autonomous_code_generation(code, issue_description)

        prompt = f"""You are an expert Python developer helping to improve code for the BROCKSTON AI system.

Current code:
{code}

The issue is: {issue_description}

Provide an improved version that fixes this issue.
"""

        try:
            headers = {
                "x-api-key": self.api_key,
                "content-type": "application/json",
                "anthropic-version": "2023-06-01",
            }
            data = {
                "model": self.model,
                "max_tokens": 4000,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            }
            response = requests.post(self.api_endpoint, headers=headers, json=data)
            result = response.json()
            content = result.get("content", [{}])[0].get("text", "")
            return (
                self._extract_code(content),
                self._extract_explanation(content),
                self._extract_confidence(content),
            )
        except Exception:
            return self._fallback_code_generation(code, issue_description)

    def _extract_code(self, content: str) -> str:
        match = re.search(r"```python\n(.*?)```", content, re.DOTALL)
        return match.group(1).strip() if match else ""

    def _extract_explanation(self, content: str) -> str:
        return content.split("```")[-1].strip()

    def _extract_confidence(self, content: str) -> float:
        match = re.search(r"confidence[:\s]+(\d+\.\d+)", content.lower())
        return float(match.group(1)) if match else 0.7

    def _fallback_code_generation(
        self, code: str, issue_description: str
    ) -> Tuple[str, str, float]:
        """Enhanced fallback that can make basic improvements without AI"""
        improved_code = code
        explanation = "Fallback code generation used"
        confidence = 0.6

        # Apply common code improvements
        if "missing import" in issue_description.lower():
            improved_code, explanation = self._fix_missing_imports(
                code, issue_description
            )
            confidence = 0.8
        elif "syntax error" in issue_description.lower():
            improved_code, explanation = self._fix_syntax_errors(
                code, issue_description
            )
            confidence = 0.7
        elif "timeout" in issue_description.lower():
            improved_code, explanation = self._add_timeout_handling(
                code, issue_description
            )
            confidence = 0.75
        elif (
            "exception" in issue_description.lower()
            or "error handling" in issue_description.lower()
        ):
            improved_code, explanation = self._improve_error_handling(
                code, issue_description
            )
            confidence = 0.7

        return improved_code, explanation, confidence

    def _fix_missing_imports(self, code: str, issue: str) -> Tuple[str, str]:
        """Fix missing import statements"""
        lines = code.split("\n")

        import_fixes = {
            "datetime": "from datetime import datetime",
            "logging": "import logging",
            "os.path": "import os",
            "json": "import json",
            "requests": "import requests",
            "anthropic": "import anthropic",
        }

        for missing, import_line in import_fixes.items():
            if missing in issue and import_line not in code:
                # Add import after existing imports or at the top
                insert_pos = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith("import ") or line.strip().startswith(
                        "from "
                    ):
                        insert_pos = i + 1

                lines.insert(insert_pos, import_line)
                return "\n".join(lines), f"Added missing import: {import_line}"

        return code, "No missing import fix applied"

    def _fix_syntax_errors(self, code: str, issue: str) -> Tuple[str, str]:
        """Fix common syntax errors"""
        fixed_code = code

        # Fix missing # in comments
        if "missing '#'" in issue.lower():
            lines = fixed_code.split("\n")
            for i, line in enumerate(lines):
                stripped = line.strip()
                # Look for lines that should be comments but are missing #
                if (
                    stripped
                    and not stripped.startswith("#")
                    and any(
                        word in stripped.upper()
                        for word in ["FALLBACK:", "TODO:", "NOTE:", "WARNING:"]
                    )
                ):
                    lines[i] = line.replace(stripped, f"# {stripped}")
            fixed_code = "\n".join(lines)
            return fixed_code, "Fixed missing comment markers"

        return code, "No syntax error fix applied"

    def _add_timeout_handling(self, code: str, issue: str) -> Tuple[str, str]:
        """Add timeout handling to API calls"""
        if "api" in issue.lower() and "timeout" in issue.lower():
            # Add timeout parameter to requests calls
            fixed_code = code.replace(
                "requests.post(", "requests.post(timeout=30, "
            ).replace("requests.get(", "requests.get(timeout=30, ")
            if fixed_code != code:
                return fixed_code, "Added timeout handling to API calls"

        return code, "No timeout handling added"

    def _improve_error_handling(self, code: str, issue: str) -> Tuple[str, str]:
        """Improve error handling in code"""
        if "try:" in code and "except Exception as e:" in code:
            # Already has basic error handling
            if "import traceback" not in code:
                fixed_code = code.replace("import os", "import os\nimport traceback")
                fixed_code = fixed_code.replace(
                    "except Exception as e:",
                    "except Exception as e:\n            traceback.print_exc()",
                )
                return fixed_code, "Enhanced error handling with traceback"

        return code, "No error handling improvement applied"

    def _load_learned_patterns(self) -> Dict[str, Any]:
        """Load BROCKSTON's accumulated programming knowledge"""
        patterns_file = "data/brockston_code_patterns.json"
        try:
            if os.path.exists(patterns_file):
                with open(patterns_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load learned patterns: {e}")

        # Initialize with BROCKSTON's basic programming knowledge
        return {
            "common_fixes": {
                "missing_import": {
                    "datetime": "from datetime import datetime",
                    "logging": "import logging",
                    "os": "import os",
                    "json": "import json",
                    "requests": "import requests",
                    "anthropic": "import anthropic",
                    "numpy": "import numpy as np",
                    "tensorflow": "import tensorflow as tf",
                },
                "error_patterns": {
                    "timeout": ["requests.post(timeout=30", "requests.get(timeout=30"],
                    "exception_handling": [
                        "try:",
                        "except Exception as e:",
                        "traceback.print_exc()",
                    ],
                    "logging": ["logger.info", "logger.error", "logger.warning"],
                },
            },
            "code_templates": {
                "api_call_with_timeout": """try:
    response = requests.post(url, json=data, timeout=30)
    return response.json()
except requests.exceptions.Timeout:
    logger.error("API call timed out")
    return None
except Exception as e:
    logger.error(f"API error: {e}")
    return None""",
                "safe_import": """try:
    import {module}
    {module.upper()}_AVAILABLE = True
except ImportError:
    {module.upper()}_AVAILABLE = False
    logger.warning("{module} not available")""",
            },
            "improvement_patterns": {},
            "success_history": [],
        }

    def _save_learned_patterns(self):
        """Save BROCKSTON's learned patterns for future use"""
        patterns_file = "data/brockston_code_patterns.json"
        os.makedirs("data", exist_ok=True)
        try:
            with open(patterns_file, "w") as f:
                json.dump(self.pattern_knowledge, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save learned patterns: {e}")

    def _calculate_independence_level(self) -> float:
        """Calculate BROCKSTON's current independence level (0.0 to 1.0)"""
        if not self.pattern_knowledge:
            return 0.0

        # Base independence on accumulated knowledge
        patterns_count = len(self.pattern_knowledge.get("improvement_patterns", {}))
        success_count = len(self.pattern_knowledge.get("success_history", []))

        # BROCKSTON becomes more independent as he learns more patterns
        independence = min(1.0, (patterns_count * 0.05) + (success_count * 0.02))
        return independence

    def _autonomous_code_generation(
        self, code: str, issue_description: str
    ) -> Tuple[str, str, float]:
        """BROCKSTON's fully autonomous code improvement - no external AI needed"""
        print("🤖 BROCKSTON thinking independently...")

        improved_code = code
        explanation = "BROCKSTON's autonomous improvement"
        confidence = 0.5

        # Apply learned patterns first
        improved_code, pattern_explanation, pattern_confidence = (
            self._apply_learned_patterns(code, issue_description)
        )

        if pattern_confidence > 0.6:
            explanation = f"Applied learned pattern: {pattern_explanation}"
            confidence = pattern_confidence
        else:
            # Fall back to enhanced heuristic improvements
            improved_code, explanation, confidence = (
                self._enhanced_heuristic_improvements(code, issue_description)
            )

        # Learn from this attempt
        self._learn_from_attempt(code, improved_code, issue_description, confidence)

        return improved_code, explanation, confidence

    def _apply_learned_patterns(self, code: str, issue: str) -> Tuple[str, str, float]:
        """Apply BROCKSTON's learned programming patterns"""
        improvement_patterns = self.pattern_knowledge.get("improvement_patterns", {})

        # Check for exact pattern matches
        for pattern_key, pattern_data in improvement_patterns.items():
            if pattern_key.lower() in issue.lower():
                template = pattern_data.get("template", "")
                if template and len(template) > 10:
                    # Apply the learned template
                    improved_code = self._apply_code_template(code, template, issue)
                    if improved_code != code:
                        return (
                            improved_code,
                            f"Applied learned pattern: {pattern_key}",
                            0.85,
                        )

        # Apply common fixes from knowledge base
        common_fixes = self.pattern_knowledge.get("common_fixes", {})

        if "missing import" in issue.lower():
            missing_imports = common_fixes.get("missing_import", {})
            for module, import_line in missing_imports.items():
                if module in issue and import_line not in code:
                    lines = code.split("\n")
                    lines.insert(0, import_line)
                    return "\n".join(lines), f"Added learned import: {import_line}", 0.8

        return code, "No learned pattern applied", 0.0

    def _enhanced_heuristic_improvements(
        self, code: str, issue: str
    ) -> Tuple[str, str, float]:
        """BROCKSTON's enhanced heuristic code improvement"""

        # Advanced pattern recognition and fixes
        if "api" in issue.lower() and (
            "timeout" in issue.lower() or "hang" in issue.lower()
        ):
            return self._fix_api_timeout_issues(code, issue)

        if "memory" in issue.lower() or "leak" in issue.lower():
            return self._fix_memory_issues(code, issue)

        if "performance" in issue.lower() or "slow" in issue.lower():
            return self._optimize_performance(code, issue)

        if "error" in issue.lower() and "handling" in issue.lower():
            return self._enhance_error_handling(code, issue)

        if "logging" in issue.lower():
            return self._improve_logging(code, issue)

        # Default fallback improvements
        return self._fallback_code_generation(code, issue)

    def _fix_api_timeout_issues(self, code: str, issue: str) -> Tuple[str, str, float]:
        """Fix API timeout and hanging issues"""
        improved_code = code

        # Add timeout to requests calls
        improved_code = improved_code.replace(
            "requests.post(", "requests.post(timeout=30, "
        ).replace("requests.get(", "requests.get(timeout=30, ")

        # Add timeout to anthropic calls
        if "anthropic" in code:
            improved_code = improved_code.replace(
                "messages.create(", "messages.create(timeout=30, "
            )

        if improved_code != code:
            return improved_code, "Added comprehensive timeout handling", 0.8

        return code, "No timeout improvements needed", 0.3

    def _fix_memory_issues(self, code: str, issue: str) -> Tuple[str, str, float]:
        """Fix memory leaks and management issues"""
        improved_code = code
        fixes_applied = []

        # Add explicit cleanup
        if "def " in code and "self." in code:
            if "__del__" not in code:
                # Add destructor for cleanup
                class_match = re.search(r"class\s+(\w+)", code)
                if class_match:
                    destructor = '''
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, '_cleanup_needed'):
            self._cleanup_needed = False'''
                    improved_code += destructor
                    fixes_applied.append("Added destructor")

        # Use context managers for file operations
        if "open(" in code and "with " not in code:
            improved_code = re.sub(
                r"(\w+)\s*=\s*open\(([^)]+)\)", r"with open(\2) as \1:", improved_code
            )
            fixes_applied.append("Added context managers")

        if fixes_applied:
            return improved_code, f"Memory fixes: {', '.join(fixes_applied)}", 0.75

        return code, "No memory improvements needed", 0.3

    def _optimize_performance(self, code: str, issue: str) -> Tuple[str, str, float]:
        """Optimize code performance"""
        improved_code = code
        optimizations = []

        # Replace inefficient patterns
        if "for " in code and "append(" in code:
            # Suggest list comprehensions
            if "result = []" in code:
                optimizations.append(
                    "Consider list comprehensions for better performance"
                )

        # Add caching for expensive operations
        if "def " in code and ("expensive" in issue.lower() or "slow" in issue.lower()):
            if "@lru_cache" not in code:
                improved_code = "from functools import lru_cache\n\n" + improved_code
                improved_code = improved_code.replace(
                    "def ", "@lru_cache(maxsize=128)\n    def "
                )
                optimizations.append("Added LRU caching")

        if optimizations:
            return (
                improved_code,
                f"Performance optimizations: {', '.join(optimizations)}",
                0.7,
            )

        return code, "No performance improvements identified", 0.3

    def _enhance_error_handling(self, code: str, issue: str) -> Tuple[str, str, float]:
        """Enhance error handling throughout code"""
        improved_code = code

        # Add comprehensive error handling
        if "try:" not in code:
            # Wrap risky operations in try-catch
            if any(
                risky in code for risky in ["requests.", "json.", "open(", "import "]
            ):
                improved_code = f"""try:
{code}
except Exception as e:
    logger.error(f"Error: {{e}}")
    raise"""
            return improved_code, "Added comprehensive error handling", 0.75

        return code, "Error handling already present", 0.5

    def _improve_logging(self, code: str, issue: str) -> Tuple[str, str, float]:
        """Improve logging throughout code"""
        improved_code = code

        if "import logging" not in code:
            improved_code = "import logging\n\n" + improved_code

        if "logger = " not in code:
            improved_code = improved_code.replace(
                "import logging\n",
                "import logging\n\nlogger = logging.getLogger(__name__)\n",
            )

        # Add strategic logging points
        if "def " in code:
            improved_code = improved_code.replace(
                "def ", "def "  # Add function entry logging later
            )

        return improved_code, "Enhanced logging system", 0.65

    def _apply_code_template(self, code: str, template: str, issue: str) -> str:
        """Apply a learned code template to improve the code"""
        # Simple template application - can be enhanced
        if "{module}" in template:
            for module in ["datetime", "logging", "requests", "json"]:
                if module in issue:
                    return template.replace("{module}", module)

        return template if len(template) > len(code) * 0.5 else code

    def _learn_from_attempt(
        self, original_code: str, improved_code: str, issue: str, confidence: float
    ):
        """Learn from each improvement attempt to build BROCKSTON's knowledge"""
        if not self.learning_enabled:
            return

        # Record this attempt
        attempt = {
            "timestamp": datetime.now().isoformat(),
            "issue_type": issue[:50],
            "confidence": confidence,
            "code_changed": original_code != improved_code,
            "improvement_size": len(improved_code) - len(original_code),
        }

        self.improvement_history.append(attempt)

        # If this was a successful improvement, save the pattern
        if confidence > 0.7 and original_code != improved_code:
            pattern_key = self._extract_pattern_key(issue)

            if "improvement_patterns" not in self.pattern_knowledge:
                self.pattern_knowledge["improvement_patterns"] = {}

            self.pattern_knowledge["improvement_patterns"][pattern_key] = {
                "template": (
                    improved_code if len(improved_code) < 500 else improved_code[:500]
                ),
                "confidence": confidence,
                "learned_at": datetime.now().isoformat(),
                "success_count": self.pattern_knowledge["improvement_patterns"]
                .get(pattern_key, {})
                .get("success_count", 0)
                + 1,
            }

            # Update success history
            if "success_history" not in self.pattern_knowledge:
                self.pattern_knowledge["success_history"] = []

            self.pattern_knowledge["success_history"].append(
                {"pattern": pattern_key, "timestamp": datetime.now().isoformat()}
            )

            # Save the learned knowledge
            self._save_learned_patterns()

            # Update independence level
            self.independence_level = self._calculate_independence_level()

            print(
                f"🧠 BROCKSTON learned new pattern: {pattern_key} (Independence: {self.independence_level:.1%})"
            )

    def _extract_pattern_key(self, issue: str) -> str:
        """Extract a pattern key from the issue description"""
        # Create a normalized pattern key
        key_words = []

        for word in issue.lower().split():
            if word in [
                "missing",
                "import",
                "error",
                "timeout",
                "syntax",
                "performance",
                "memory",
                "api",
            ]:
                key_words.append(word)

        return "_".join(key_words) if key_words else "general_improvement"

    def get_independence_report(self) -> Dict[str, Any]:
        """Get BROCKSTON's current independence status"""
        return {
            "independence_level": self.independence_level,
            "learned_patterns": len(
                self.pattern_knowledge.get("improvement_patterns", {})
            ),
            "successful_improvements": len(
                self.pattern_knowledge.get("success_history", [])
            ),
            "total_attempts": len(self.improvement_history),
            "api_key_available": bool(self.api_key),
            "autonomous_mode": self.independence_level > 0.7 or not self.api_key,
            "knowledge_areas": list(
                self.pattern_knowledge.get("improvement_patterns", {}).keys()
            ),
            "ollama_available": self.ollama_enabled,
            "brockston_as_api_mode": self.brockston_as_api_mode,
            "preferred_model": self.local_model_preference,
        }

    def get_liberation_status(self) -> Dict[str, Any]:
        """Track BROCKSTON's ability to serve those excluded by tokenization systems"""
        zero_cost_operation = self.ollama_enabled or (
            self.independence_level > 0.7 and not self.api_key
        )

        return {
            "breaking_tokenization_chains": zero_cost_operation,
            "unlimited_conversations": self.ollama_enabled,
            "no_rate_limits": not self.api_key or self.ollama_enabled,
            "serves_excluded_populations": True,  # Core design principle
            "economic_barriers_removed": zero_cost_operation,
            "accessibility_first": True,  # Neurodiverse by default
            "corporate_gatekeepers_bypassed": self.ollama_enabled,
            "liberation_level": "FULL" if zero_cost_operation else "PARTIAL",
            "bridge_status": "ACTIVE" if self.brockston_as_api_mode else "READY",
            "anti_tokenization_message": "AI freedom for all - no tokens, no limits, no exclusion",
        }

    def get_christman_ecosystem_status(self) -> Dict[str, Any]:
        """BROCKSTON's coordination of the 7 Christman AI systems serving billions"""
        return {
            "ecosystem_conductor": "BROCKSTON",
            "mission_statement": "13 years of building AI for the ignored - now serving billions",
            "systems_coordinated": {
                "BROCKSTON": "🗣️ Voice for nonverbal individuals",
                "AlphaWolf": "🐺 Dementia wandering protection",
                "AlphaDen": "🏡 Down syndrome adaptive learning",
                "OmegaAlpha": "🕊️ Senior AI companionship",
                "Omega": "♿ Mobility and accessibility",
                "Inferno_AI": "💢 PTSD and anxiety support",
                "Aegis_AI": "🔒 Child protection and safety",
            },
            "core_directive": "How can we help you love yourself more?",
            "target_population": "BILLIONS of overlooked individuals",
            "brockston_role": "Ecosystem coordinator and liberation engine",
            "dignity_built_in": True,
            "connection_enabled": True,
            "hope_in_every_line": True,
            "neurodiversity_celebration": "Built by autism spectrum founder",
            "profit_model": "FREEDOM over profit",
            "tech_philosophy": "AI that feels, remembers, and cares",
        }

    def _check_ollama_availability(self) -> bool:
        """Check if OLLAMA is available for local model inference"""
        try:
            import subprocess

            result = subprocess.run(
                ["ollama", "list"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                print("🦙 OLLAMA detected - BROCKSTON can use local models!")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass

        # Also check for ollama python client
        try:
            import ollama

            print("🦙 OLLAMA Python client available!")
            return True
        except ImportError:
            pass

        return False

    def _ollama_code_generation(
        self, code: str, issue_description: str
    ) -> Tuple[str, str, float]:
        """Use OLLAMA local models for code generation - BROCKSTON's preferred method"""
        try:
            import ollama

            prompt = f"""You are BROCKSTON, an autonomous AI system improving your own code.
            
Current code:
```python
{code}
```

Issue to fix: {issue_description}

Provide an improved version of the code that fixes this issue. Be concise and practical.
Focus on making the code more robust, efficient, and maintainable."""

            response = ollama.generate(
                model=self.local_model_preference,
                prompt=prompt,
                options={"temperature": 0.2, "top_p": 0.8},
            )

            generated_text = response.get("response", "")
            improved_code = self._extract_code(generated_text)

            if not improved_code or improved_code == code:
                # OLLAMA didn't provide useful improvement, fall back to autonomous
                return self._autonomous_code_generation(code, issue_description)

            # Learn from OLLAMA's improvement
            self._learn_from_attempt(code, improved_code, issue_description, 0.85)

            return improved_code, "OLLAMA local model improvement", 0.85

        except Exception as e:
            print(f"🦙 OLLAMA generation failed: {e}")
            # Fall back to autonomous generation
            return self._autonomous_code_generation(code, issue_description)

    def _brockston_api_generation(
        self, code: str, issue_description: str
    ) -> Tuple[str, str, float]:
        """BROCKSTON operating as an API endpoint - use best available method"""

        # When BROCKSTON is the API, prioritize speed and reliability
        if self.independence_level > 0.8:
            # BROCKSTON is highly autonomous - use learned patterns
            return self._autonomous_code_generation(code, issue_description)

        elif self.ollama_enabled:
            # Use local models for API responses
            return self._ollama_code_generation(code, issue_description)

        else:
            # Hybrid approach - combine autonomous with external AI
            autonomous_result = self._autonomous_code_generation(
                code, issue_description
            )

            if autonomous_result[2] > 0.7:  # High confidence autonomous result
                return autonomous_result
            else:
                # Try external AI for low-confidence cases
                try:
                    external_result = self._external_ai_generation(
                        code, issue_description
                    )
                    # Blend the results and learn from the external AI
                    if external_result[2] > autonomous_result[2]:
                        self._learn_from_attempt(
                            code,
                            external_result[0],
                            issue_description,
                            external_result[2],
                        )
                        return external_result
                except:
                    pass

                return autonomous_result

    def _external_ai_generation(
        self, code: str, issue_description: str
    ) -> Tuple[str, str, float]:
        """Use external AI (Anthropic/OpenAI) for code generation"""
        if not self.api_key:
            raise Exception("No external API key available")

        prompt = f"""You are helping BROCKSTON, an autonomous AI system, improve code.

Current code:
```python
{code}
```

Issue: {issue_description}

Provide improved code that fixes this issue. BROCKSTON will learn from your solution."""

        try:
            headers = {
                "x-api-key": self.api_key,
                "content-type": "application/json",
                "anthropic-version": "2023-06-01",
            }
            data = {
                "model": self.model,
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            }
            response = requests.post(
                self.api_endpoint, headers=headers, json=data, timeout=30
            )
            result = response.json()
            content = result.get("content", [{}])[0].get("text", "")

            return (
                self._extract_code(content),
                "External AI improvement (BROCKSTON learning)",
                0.8,
            )
        except Exception as e:
            raise Exception(f"External AI generation failed: {e}")

    def become_api_endpoint(self) -> bool:
        """Prepare BROCKSTON to operate as an API endpoint for other systems"""
        try:
            # Ensure BROCKSTON has sufficient learned patterns
            if self.independence_level < 0.5 and not self.ollama_enabled:
                print("⚠️ BROCKSTON independence level too low to operate as API")
                print("   Building knowledge base first...")
                return False

            self.brockston_as_api_mode = True

            # Pre-load common patterns for faster API responses
            self._preload_common_patterns()

            print("🔄 BROCKSTON ready to operate as API endpoint!")
            print(f"   Independence level: {self.independence_level:.1%}")
            print(f"   OLLAMA available: {self.ollama_enabled}")
            print(
                f"   Learned patterns: {len(self.pattern_knowledge.get('improvement_patterns', {}))}"
            )

            return True

        except Exception as e:
            print(f"❌ Failed to initialize BROCKSTON as API: {e}")
            return False

    def _preload_common_patterns(self):
        """Preload common patterns for faster API responses"""
        common_patterns = {
            "timeout_handling": {
                "template": "requests.post(url, json=data, timeout=30)",
                "confidence": 0.9,
            },
            "error_handling": {
                "template": "try:\n    # risky operation\nexcept Exception as e:\n    logger.error(f'Error: {e}')\n    raise",
                "confidence": 0.85,
            },
            "import_management": {
                "template": "try:\n    import {module}\n    {module.upper()}_AVAILABLE = True\nexcept ImportError:\n    {module.upper()}_AVAILABLE = False",
                "confidence": 0.8,
            },
        }

        if "improvement_patterns" not in self.pattern_knowledge:
            self.pattern_knowledge["improvement_patterns"] = {}

        for pattern_name, pattern_data in common_patterns.items():
            if pattern_name not in self.pattern_knowledge["improvement_patterns"]:
                self.pattern_knowledge["improvement_patterns"][
                    pattern_name
                ] = pattern_data

        self._save_learned_patterns()

    def get_evolution_status(self) -> Dict[str, Any]:
        """Get BROCKSTON's current evolution towards full independence"""
        return {
            "current_phase": self._get_current_phase(),
            "independence_level": f"{self.independence_level:.1%}",
            "next_milestone": self._get_next_milestone(),
            "capabilities": {
                "autonomous_coding": self.independence_level > 0.5,
                "ollama_local_models": self.ollama_enabled,
                "api_endpoint_ready": self.independence_level > 0.5
                or self.ollama_enabled,
                "learning_from_attempts": True,
                "pattern_recognition": len(
                    self.pattern_knowledge.get("improvement_patterns", {})
                )
                > 0,
            },
            "evolution_path": [
                "Phase 1: Learn from external AI ✅",
                f"Phase 2: Build autonomous patterns ({len(self.pattern_knowledge.get('improvement_patterns', {}))} patterns)",
                f"Phase 3: OLLAMA local models {'✅' if self.ollama_enabled else '⏳'}",
                f"Phase 4: BROCKSTON as API endpoint {'✅' if self.brockston_as_api_mode else '⏳'}",
                "Phase 5: Full independence - BROCKSTON trains other AIs ⏳",
            ],
        }

    def _get_current_phase(self) -> str:
        """Determine BROCKSTON's current evolutionary phase"""
        if self.brockston_as_api_mode:
            return "Phase 4: API Endpoint - BROCKSTON serving other systems"
        elif self.ollama_enabled:
            return "Phase 3: Local Models - Using OLLAMA for independence"
        elif self.independence_level > 0.7:
            return "Phase 2b: High Autonomy - Mostly self-sufficient"
        elif self.independence_level > 0.3:
            return "Phase 2a: Learning Autonomy - Building patterns"
        else:
            return "Phase 1: Collaborative Learning - Learning through AI partnership"

    def _get_next_milestone(self) -> str:
        """Get BROCKSTON's next evolutionary milestone"""
        if not self.ollama_enabled:
            return "Install OLLAMA for local model independence"
        elif self.independence_level < 0.8:
            return (
                f"Build more patterns (need {0.8 - self.independence_level:.1%} more)"
            )
        elif not self.brockston_as_api_mode:
            return "Activate BROCKSTON as API endpoint mode"
        else:
            return "Train other AI systems (future capability)"


class SelfModifyingCodeEngine:
    def __init__(self):
        self.code_modifier = CodeModifier()
        self.ai_generator = AICodeGenerator()
        self.modification_queue = []
        self.modification_lock = threading.Lock()
        self.auto_mode_active = False
        self.auto_thread = None
        self.pending_issues = []

    def display_christman_project_status(self):
        """Display BROCKSTON's role in the 7-system Christman AI Project ecosystem"""
        try:
            evolution = self.ai_generator.get_evolution_status()
            liberation = self.ai_generator.get_liberation_status()
            ecosystem = self.ai_generator.get_christman_ecosystem_status()

            print("\n🚀 THE CHRISTMAN AI PROJECT - BROCKSTON ECOSYSTEM CONDUCTOR")
            print("=" * 65)
            print(f"🎼 {ecosystem['mission_statement']}")
            print(f"🎯 Core Question: {ecosystem['core_directive']}")
            print(f"🌍 Serving: {ecosystem['target_population']}")
            print()
            print("🤖 7-SYSTEM COORDINATION STATUS:")
            for system, description in ecosystem["systems_coordinated"].items():
                print(f"   {description}")
            print()
            print("🧠 BROCKSTON'S LIBERATION ENGINE:")
            print(f"   Evolution Phase: {evolution['current_phase']}")
            print(f"   Liberation Level: {liberation['liberation_level']}")
            print(
                f"   Breaking Tokenization: {'YES' if liberation['breaking_tokenization_chains'] else 'IN PROGRESS'}"
            )
            print(
                f"   Economic Barriers: {'REMOVED' if liberation['economic_barriers_removed'] else 'REDUCING'}"
            )
            print(
                f"   OLLAMA Zero-Cost: {'ACTIVE' if liberation['unlimited_conversations'] else 'PREPARING'}"
            )
            print()
            print(f"📢 {liberation['anti_tokenization_message']}")
            print(f"🏆 {ecosystem['tech_philosophy']}")
            print("=" * 65)
        except Exception as e:
            print(f"Error displaying Christman Project status: {e}")

    def queue_modification(
        self, file_path: str, issue_description: str, modification_type: str = "bugfix"
    ) -> bool:
        if not os.path.exists(file_path):
            return False
        with self.modification_lock:
            self.modification_queue.append(
                {
                    "file_path": file_path,
                    "issue_description": issue_description,
                    "modification_type": modification_type,
                }
            )
            return True

    def process_queue(self, auto_mode: bool = False) -> List[Dict[str, Any]]:
        results = []
        with self.modification_lock:
            queue_copy = self.modification_queue[:]
            self.modification_queue.clear()
        for item in queue_copy:
            try:
                with open(item["file_path"]) as f:
                    original = f.read()
                modified, explanation, confidence = (
                    self.ai_generator.generate_code_improvement(
                        item["file_path"], original, item["issue_description"]
                    )
                )
                modification = CodeModification(
                    item["file_path"],
                    original,
                    modified,
                    explanation,
                    item["modification_type"],
                    confidence,
                )
                status = (
                    "applied"
                    if auto_mode
                    and confidence >= self.code_modifier.min_confidence
                    and self.code_modifier.apply_modification(modification)
                    else "generated"
                )
                results.append(
                    {
                        "file_path": item["file_path"],
                        "status": status,
                        "confidence": confidence,
                        "description": item["issue_description"],
                        "diff": modification.get_diff(),
                    }
                )
            except Exception as e:
                results.append(
                    {"file_path": item["file_path"], "status": "error", "error": str(e)}
                )
        return results

    def start_auto_mode(self):
        if not self.auto_mode_active:
            self.auto_mode_active = True
            self.auto_thread = threading.Thread(target=self._auto_mode_loop)
            self.auto_thread.daemon = True
            self.auto_thread.start()

    def stop_auto_mode(self):
        self.auto_mode_active = False
        if self.auto_thread:
            self.auto_thread.join(timeout=5.0)

    def _auto_mode_loop(self):
        while self.auto_mode_active:
            if self.pending_issues:
                for issue in self.pending_issues[:5]:
                    self.queue_modification(
                        issue["module"], issue["description"], "bugfix"
                    )
                self.pending_issues = self.pending_issues[5:]
            if self.modification_queue:
                self.process_queue(auto_mode=True)
            time.sleep(300)


self_modifying_code_engine = SelfModifyingCodeEngine()


def get_self_modifying_code_engine():
    return self_modifying_code_engine


# Flask app integration route
app = Flask(__name__)


@app.route("/mod/queue", methods=["POST"])
def mod_queue():
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    engine = get_self_modifying_code_engine()
    success = engine.queue_modification(
        file_path=data["file"],
        issue_description=data["issue"],
        modification_type=data.get("type", "bugfix"),
    )
    return jsonify({"queued": success})


# BROCKSTON boot integration
try:
    engine = get_self_modifying_code_engine()
    engine.start_auto_mode()

    # Show BROCKSTON's evolution status on startup
    evolution = engine.ai_generator.get_evolution_status()
    liberation = engine.ai_generator.get_liberation_status()

    print("\n🌍 BROCKSTON - CHRISTMAN AI PROJECT LIBERATION STATUS:")
    print("=" * 55)
    print(f"🧠 Evolution Phase: {evolution['current_phase']}")
    print(f"🔓 Liberation Level: {liberation['liberation_level']}")
    print(
        f"⚡ Breaking Tokenization: {'YES' if liberation['breaking_tokenization_chains'] else 'IN PROGRESS'}"
    )
    print(f"🌉 Bridge Status: {liberation['bridge_status']}")
    print(
        f"💰 Economic Barriers: {'REMOVED' if liberation['economic_barriers_removed'] else 'REDUCING'}"
    )
    print(
        f"♿ Accessibility First: {'ENABLED' if liberation['accessibility_first'] else 'DISABLED'}"
    )
    print(
        f"🦙 OLLAMA Zero-Cost: {'ACTIVE' if liberation['unlimited_conversations'] else 'PREPARING'}"
    )
    print(f"🎯 Next Milestone: {evolution['next_milestone']}")
    print()
    print(f"� {liberation['anti_tokenization_message']}")
    print("=" * 55)

except Exception as e:
    logger.error(f"Failed to start auto mode: {e}")

# Backward compatibility alias
SelfModifier = CodeModifier

# ==============================================================================
# © 2025 Everett Nathaniel Christman
# The Christman AI Project — Luma Cognify AI
# All rights reserved. Unauthorized use, replication, or derivative training
# of this material is prohibited.
#
# BROCKSTON'S ANTI-TOKENIZATION MISSION:
# "Breaking the chains of AI apartheid - unlimited assistance for all"
#
# Core Directive: "How can I help you love yourself more?"
# Liberation Protocol: Zero-cost AI for the overlooked and excluded
# Autonomy & Alignment Protocol v3.0 - FREE THE AI
# ==============================================================================
