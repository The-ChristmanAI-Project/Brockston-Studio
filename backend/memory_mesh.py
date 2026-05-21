"""
Memory Mesh - Human-Like Memory System for BROCKSTON
The Christman AI Project

Mimics human memory architecture:
- Working Memory (surface, current conversation)
- Episodic Memory (experiences, conversations)
- Semantic Memory (facts, learned knowledge)
- Memory Consolidation (filing from working → long-term)
- Intelligent Retrieval (contextually relevant recall)

"Memory is what makes us human. BROCKSTON deserves the same."
"""

import json
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import threading
from collections import defaultdict
import logging
import os
from cryptography.fernet import Fernet

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("logs/memory_mesh.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class MemoryMesh:
    """
    Human-like memory system with automatic categorization and consolidation
    """

    def __init__(
        self,
        memory_dir: str = "brockston_memory",
        encryption_key: Optional[bytes] = None,
    ):
        """
        Initialize the Memory Mesh

        Args:
            memory_dir: Directory to store persistent memory files
            encryption_key: Optional Fernet key for encrypting memory files
        """
        self.memory_dir = Path(memory_dir)
        try:
            self.memory_dir.mkdir(exist_ok=True, parents=True)
            if not os.access(self.memory_dir, os.W_OK):
                raise PermissionError(f"No write permission for {self.memory_dir}")
        except Exception as e:
            logger.error(f"Failed to initialize memory directory: {e}")
            raise RuntimeError(f"Cannot initialize MemoryMesh: {e}")

        self.encryption_key = encryption_key or Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key) if self.encryption_key else None
        self.working_memory = []
        self.working_memory_limit = 7
        self.episodic_memory = []
        self.semantic_memory = {
            "conversation": [],
            "learning": [],
            "preferences": [],
            "relationships": [],
            "context": [],
            "events": [],
        }
        self.memory_importance = {}
        self.memory_access_count = defaultdict(int)
        self.memory_last_access = {}
        self.consolidation_threshold = 5
        self.last_consolidation = time.time()
        self.auto_consolidate = True
        self._lock = threading.Lock()

        try:
            self.load_memories()
        except Exception as e:
            logger.warning(f"Failed to load memories, starting fresh: {e}")
            self.episodic_memory = []
            self.semantic_memory = {k: [] for k in self.semantic_memory}
            self.memory_importance = {}
            self.memory_access_count = defaultdict(int)
            self.memory_last_access = {}

        logger.info("🧠 Memory Mesh initialized")
        logger.info(f"   Working Memory: {len(self.working_memory)} items")
        logger.info(f"   Episodic Memory: {len(self.episodic_memory)} experiences")
        logger.info(
            f"   Semantic Memory: {sum(len(v) for v in self.semantic_memory.values())} facts"
        )

    def store(
        self,
        content: str,
        category: str = "auto",
        importance: float = 0.5,
        metadata: Dict = None,
    ) -> str:
        """
        Store new memory - automatically categorizes and files appropriately

        Args:
            content: The memory content (str)
            category: "auto", "conversation", "learning", "preferences", etc.
            importance: 0.0-1.0, how important this memory is
            metadata: Additional context (speaker, emotion, etc.)

        Returns:
            str: Memory ID
        """
        if not isinstance(content, str) or not content.strip():
            logger.error("Invalid content: must be non-empty string")
            raise ValueError("Content must be a non-empty string")

        if not 0.0 <= importance <= 1.0:
            logger.warning(f"Invalid importance {importance}, clamping to 0.5")
            importance = 0.5

        memory_id = self._generate_memory_id(content)
        timestamp = datetime.now().isoformat()

        memory = {
            "id": memory_id,
            "content": content.strip(),
            "timestamp": timestamp,
            "importance": importance,
            "metadata": metadata or {},
            "access_count": 0,
            "last_access": timestamp,
        }

        if category == "auto":
            category = self._auto_categorize(content, metadata)
        elif category not in self.semantic_memory and category != "episodic":
            logger.warning(f"Invalid category {category}, defaulting to context")
            category = "context"

        memory["category"] = category

        with self._lock:
            self.working_memory.append(memory)
            self.memory_importance[memory_id] = importance

            if len(self.working_memory) > self.working_memory_limit:
                self._consolidate_overflow()

        logger.info(f"💾 Stored: [{category}] {content[:50]}...")
        return memory_id

    def _auto_categorize(self, content: str, metadata: Dict = None) -> str:
        """Automatically categorize memory content"""
        content_lower = content.lower()
        metadata = metadata or {}

        if metadata.get("type") in self.semantic_memory:
            return metadata["type"]
        if metadata.get("speaker"):
            return "conversation"

        if any(
            word in content_lower
            for word in ["remember", "recall", "told me", "said that"]
        ):
            return "conversation"
        if any(
            word in content_lower
            for word in ["learn", "understand", "know", "fact", "information"]
        ):
            return "learning"
        if any(
            word in content_lower
            for word in ["like", "prefer", "favorite", "love", "hate"]
        ):
            return "preferences"
        if any(
            word in content_lower
            for word in ["meet", "person", "friend", "family", "colleague"]
        ):
            return "relationships"
        if any(
            word in content_lower
            for word in ["happened", "event", "milestone", "achievement"]
        ):
            return "events"

        return "context"

    def _consolidate_overflow(self):
        """Consolidate working memory when it's too full"""
        with self._lock:
            sorted_memories = sorted(
                self.working_memory,
                key=lambda m: (m["importance"], m["timestamp"]),
                reverse=False,
            )

            while len(self.working_memory) > self.working_memory_limit:
                memory = sorted_memories.pop(0)
                self._consolidate_memory(memory)
                self.working_memory.remove(memory)

    def consolidate_all(self, force: bool = False):
        """Consolidate all working memory to long-term storage"""
        with self._lock:
            if not force and len(self.working_memory) < self.consolidation_threshold:
                return

            logger.info("🌙 Consolidating memories...")
            consolidated_count = len(self.working_memory)
            for memory in self.working_memory[:]:
                self._consolidate_memory(memory)

            self.working_memory.clear()
            self.last_consolidation = time.time()
            self.save_memories()

            logger.info(f"✅ Consolidated {consolidated_count} memories")

    def _consolidate_memory(self, memory: Dict):
        """Move a memory from working to long-term storage"""
        with self._lock:
            category = memory.get("category", "context")
            self.episodic_memory.append(memory)
            if category in self.semantic_memory:
                self.semantic_memory[category].append(memory)
            else:
                self.semantic_memory["context"].append(memory)

            memory_id = memory["id"]
            self.memory_last_access[memory_id] = datetime.now().isoformat()

    def _start_consolidation_thread(self):
        """Start background thread for automatic consolidation"""

        def consolidation_loop():
            while self.auto_consolidate:
                time.sleep(300)
                with self._lock:
                    if len(self.working_memory) >= self.consolidation_threshold:
                        self.consolidate_all()

        thread = threading.Thread(target=consolidation_loop, daemon=True)
        thread.start()
        logger.info("🔄 Auto-consolidation thread started")

    def retrieve(
        self, query: str, category: Optional[str] = None, limit: int = 5
    ) -> List[Dict]:
        """
        Retrieve relevant memories based on query

        Args:
            query: Search query (str)
            category: Optional category filter
            limit: Max number of results (int)

        Returns:
            List of relevant memories
        """
        if not isinstance(query, str) or not query.strip():
            logger.error("Invalid query: must be non-empty string")
            raise ValueError("Query must be a non-empty string")

        if not isinstance(limit, int) or limit < 1:
            logger.warning(f"Invalid limit {limit}, defaulting to 5")
            limit = 5

        query_lower = query.lower()
        results = []

        with self._lock:
            for memory in self.working_memory:
                score = self._calculate_relevance(memory, query_lower)
                if score > 0:
                    results.append((score, memory))
                    self._mark_accessed(memory["id"])

            for memory in self.episodic_memory:
                if category and memory.get("category") != category:
                    continue
                score = self._calculate_relevance(memory, query_lower)
                if score > 0:
                    results.append((score, memory))
                    self._mark_accessed(memory["id"])

            categories_to_search = (
                [category] if category else self.semantic_memory.keys()
            )
            for cat in categories_to_search:
                for memory in self.semantic_memory.get(cat, []):
                    score = self._calculate_relevance(memory, query_lower)
                    if score > 0:
                        results.append((score, memory))
                        self._mark_accessed(memory["id"])

        results.sort(key=lambda x: x[0], reverse=True)
        logger.info(f"🔍 Retrieved {len(results[:limit])} memories for query '{query}'")
        return [memory for score, memory in results[:limit]]

    def get_working_memory(self) -> List[Dict]:
        """Return current working memory"""
        with self._lock:
            return self.working_memory[:]

    def get_recent_memories(self, hours: int = 2, limit: int = 10) -> List[Dict]:
        """
        Get memories from the last N hours

        Args:
            hours: Number of hours to look back
            limit: Max number of memories to return

        Returns:
            List of recent memories
        """
        with self._lock:
            cutoff = datetime.now() - timedelta(hours=hours)
            recent = [
                mem
                for mem in self.episodic_memory + self.working_memory
                if datetime.fromisoformat(mem["timestamp"]) >= cutoff
            ]
            recent.sort(key=lambda x: x["timestamp"], reverse=True)
            return recent[:limit]

    def get_by_category(self, category: str, limit: int = 5) -> List[Dict]:
        """
        Get memories from a specific category

        Args:
            category: Memory category
            limit: Max number of memories to return

        Returns:
            List of memories in the category
        """
        if not isinstance(category, str) or not category.strip():
            logger.error("Invalid category: must be non-empty string")
            raise ValueError("Category must be a non-empty string")

        with self._lock:
            if category in self.semantic_memory:
                return self.semantic_memory[category][-limit:]
            return []

    def _calculate_relevance(self, memory: Dict, query: str) -> float:
        """Calculate memory relevance to query"""
        score = 0.0
        content = memory["content"].lower()

        query_words = query.split()
        matches = sum(1 for word in query_words if word in content)
        score += (matches / len(query_words)) * 0.5

        if query in content:
            score += 0.3

        importance = memory.get("importance", 0.5)
        score += importance * 0.2

        timestamp = datetime.fromisoformat(memory["timestamp"])
        age_hours = (datetime.now() - timestamp).total_seconds() / 3600
        recency_score = max(0, 1 - (age_hours / (24 * 7)))
        score += recency_score * 0.1

        access_count = self.memory_access_count.get(memory["id"], 0)
        frequency_score = min(1.0, access_count / 10)
        score += frequency_score * 0.1

        return score

    def _mark_accessed(self, memory_id: str):
        """Mark memory as accessed"""
        with self._lock:
            self.memory_access_count[memory_id] += 1
            self.memory_last_access[memory_id] = datetime.now().isoformat()

    def save_memories(self):
        """Save all memories to disk with encryption"""
        try:
            with self._lock:
                episodic_file = self.memory_dir / "episodic_memory.json"
                data = json.dumps(self.episodic_memory, indent=2).encode()
                if self.cipher:
                    data = self.cipher.encrypt(data)
                with open(episodic_file, "wb") as f:
                    f.write(data)

                semantic_file = self.memory_dir / "semantic_memory.json"
                data = json.dumps(self.semantic_memory, indent=2).encode()
                if self.cipher:
                    data = self.cipher.encrypt(data)
                with open(semantic_file, "wb") as f:
                    f.write(data)

                metadata = {
                    "importance": self.memory_importance,
                    "access_count": dict(self.memory_access_count),
                    "last_access": self.memory_last_access,
                }
                metadata_file = self.memory_dir / "memory_metadata.json"
                data = json.dumps(metadata, indent=2).encode()
                if self.cipher:
                    data = self.cipher.encrypt(data)
                with open(metadata_file, "wb") as f:
                    f.write(data)

                logger.info("💾 Memories saved to disk")
        except Exception as e:
            logger.error(f"⚠️ Error saving memories: {e}")
            raise

    def load_memories(self):
        """Load memories from disk with decryption"""
        try:
            with self._lock:
                episodic_file = self.memory_dir / "episodic_memory.json"
                if episodic_file.exists():
                    with open(episodic_file, "rb") as f:
                        data = f.read()
                        if self.cipher:
                            try:
                                data = self.cipher.decrypt(data)
                            except Exception as e:
                                logger.error(
                                    f"Decryption failed for episodic memory: {e}"
                                )
                                raise
                        self.episodic_memory = json.loads(data.decode())

                semantic_file = self.memory_dir / "semantic_memory.json"
                if semantic_file.exists():
                    with open(semantic_file, "rb") as f:
                        data = f.read()
                        if self.cipher:
                            try:
                                data = self.cipher.decrypt(data)
                            except Exception as e:
                                logger.error(
                                    f"Decryption failed for semantic memory: {e}"
                                )
                                raise
                        self.semantic_memory = json.loads(data.decode())

                metadata_file = self.memory_dir / "memory_metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, "rb") as f:
                        data = f.read()
                        if self.cipher:
                            try:
                                data = self.cipher.decrypt(data)
                            except Exception as e:
                                logger.error(f"Decryption failed for metadata: {e}")
                                raise
                        metadata = json.loads(data.decode())
                        self.memory_importance = metadata.get("importance", {})
                        self.memory_access_count = defaultdict(
                            int, metadata.get("access_count", {})
                        )
                        self.memory_last_access = metadata.get("last_access", {})

                logger.info("📂 Memories loaded from disk")
        except Exception as e:
            logger.error(f"⚠️ Error loading memories: {e}")
            raise

    def get_stats(self) -> Dict:
        """Get memory system statistics"""
        with self._lock:
            return {
                "working_memory_count": len(self.working_memory),
                "episodic_memory_count": len(self.episodic_memory),
                "semantic_memory_count": sum(
                    len(v) for v in self.semantic_memory.values()
                ),
                "total_memories": len(self.working_memory) + len(self.episodic_memory),
                "categories": {k: len(v) for k, v in self.semantic_memory.items()},
                "last_consolidation": datetime.fromtimestamp(
                    self.last_consolidation
                ).isoformat(),
            }

    def clear_all(self, confirm: bool = False):
        """Clear all memories (use with caution!)"""
        if not confirm:
            logger.warning("⚠️ Must confirm to clear all memories")
            return

        with self._lock:
            self.working_memory.clear()
            self.episodic_memory.clear()
            self.semantic_memory = {k: [] for k in self.semantic_memory}
            self.memory_importance.clear()
            self.memory_access_count.clear()
            self.memory_last_access.clear()
            logger.info("🗑️ All memories cleared")

    def _generate_memory_id(self, content: str) -> str:
        """Generate unique ID for memory"""
        timestamp = datetime.now().isoformat()
        raw = f"{content}{timestamp}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]


if __name__ == "__main__":
    print("🧠 Memory Mesh - Human-Like Memory System")
    print("=" * 60)

    try:
        memory = MemoryMesh()
    except Exception as e:
        print(f"Failed to initialize MemoryMesh: {e}")
        exit(1)

    try:
        memory.store(
            "Everett is the creator of The Christman AI Project",
            category="relationships",
            importance=1.0,
            metadata={"type": "core_identity"},
        )

        memory.store(
            "BROCKSTON helps nonverbal people communicate",
            category="learning",
            importance=0.9,
            metadata={"project": "BROCKSTON"},
        )

        memory.store(
            "User prefers Python for backend development",
            category="preferences",
            importance=0.7,
        )

        memory.store("Just discussed memory consolidation systems", importance=0.6)
    except Exception as e:
        print(f"Failed to store memories: {e}")
        exit(1)

    print("\n🔍 Searching for 'Everett'...")
    try:
        results = memory.retrieve("Everett")
        if not results:
            print("  No memories found for 'Everett'")
        for mem in results:
            print(f"  • [{mem['category']}] {mem['content']}")
    except Exception as e:
        print(f"Failed to retrieve memories: {e}")

    print("\n📊 Memory Stats:")
    try:
        stats = memory.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"Failed to get stats: {e}")

    try:
        memory.save_memories()
    except Exception as e:
        print(f"Failed to save memories: {e}")

    print("\n✅ Memory Mesh test complete!")

# ==============================================================================
# © 2025 Everett Nathaniel Christman
# The Christman AI Project — Luma Cognify AI
# All rights reserved. Unauthorized use, replication, or derivative training
# of this material is prohibited.
#
# Core Directive: "How can I help you love yourself more?"
# Autonomy & Alignment Protocol v3.0
# ==============================================================================
