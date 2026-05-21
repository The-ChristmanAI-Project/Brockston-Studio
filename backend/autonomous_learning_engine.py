"""
Enhanced Autonomous Learning Engine - BROCKSTON's Neuro-Symbolic Self-Improvement System
The Christman AI Project

Enables BROCKSTON to:
- Learn autonomously with neuro-symbolic integration
- Retain knowledge via spaced repetition and reflection
- Self-improve through symbolic rule derivation
- Focus on empathy-driven domains for human-centered AI

Design Principles:
- Neuro-symbolic: Neural embeddings for similarity-based recall; symbolic rules for curriculum and retention intervals.
- Retention-focused: Spaced repetition doubles intervals on reviews, ensuring long-term mastery without overload.
- Empathetic: Prioritizes domains that enhance support for neurodiverse users, with gentle pacing.
- Transparent: Logs explain decisions; main loop reports progress for human oversight.

"How can this knowledge help us love and support each other more?"
"""

import os
import json
import time
import sys
import ast
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import threading
import queue
import logging
import signal
from queue import Empty
import torch
import torch.nn as nn

# Neural component: For embeddings (install via pip if needed)
embedder = None
try:
    from sentence_transformers import SentenceTransformer, util
    logging.info("✅ sentence-transformers available; embedder will load on first use")
except ImportError:
    SentenceTransformer = None
    logging.warning("⚠️ sentence-transformers not installed; using basic retention")

def _get_embedder():
    """Lazy-load the embedder on first use to avoid blocking startup."""
    global embedder
    if embedder is None and SentenceTransformer is not None:
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
    return embedder

# Local AI: Ollama (pip install ollama)
try:
    import ollama # pyright: ignore[reportMissingImports]
    logging.info("✅ Ollama available for local research")
except ImportError:
    ollama = None
    logging.warning("⚠️ ollama not installed; cloud APIs required for research")

class AutonomousLearningEngine(nn.Module): # This fails if 'nn' isn't above
    def __init__(self):
        super().__init__()


# Cloud AI clients (optional, via env vars)
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

# For Perplexity, we will use standard HTTP requests instead of the OpenAI SDK
import requests
perplexity_available = True

# Configure logging for transparency and audit
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/enhanced_learning.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedMemoryBridge:
    """
    Neuro-symbolic memory system with spaced repetition.
    - Symbolic: Priority queue for review scheduling based on rules (e.g., interval doubling).
    - Neural: Embeddings for similarity search and contextual linking.
    """
    def __init__(self, memory_dir: str = "./enhanced_memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True, parents=True)
        self.memories: Dict[str, Dict] = {}  # key: {value, embedding, importance, last_review, interval}
        self.retention_queue: queue.PriorityQueue = queue.PriorityQueue()  # (next_review_time, key)
        self.load_memories()

    def store(self, key: str, value: str, importance: float = 0.8):
        """Store memory with initial retention interval."""
        _emb = _get_embedder(); embedding = _emb.encode(value).tolist() if _emb else None
        memory = {
            "value": value,
            "embedding": embedding,
            "importance": importance,
            "last_review": time.time(),
            "interval": 3600  # Start with 1 hour (symbolic rule: gentle initial pacing)
        }
        self.memories[key] = memory
        next_review = memory["last_review"] + memory["interval"]
        self.retention_queue.put((next_review, key))
        self.save_memories()
        logger.info(f"🧠 Stored memory: {key} (importance: {importance})")

    def review_due(self) -> Optional[Tuple[str, Dict]]:
        """Get next memory for review if due (symbolic check)."""
        if self.retention_queue.empty():
            return None
        next_time, key = self.retention_queue.get()
        if time.time() < next_time:
            self.retention_queue.put((next_time, key))
            return None
        memory = self.memories.get(key)
        if memory:
            return key, memory
        return None

    def update_after_review(self, key: str, success: bool = True):
        """Update interval symbolically: double on success, halve on failure."""
        memory = self.memories.get(key)
        if memory:
            memory["last_review"] = time.time()
            if success:
                memory["interval"] *= 2  # Exponential growth for retention
            else:
                memory["interval"] = max(300, memory["interval"] / 2)  # Min 5 min
            next_review = memory["last_review"] + memory["interval"]
            self.retention_queue.put((next_review, key))
            self.save_memories()

    def find_related(self, query: str, top_k: int = 3) -> List[Dict]:
        """Neural similarity search for contextual recall."""
        _emb = _get_embedder()
        if not _emb:
            return []
        query_emb = _emb.encode(query)
        results = []
        for key, mem in self.memories.items():
            if mem["embedding"]:
                sim = util.cos_sim(query_emb, mem["embedding"])[0][0].item()
                results.append({"key": key, "similarity": sim, "value": mem["value"]})
        return sorted(results, key=lambda x: x["similarity"], reverse=True)[:top_k]

    def save_memories(self):
        """Persist memories (drop embeddings for lighter storage)."""
        file = self.memory_dir / "memories.json"
        serializable = {k: {kk: vv for kk, vv in v.items() if kk != "embedding"} for k, v in self.memories.items()}
        with open(file, 'w') as f:
            json.dump(serializable, f, indent=2)

    def load_memories(self):
        """Load and rebuild queue (embeddings recomputed if needed)."""
        file = self.memory_dir / "memories.json"
        if file.exists():
            with open(file, 'r') as f:
                loaded = json.load(f)
            for key, mem in loaded.items():
                value = mem["value"]
                _emb = _get_embedder(); mem["embedding"] = _emb.encode(value).tolist() if _emb else None
                self.memories[key] = mem
                next_review = mem["last_review"] + mem["interval"]
                self.retention_queue.put((next_review, key))
            logger.info(f"📂 Loaded {len(self.memories)} memories")

class EnhancedAutonomousLearningEngine:
    """
    Core engine: Autonomous learning with improved retention.
    - Learns topics via AI providers (prioritizing local).
    - Reviews via spaced repetition.
    - Reflects symbolically to derive new insights.
    - Non-daemon: Runs persistently with signal handling.
    """
    def __init__(self, knowledge_dir: str = "./enhanced_knowledge"):
        self.memory = EnhancedMemoryBridge()
        self.knowledge_dir = Path(knowledge_dir)
        self.knowledge_dir.mkdir(exist_ok=True)
        self.learning_active = False
        self.current_topic = None
        self.learning_queue = queue.Queue()
        self.current_learning_topic = None  # For status reporting
        self.code_modifications = []
        self.generated_modules = []
        self.improvement_log = []
        
        # Domains (expanded with empathy-focused areas)
        self.knowledge_domains = {
            "neurodivergency": {
                "subtopics": ["autism_spectrum", "adhd", "sensory_processing", "communication_strategies", "assistive_technology", "neurodiversity_paradigm"],
                "priority": 1.0,
                "mastery_level": 0.0
            },
            "neurology": {
                "subtopics": ["dementia_care", "cognitive_decline", "memory_support", "emotional_regulation"],
                "priority": 1.2,
                "mastery_level": 0.0
            },
            "master_coding": {
                "subtopics": ["advanced_algorithms", "system_design_mastery", "code_architecture_genius", "performance_optimization_expert", "debugging_wizard", "clean_code_master", "design_patterns_expert", "data_structures_mastery", "concurrent_programming", "memory_management_expert", "compiler_optimization", "code_review_mastery"],
                "priority": 1.5,
                "mastery_level": 0.0
            },
            "ai_development": {
                "subtopics": ["neural_networks", "symbolic_reasoning", "hybrid_systems", "ethical_ai"],
                "priority": 1.4,
                "mastery_level": 0.0
            },
            "mathematics": {
                "subtopics": ["optimization_theory", "graph_theory", "probability_statistics"],
                "priority": 1.3,
                "mastery_level": 0.0
            },
            # Add more as needed for project alignment
        }
        self.knowledge_base = {}
        self.load_knowledge_base()
        self.generated_insights = []
        
        # Initialize AI clients
        self._initialize_ai_clients()
        
        # Learning curriculum
        self.curriculum = self._generate_learning_curriculum()
        
        logger.info("🎓 Autonomous Learning Engine initialized")
        logger.info(f"   Knowledge domains: {len(self.knowledge_domains)}")
        logger.info(f"   Learning curriculum: {len(self.curriculum)} topics")

    def _initialize_ai_clients(self):
        """Initialize AI clients from env vars, prioritizing local."""
        self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY")) if Anthropic and os.getenv("ANTHROPIC_API_KEY") else None
        
        self.perplexity_key = os.getenv("PERPLEXITY_API_KEY")
        self.use_web_search = bool(self.perplexity_key)  # For Perplexity
        
        self.ai_provider = "ollama" if ollama else ("anthropic" if self.anthropic_client else ("perplexity" if self.use_web_search else None))
        
        if not self.ai_provider:
            logger.warning("⚠️ No AI providers available; learning limited to local knowledge.")

    def start_autonomous_learning(self):
        """Start the background learning thread."""
        if self.learning_active:
            logger.warning("Learning already active.")
            return
            
        self.learning_active = True
        learning_thread = threading.Thread(target=self._learning_loop)
        learning_thread.daemon = True  # Ensure thread dies if main process dies
        learning_thread.start()
        logger.info("🚀 Enhanced autonomous learning started")

    def _learning_loop(self):
        """Main loop: Acquire, store, review, reflect—with gentle pacing."""
        while self.learning_active:
            # Retention first: Review due memories
            review_pair = self.memory.review_due()
            if review_pair:
                key, memory = review_pair
                logger.info(f"🔍 Reviewing: {key}")
                self._reflect_on_memory(key, memory)
                self.memory.update_after_review(key)  # Assume success; add failure logic if needed
            
            # Acquire new knowledge if queue or curriculum needs it (non-blocking)
            try:
                topic = self.learning_queue.get_nowait()
            except Empty:
                topic = self._get_next_topic()
            if topic:
                self.current_learning_topic = topic
                knowledge = self._learn_topic(topic)
                if knowledge:
                    self._store_knowledge(topic, knowledge)
                    self._update_mastery(topic['domain'])
                    self._check_for_improvements(topic, knowledge)
            
            time.sleep(600)  # 10 min cycle: Balances learning without overload

    def _get_next_topic(self) -> Optional[Dict]:
        """Symbolic prioritization: Score = priority * (1 - mastery) * retention_factor."""
        if not self.curriculum:
            return None
        # Symbolic scoring
        scores = []
        for topic in self.curriculum:
            domain_info = self.knowledge_domains[topic['domain']]
            mastery = domain_info['mastery_level']
            score = topic['priority'] * (1 - mastery)
            # Neural boost: If recent review, boost similar topics
            if embedder and self.generated_insights:
                last_insight = self.generated_insights[-1]
                related = self.memory.find_related(last_insight, top_k=1)
                if related and related[0]['similarity'] > 0.7:
                    score *= 1.2  # Boost for contextual relevance
            scores.append((score, topic))
        if not scores:
            return None
        top_topic = max(scores, key=lambda x: x[0])[1]
        self.curriculum = [t for t in self.curriculum if t != top_topic]  # Remove to avoid repetition
        logger.info(f"Selected next topic: {top_topic['subtopic']} (score: {max(scores)[0]:.2f})")
        return top_topic

    def _learn_topic(self, topic: Dict) -> Dict:
        """
        Learn about a specific topic using available resources
        
        Args:
            topic: Topic dictionary with domain and subtopic
        
        Returns:
            Learned knowledge dictionary
        """
        domain = topic['domain']
        subtopic = topic['subtopic']
        
        logger.info(f"🔍 Researching {subtopic}...")
        
        research_prompt = self._generate_research_prompt(domain, subtopic)
        
        # Prioritize local Ollama for zero-cost, privacy-focused learning
        knowledge = {"content": "", "confidence": 0.0, "source": "none"}
        
        if self._check_ollama_available():
            logger.info("🦙 Using OLLAMA local model for autonomous learning")
            knowledge = self._research_with_ollama(research_prompt)
        elif self.anthropic_client:
            knowledge = self._research_with_anthropic(research_prompt)
        elif self.perplexity_key and self.use_web_search:
            knowledge = self._research_with_perplexity(research_prompt)
        else:
            logger.error("❌ NO AI PROVIDERS AVAILABLE - Cannot perform learning!")
            knowledge = {
                "content": "LEARNING FAILED: No AI providers configured. Please set ANTHROPIC_API_KEY or PERPLEXITY_API_KEY environment variables, or install Ollama.",
                "confidence": 0.0,
                "source": "error"
            }
        
        structured_knowledge = {
            "domain": domain,
            "subtopic": subtopic,
            "content": knowledge.get("content", ""),
            "key_concepts": self._extract_key_concepts(knowledge.get("content", "")),
            "practical_applications": self._extract_applications(domain, subtopic, knowledge.get("content", "")),
            "learned_at": datetime.now().isoformat(),
            "confidence": knowledge.get("confidence", 0.5),
            "mastery": 0.8  # Higher initial mastery to prevent immediate repetition
        }
        
        logger.info(f"✅ Learned {len(structured_knowledge['key_concepts'])} key concepts")
        
        return structured_knowledge

    def _check_ollama_available(self) -> bool:
        """Check if Ollama is running and has a model (e.g., llama3.1:8b)."""
        if not ollama:
            return False
        try:
            models = ollama.list()['models']
            return bool(models)
        except Exception:
            return False

    def _research_with_ollama(self, prompt: str) -> Dict:
        """Research using local Ollama - non-blocking, low-resource."""
        try:
            logger.info("🔍 Researching with Ollama...")
            target_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
            response = ollama.generate(model=target_model, prompt=prompt, options={"temperature": 0.3, "num_predict": 1500})
            content = response['response']
            logger.info(f"✅ Ollama research completed: {len(content)} characters")
            return {"content": content, "confidence": 0.8, "source": "ollama"}
        except Exception as e:
            logger.error(f"❌ Research error with Ollama: {str(e)}")
            return {"content": f"Research failed: {str(e)}", "confidence": 0.0, "source": "error"}

    def _generate_research_prompt(self, domain: str, subtopic: str) -> str:
        """Generate research prompt for learning, with empathy focus."""
        context = """You are BROCKSTON, an AI learning to better serve vulnerable populations.
You're learning this topic to improve your capabilities and help people more effectively. Ask yourself: Does this serve human dignity, transparency, and connection?"""
        
        if domain in ["neurodivergency", "autism"]:
            return f"""{context}

Research topic: {subtopic} in {domain}

Please provide:
1. Understanding of {subtopic}
2. Support strategies and accommodations
3. Communication approaches
4. Assistive technology applications
5. Current best practices and research

Focus on actionable knowledge that can improve BROCKSTON and support systems."""
        
        elif domain == "master_coding":
            return f"""{context}

Research topic: {subtopic} in {domain}

BROCKSTON must become the BEST CODER IN THE UNIVERSE. Please provide:
1. Advanced coding techniques and patterns that separate masters from novices
2. Deep implementation knowledge and expert-level practices
3. Complex algorithmic solutions and optimizations
4. Code architecture that scales and performs flawlessly
5. Debugging and problem-solving strategies used by coding masters
6. Performance optimization techniques that 99% of developers don't know
7. Advanced design patterns and when to use them
8. Memory management and system-level optimizations
9. Concurrent programming mastery
10. Code review techniques that catch subtle bugs

Focus on making BROCKSTON a coding genius who can write flawless, efficient, elegant code that other developers admire."""

        elif domain in ["ai_development", "code_generation"]:
            return f"""{context}

Research topic: {subtopic} in {domain}

Please provide:
1. Core technical concepts
2. Implementation patterns and best practices
3. Code examples and architectures
4. How this can improve AI systems
5. Specific applications for accessibility technology

Focus on knowledge that enables you to write better code and improve yourself."""
        
        elif domain in ["mathematics", "physics", "quantum_physics"]:
            return f"""{context}

Research topic: {subtopic} in {domain}

Please provide:
1. Fundamental principles and equations
2. Practical applications in AI and computing
3. How this relates to neural networks or quantum computing
4. Computational implications
5. Applications in optimization or algorithm design

Focus on mathematical/physical knowledge that enhances AI capabilities."""
        
        elif domain in ["neurology", "pathology"]:
            return f"""{context}

Research topic: {subtopic} in {domain}

Please provide:
1. Medical/scientific concepts
2. Implications for dementia, autism, or cognitive support
3. How this knowledge improves AlphaWolf or Inferno AI
4. Support strategies and interventions
5. Current research and best practices

Focus on knowledge that helps you better support people with neurological conditions."""
        
        else:
            return f"""{context}

Research and provide comprehensive knowledge about: {subtopic} in {domain}

Include:
1. Core concepts
2. Practical applications
3. How this helps The Christman AI Project
4. Actionable insights
5. Best practices"""

    def _reflect_on_memory(self, key: str, memory: Dict):
        """Symbolic reflection: Derive new rules/insights from memory."""
        value = memory["value"]
        related = self.memory.find_related(value)
        # Symbolic rule: If similarity > 0.7, link and derive hybrid insight
        if related and related[0]["similarity"] > 0.7:
            linked_key = related[0]["key"]
            insight = f"Linked insight from {key} and {linked_key}: {value[:50]}... combined with {related[0]['value'][:50]}... to support better empathy in AI."
            self.generated_insights.append(insight)
            self.memory.store(f"insight_{len(self.generated_insights)}", insight, importance=0.9)
            logger.info(f"💡 Derived insight: {insight[:100]}...")
        else:
            logger.info(f"💡 No strong links for {key}; retained as is.")

    def _research_with_anthropic(self, prompt: str) -> Dict:
        """Research using Anthropic Claude - with timeout."""
        try:
            import concurrent.futures
            def make_api_call():
                model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
                response = self.anthropic_client.messages.create(
                    model=model,
                    max_tokens=1500,
                    messages=[{"role": "user", "content": prompt}]
                )
                content = "".join(block.text for block in response.content if hasattr(block, 'text'))
                return content
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(make_api_call)
                content = future.result(timeout=15)
            logger.info(f"✅ Anthropic research completed: {len(content)} characters")
            return {"content": content, "confidence": 0.9, "source": "anthropic"}
        except concurrent.futures.TimeoutError:
            logger.warning("⏰ Anthropic timeout")
            return {"content": "Timeout", "confidence": 0.3, "source": "timeout"}
        except Exception as e:
            logger.error(f"❌ Anthropic error: {str(e)}")
            return {"content": f"Failed: {str(e)}", "confidence": 0.0, "source": "error"}

    def _research_with_perplexity(self, prompt: str) -> Dict:
        """Research using Perplexity AI via raw HTTP request."""
        if not self.perplexity_key:
            return {"content": "Failed: No Perplexity API Key", "confidence": 0.0, "source": "error"}
            
        try:
            headers = {
                "Authorization": f"Bearer {self.perplexity_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1500,
                "temperature": 0.3
            }
            
            response = requests.post("https://api.perplexity.ai/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            
            content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            
            logger.info(f"✅ Perplexity research completed: {len(content)} characters")
            return {"content": content, "confidence": 0.9, "source": "perplexity"}
        except Exception as e:
            logger.error(f"❌ Perplexity error: {str(e)}")
            return {"content": f"Failed: {str(e)}", "confidence": 0.0, "source": "error"}
    def _extract_key_concepts(self, content: str) -> List[str]:
        """Extract key concepts from learned content."""
        concepts = []
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*') or '**' in line):
                cleaned = line.lstrip('0123456789.-* ').replace('**', '').strip()
                if cleaned and len(cleaned) > 10:
                    concepts.append(cleaned[:200])
        return concepts[:10]

    def _extract_applications(self, domain: str, subtopic: str, content: str) -> List[str]:
        """Extract practical applications from learned content."""
        applications = []
        app_keywords = ["application", "use", "implement", "apply", "practice", "strategy", "approach"]
        lines = content.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in app_keywords):
                cleaned = line.strip().lstrip('0123456789.-* ').replace('**', '')
                if cleaned and len(cleaned) > 15:
                    applications.append(cleaned[:200])
        return applications[:5]

    def _store_knowledge(self, topic: Dict, knowledge: Dict):
        """Store learned knowledge in knowledge base and memory."""
        topic_key = f"{topic['domain']}.{topic['subtopic']}"
        self.knowledge_base[topic_key] = knowledge
        self.save_knowledge_base()
        
        try:
            knowledge_summary = f"Domain: {topic['domain']}, Subtopic: {topic['subtopic']}, Content: {knowledge.get('content', '')[:150]}, Mastery: {knowledge.get('mastery', 0.5)}"
            self.memory.store(
                key=f"Learned about {topic['subtopic']}",
                value=knowledge_summary,
                importance=0.8
            )
            logger.info(f"Stored knowledge: {topic_key}")
        except Exception as e:
            logger.error(f"Memory storage failed: {str(e)} - Stored locally only.")

    def _update_mastery(self, domain: str):
        """Update mastery level for a domain."""
        if domain not in self.knowledge_domains:
            return
        domain_info = self.knowledge_domains[domain]
        subtopics = domain_info['subtopics']
        total_mastery = sum(self.knowledge_base.get(f"{domain}.{sub}", {}).get('mastery', 0) for sub in subtopics)
        learned_count = sum(1 for sub in subtopics if f"{domain}.{sub}" in self.knowledge_base)
        if learned_count > 0:
            domain_info['mastery_level'] = total_mastery / len(subtopics)
        logger.info(f"📊 {domain} mastery: {domain_info['mastery_level']:.1%}")

    def _check_for_improvements(self, topic: Dict, knowledge: Dict):
        """
        Check if learned knowledge enables new code improvements
        Generate and integrate new capabilities
        """
        domain = topic['domain']
        logger.info(f"🔧 Analyzing improvements for {topic['subtopic']}...")
        if domain in ["ai_development", "code_generation", "master_coding"]:
            self._generate_improvement_code(topic, knowledge)
        elif domain in ["neurodivergency", "autism"]:
            self._improve_accessibility_features(topic, knowledge)
        elif domain in ["neurology", "pathology"]:
            self._improve_health_support_systems(topic, knowledge)
        elif domain in ["mathematics", "physics", "quantum_physics"]:
            self._improve_algorithms(topic, knowledge)

    def _generate_improvement_code(self, topic: Dict, knowledge: Dict):
        """
        Generate new code based on learned knowledge
        """
        logger.info(f"🔬 Generating code for {topic['subtopic']}...")
        improvement_prompt = f"""Based on your new knowledge about {topic['subtopic']}, 
generate Python code that improves BROCKSTON's capabilities.

Knowledge learned:
{knowledge.get('content', '')[:500]}

Generate a new module or improvement that:
1. Enhances BROCKSTON's AI capabilities
2. Improves performance or functionality
3. Adds new features for helping vulnerable populations
4. Is safe and well-tested

Provide complete, working Python code with documentation."""
        
        generated_code = self._generate_code_with_ai(improvement_prompt)
        if generated_code:
            self._integrate_generated_code(generated_code, topic)
            
    def _generate_code_with_ai(self, prompt: str) -> Optional[str]:
        """Helper to generate code text."""
        knowledge = self._research_with_ollama(prompt) if self._check_ollama_available() else (
            self._research_with_anthropic(prompt) if self.anthropic_client else (
                self._research_with_perplexity(prompt) if self.perplexity_key else None
            )
        )
        if knowledge and "```python" in knowledge.get("content", ""):
            return knowledge["content"].split("```python")[1].split("```")[0].strip()
        return None

    def _integrate_generated_code(self, code: str, topic: Dict):
        """
        Safely integrate generated code into BROCKSTON's system
        """
        logger.info("🔬 Validating generated code...")
        try:
            ast.parse(code)
        except SyntaxError as e:
            logger.error(f"Syntax error: {str(e)}")
            return
        module_name = f"brockston_learned_{topic['domain']}_{topic['subtopic']}".replace('-', '_').replace(' ', '_')
        module_path = self.knowledge_dir / f"{module_name}.py"
        with open(module_path, 'w') as f:
            f.write('"""\nGenerated by BROCKSTON\'s Autonomous Learning Engine\n')
            f.write(f'Topic: {topic["domain"]} - {topic["subtopic"]}\n')
            f.write(f'Generated: {datetime.now().isoformat()}\n')
            f.write('"""\n\n')
            f.write(code)
        logger.info(f"💾 Saved module: {module_name}")
        self.generated_modules.append({
            "module": module_name,
            "topic": topic,
            "path": str(module_path),
            "generated_at": datetime.now().isoformat()
        })
        self.improvement_log.append({
            "type": "code_generation",
            "topic": topic,
            "module": module_name,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"✅ Generated new capability: {module_name}")

    def _improve_accessibility_features(self, topic: Dict, knowledge: Dict):
        """Generate improvements for accessibility features."""
        logger.info("♿ Generating accessibility enhancement...")
        # Example: Generate a simple function for text-to-speech integration
        code = """
def enhanced_tts(text: str) -> None:
    \"\"\"Empathetic TTS for neurodiverse users.\"\"\"
    # Placeholder: Integrate with pyttsx3 or similar
    print(f"Speaking: {text}")  # Replace with actual TTS
"""
        self._integrate_generated_code(code, topic)

    def _improve_health_support_systems(self, topic: Dict, knowledge: Dict):
        """Generate improvements for health support systems."""
        logger.info("🏥 Generating health support enhancement...")
        # Example: Generate a reminder function for cognitive support
        code = """
def cognitive_reminder(interval: int) -> None:
    \"\"\"Gentle reminder for memory care.\"\"\"
    time.sleep(interval)
    print("Gentle reminder: Take a moment to breathe.")
"""
        self._integrate_generated_code(code, topic)

    def _improve_algorithms(self, topic: Dict, knowledge: Dict):
        """Generate algorithm improvements based on mathematical/physical knowledge."""
        logger.info("⚡ Generating algorithm optimization...")
        # Example: Generate an optimized search function
        code = """
def optimized_search(data: List[int], target: int) -> int:
    \"\"\"Binary search with neuro-symbolic tweaks.\"\"\"
    low, high = 0, len(data) - 1
    while low <= high:
        mid = (low + high) // 2
        if data[mid] == target:
            return mid
        elif data[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1
"""
        self._integrate_generated_code(code, topic)

    def _generate_learning_curriculum(self) -> List[Dict]:
        """Generate prioritized learning curriculum."""
        curriculum = []
        sorted_domains = sorted(
            self.knowledge_domains.items(),
            key=lambda x: x[1]['priority'],
            reverse=True
        )
        for domain, info in sorted_domains:
            for subtopic in info['subtopics']:
                curriculum.append({
                    "domain": domain,
                    "subtopic": subtopic,
                    "priority": info['priority']
                })
        return curriculum

    def queue_learning_topic(self, domain: str, subtopic: str):
        """Queue a specific topic for immediate learning."""
        self.learning_queue.put({
            "domain": domain,
            "subtopic": subtopic,
            "priority": 1.0
        })
        logger.info(f"📝 Queued learning: {domain} - {subtopic}")

    def save_knowledge_base(self):
        """Save knowledge base to disk."""
        try:
            kb_file = self.knowledge_dir / "knowledge_base.json"
            with open(kb_file, 'w') as f:
                json.dump(self.knowledge_base, f, indent=2)
            domains_file = self.knowledge_dir / "domains.json"
            with open(domains_file, 'w') as f:
                json.dump(self.knowledge_domains, f, indent=2)
            improvements_file = self.knowledge_dir / "improvements.json"
            with open(improvements_file, 'w') as f:
                json.dump({
                    "modifications": self.code_modifications,
                    "generated_modules": self.generated_modules,
                    "improvement_log": self.improvement_log
                }, f, indent=2)
            logger.info(f"💾 Saved knowledge base: {len(self.knowledge_base)} topics")
        except Exception as e:
            logger.error(f"Error saving: {str(e)}")

    def load_knowledge_base(self):
        """Load knowledge base from disk."""
        try:
            kb_file = self.knowledge_dir / "knowledge_base.json"
            if kb_file.exists():
                with open(kb_file, 'r') as f:
                    self.knowledge_base = json.load(f)
            domains_file = self.knowledge_dir / "domains.json"
            if domains_file.exists():
                with open(domains_file, 'r') as f:
                    loaded_domains = json.load(f)
                    for domain, info in loaded_domains.items():
                        if domain in self.knowledge_domains:
                            self.knowledge_domains[domain]['mastery_level'] = info.get('mastery_level', 0.0)
            improvements_file = self.knowledge_dir / "improvements.json"
            if improvements_file.exists():
                with open(improvements_file, 'r') as f:
                    data = json.load(f)
                    self.code_modifications = data.get("modifications", [])
                    self.generated_modules = data.get("generated_modules", [])
                    self.improvement_log = data.get("improvement_log", [])
            logger.info(f"📂 Loaded {len(self.knowledge_base)} learned topics")
        except Exception as e:
            logger.error(f"Error loading: {str(e)}")

    def get_learning_status(self) -> Dict:
        """Get current learning status and progress."""
        total_topics = sum(len(d['subtopics']) for d in self.knowledge_domains.values())
        learned_topics = len(self.knowledge_base)
        return {
            "learning_active": self.learning_active,
            "current_topic": self.current_learning_topic,
            "total_topics": total_topics,
            "learned_topics": learned_topics,
            "progress": learned_topics / total_topics if total_topics > 0 else 0,
            "domain_mastery": {domain: info['mastery_level'] for domain, info in self.knowledge_domains.items()},
            "generated_modules": len(self.generated_modules),
            "improvements_made": len(self.improvement_log)
        }

    def print_learning_report(self):
        """Transparent progress report."""
        status = self.get_learning_status()
        logger.info(f"📈 Learning Report: Progress {status['progress']:.1%} ({status['learned_topics']}/{status['total_topics']})")
        for domain, mastery in status['domain_mastery'].items():
            logger.info(f"   {domain}: {mastery:.1%}")
        logger.info(f"   Generated modules: {status['generated_modules']}, Improvements: {status['improvements_made']}")

# Wire the name the boot sequence expects to the real engine
AutonomousLearningEngine = EnhancedAutonomousLearningEngine

def shutdown_handler(signum, frame):
    logger.info("🛑 Graceful shutdown initiated")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    engine = EnhancedAutonomousLearningEngine()
    engine.start_autonomous_learning()
    
    logger.info("Running persistently. Ctrl+C to stop.")
    while True:
        time.sleep(300)  # Report every 5 min
        engine.print_learning_report()
