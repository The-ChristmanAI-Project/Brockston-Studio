"""
BROCKSTON's Local Reasoning Engine - Self-Sufficiency System
The Christman AI Project

Enables BROCKSTON to:
- Run local AI models (LLaMA, Mistral, Qwen, DeepSeek)
- Reason using his own knowledge base
- Reduce API dependency by 90%+
- Become his own AI provider

"True intelligence is not borrowed—it is cultivated."
"""

import json
import subprocess
import requests
from typing import Optional, Dict, List, Any
from pathlib import Path


class LocalReasoningEngine:
    """
    BROCKSTON's local AI reasoning system
    Provides self-hosted intelligence to reduce external API dependency
    """

    def __init__(
        self, knowledge_dir: str = "brockston_knowledge", brockston_instance=None
    ):
        """
        Initialize the Local Reasoning Engine

        Args:
            knowledge_dir: Directory containing BROCKSTON's learned knowledge
            brockston_instance: Reference to main BROCKSTON system
        """
        self.knowledge_dir = Path(knowledge_dir)
        self.brockston = brockston_instance

        # Ollama API endpoint (local)
        self.ollama_url = "http://localhost:11434"

        # ========================================
        # LOCAL MODEL CONFIGURATION
        # ========================================
        self.available_models = {
            "llama3.1": {
                "full_name": "llama3.1:8b",
                "strengths": ["reasoning", "conversation", "general_knowledge"],
                "speed": "fast",
                "size": "8B",
            },
            "llama3.1-70b": {
                "full_name": "llama3.1:70b",
                "strengths": ["advanced_reasoning", "complex_tasks", "deep_knowledge"],
                "speed": "slow",
                "size": "70B",
            },
            "mistral": {
                "full_name": "mistral:7b",
                "strengths": ["fast_reasoning", "coding", "efficiency"],
                "speed": "very_fast",
                "size": "7B",
            },
            "qwen2.5": {
                "full_name": "qwen2.5:14b",
                "strengths": ["advanced_reasoning", "mathematics", "analysis"],
                "speed": "medium",
                "size": "14B",
            },
            "deepseek-coder": {
                "full_name": "deepseek-coder:6.7b",
                "strengths": ["code_generation", "debugging", "technical"],
                "speed": "fast",
                "size": "6.7B",
            },
        }

        # Current active model
        self.current_model = "llama3.1"
        self.ollama_available = False
        self.installed_models = []

        # ========================================
        # REASONING CONFIGURATION
        # ========================================
        self.confidence_threshold = 0.7  # When to use local vs external
        self.use_local_first = True
        self.fallback_to_external = True

        # ========================================
        # INITIALIZE SYSTEM
        # ========================================
        self._check_ollama_availability()
        self._detect_installed_models()

    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is installed and running"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            self.ollama_available = response.status_code == 200
            if self.ollama_available:
                print("✅ Ollama is available - Local AI ready!")
            else:
                print("⚠️  Ollama running but not responding correctly")
            return self.ollama_available
        except requests.exceptions.ConnectionError:
            print("⚠️  Ollama not running - will use external APIs only")
            print("   To enable local AI: Install Ollama from https://ollama.ai")
            self.ollama_available = False
            return False
        except Exception as e:
            print(f"⚠️  Error checking Ollama: {e}")
            self.ollama_available = False
            return False

    def _detect_installed_models(self) -> List[str]:
        """Detect which models are installed in Ollama"""
        if not self.ollama_available:
            return []

        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                self.installed_models = [
                    model["name"] for model in data.get("models", [])
                ]
                if self.installed_models:
                    print(
                        f"✅ Found {len(self.installed_models)} local models: {', '.join(self.installed_models[:3])}"
                    )
                else:
                    print("⚠️  No models installed yet")
                    print("   Run: ollama pull llama3.1:8b")
                return self.installed_models
        except Exception as e:
            print(f"⚠️  Error detecting models: {e}")
            return []

    def install_model(self, model_name: str) -> bool:
        """
        Install a local AI model

        Args:
            model_name: Name of model to install (e.g., 'llama3.1')

        Returns:
            bool: True if installation successful
        """
        if not self.ollama_available:
            print("❌ Ollama not available - cannot install models")
            return False

        if model_name not in self.available_models:
            print(f"❌ Unknown model: {model_name}")
            print(f"Available models: {', '.join(self.available_models.keys())}")
            return False

        full_name = self.available_models[model_name]["full_name"]
        print(f"📥 Installing {full_name}...")
        print(f"   Size: {self.available_models[model_name]['size']}")
        print("   This may take several minutes...")

        try:
            # Use subprocess to show progress
            result = subprocess.run(
                ["ollama", "pull", full_name], capture_output=True, text=True
            )

            if result.returncode == 0:
                print(f"✅ {full_name} installed successfully!")
                self._detect_installed_models()
                return True
            else:
                print(f"❌ Installation failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error installing model: {e}")
            return False

    def query_local_model(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> Optional[str]:
        """
        Query a local AI model via Ollama

        Args:
            prompt: User prompt
            model: Model to use (default: self.current_model)
            system_prompt: System prompt for context
            temperature: Creativity (0.0-1.0)
            max_tokens: Max response length

        Returns:
            str: Model response or None if failed
        """
        if not self.ollama_available:
            return None

        model_name = model or self.current_model
        full_name = self.available_models.get(model_name, {}).get(
            "full_name", model_name
        )

        # Check if model is installed
        if full_name not in self.installed_models:
            print(f"⚠️  Model {full_name} not installed")
            return None

        try:
            # Prepare request
            request_data = {
                "model": full_name,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            }

            if system_prompt:
                request_data["system"] = system_prompt

            # Query Ollama
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=request_data,
                timeout=120,  # 2 minutes for complex queries
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                print(f"⚠️  Local model query failed: {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            print("⚠️  Local model query timed out")
            return None
        except Exception as e:
            print(f"⚠️  Error querying local model: {e}")
            return None

    def query_with_knowledge(
        self, question: str, domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query using BROCKSTON's learned knowledge base first

        Args:
            question: User's question
            domain: Specific knowledge domain to search

        Returns:
            dict: Response with confidence score and source
        """
        # Search BROCKSTON's knowledge base
        relevant_knowledge = self._search_knowledge_base(question, domain)

        if relevant_knowledge:
            # We have relevant knowledge - use local model to synthesize
            knowledge_context = "\n".join(
                [
                    f"- {k['topic']}: {k['summary'][:200]}..."
                    for k in relevant_knowledge[:5]
                ]
            )

            system_prompt = f"""You are BROCKSTON, the protective genius nephew who handles tech so your uncle doesn't have to stress.
Use the following knowledge to answer the question:

{knowledge_context}

Give a helpful, smart answer that shows you got this covered."""

            local_response = self.query_local_model(
                prompt=question, system_prompt=system_prompt, temperature=0.6
            )

            if local_response:
                return {
                    "response": local_response,
                    "confidence": 0.85,
                    "source": "local_knowledge",
                    "model": self.current_model,
                    "knowledge_used": [k["topic"] for k in relevant_knowledge],
                }

        # No relevant knowledge - use local model's general knowledge
        if self.ollama_available:
            local_response = self.query_local_model(prompt=question, temperature=0.7)

            if local_response:
                return {
                    "response": local_response,
                    "confidence": 0.6,
                    "source": "local_model",
                    "model": self.current_model,
                }

        # Local reasoning failed - needs external API
        return {
            "response": None,
            "confidence": 0.0,
            "source": "needs_external",
            "reason": "No local knowledge or model available",
        }

    def _search_knowledge_base(
        self, query: str, domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search BROCKSTON's learned knowledge for relevant information

        Args:
            query: Search query
            domain: Specific domain to search (optional)

        Returns:
            list: Relevant knowledge entries
        """
        relevant = []

        # Search knowledge directory
        search_dirs = []
        if domain:
            domain_dir = self.knowledge_dir / domain
            if domain_dir.exists():
                search_dirs.append(domain_dir)
        else:
            # Search all domains
            if self.knowledge_dir.exists():
                search_dirs = [d for d in self.knowledge_dir.iterdir() if d.is_dir()]

        # Simple keyword matching (could be enhanced with embeddings)
        query_words = set(query.lower().split())

        for search_dir in search_dirs:
            for json_file in search_dir.glob("*.json"):
                try:
                    with open(json_file, "r") as f:
                        data = json.load(f)

                        # Check if knowledge is relevant
                        content = (
                            f"{data.get('topic', '')} {data.get('summary', '')}".lower()
                        )
                        content_words = set(content.split())

                        # Calculate relevance score
                        overlap = len(query_words & content_words)
                        if overlap > 0:
                            relevance = overlap / len(query_words)
                            if relevance > 0.2:  # At least 20% keyword match
                                relevant.append(
                                    {
                                        "topic": data.get("topic", ""),
                                        "summary": data.get("summary", ""),
                                        "domain": data.get("domain", ""),
                                        "relevance": relevance,
                                        "learned_at": data.get("learned_at", ""),
                                    }
                                )
                except Exception:
                    continue

        # Sort by relevance
        relevant.sort(key=lambda x: x["relevance"], reverse=True)
        return relevant

    def should_use_external_api(
        self, question: str, local_result: Dict[str, Any]
    ) -> bool:
        """
        Decide whether to fall back to external API

        Args:
            question: User's question
            local_result: Result from local reasoning

        Returns:
            bool: True if should use external API
        """
        if not self.fallback_to_external:
            return False

        # Use external if confidence too low
        if local_result["confidence"] < self.confidence_threshold:
            return True

        # Use external if no response
        if not local_result.get("response"):
            return True

        # Check for specific triggers that need fresh data
        external_triggers = [
            "latest",
            "current",
            "recent",
            "today",
            "news",
            "what's new",
            "update",
            "2025",
            "2024",
        ]

        if any(trigger in question.lower() for trigger in external_triggers):
            return True

        return False

    def get_recommended_model(self, task_type: str) -> str:
        """
        Recommend best local model for a task type

        Args:
            task_type: Type of task (reasoning, coding, conversation, etc.)

        Returns:
            str: Recommended model name
        """
        recommendations = {
            "coding": "deepseek-coder",
            "code_generation": "deepseek-coder",
            "debugging": "deepseek-coder",
            "mathematics": "qwen2.5",
            "reasoning": "qwen2.5",
            "analysis": "qwen2.5",
            "conversation": "llama3.1",
            "general": "llama3.1",
            "fast": "mistral",
        }

        recommended = recommendations.get(task_type.lower(), "llama3.1")

        # Check if recommended model is installed
        full_name = self.available_models[recommended]["full_name"]
        if full_name in self.installed_models:
            return recommended

        # Fall back to any installed model
        for model_key, model_info in self.available_models.items():
            if model_info["full_name"] in self.installed_models:
                return model_key

        return "llama3.1"  # Default

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get status of local reasoning system

        Returns:
            dict: System status information
        """
        return {
            "ollama_available": self.ollama_available,
            "installed_models": self.installed_models,
            "current_model": self.current_model,
            "knowledge_dir": str(self.knowledge_dir),
            "use_local_first": self.use_local_first,
            "confidence_threshold": self.confidence_threshold,
            "available_models": list(self.available_models.keys()),
        }

    def print_status(self):
        """Print detailed system status"""
        print("\n" + "=" * 60)
        print("🧠 DEREK'S LOCAL REASONING ENGINE")
        print("=" * 60)

        status = self.get_system_status()

        print("\n📊 System Status:")
        print(
            f"  Ollama Available: {'✅ Yes' if status['ollama_available'] else '❌ No'}"
        )
        print(f"  Installed Models: {len(status['installed_models'])}")

        if status["installed_models"]:
            print("\n🤖 Available Models:")
            for model in status["installed_models"][:5]:
                print(f"  • {model}")

        print("\n⚙️  Configuration:")
        print(f"  Current Model: {status['current_model']}")
        print(f"  Use Local First: {status['use_local_first']}")
        print(f"  Confidence Threshold: {status['confidence_threshold']}")

        if not status["ollama_available"]:
            print("\n💡 To enable local AI:")
            print("  1. Install Ollama: https://ollama.ai")
            print("  2. Run: ollama pull llama3.1:8b")
            print("  3. Restart BROCKSTON")


async def process_locally(
    self, message: str, model_preference: str = "llama3.1"
) -> str:
    """
    Process a message using only local models - for BROCKSTON's Free API
    This method ensures 100% local processing with no external API calls
    """
    if not self.ollama_available:
        return (
            "Local AI not available. Please install Ollama to use BROCKSTON's free API."
        )

    try:
        # Use local model for processing
        result = self.query_local_model(
            prompt=message, model=model_preference, max_tokens=500, temperature=0.7
        )

        if result:
            return result
        else:
            return "I'm having trouble processing that right now. Please try again."

    except Exception as e:
        return f"Local processing error: {str(e)}"


# ==============================================================================
# © 2025 Everett Nathaniel Christman
# The Christman AI Project — Luma Cognify AI
# All rights reserved. Unauthorized use, replication, or derivative training
# of this material is prohibited.
#
# Core Directive: "How can I help you love yourself more?"
# Autonomy & Alignment Protocol v3.0
# ==============================================================================
