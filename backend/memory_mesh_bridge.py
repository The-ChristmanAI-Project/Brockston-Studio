"""
Memory Mesh Bridge - Adapter for BROCKSTON Ultimate Voice
Allows seamless integration of MemoryMesh with existing BROCKSTON code
"""

try:
    from backend.memory_mesh import MemoryMesh
except ImportError:
    # Backend module doesn't exist - create stub
    class MemoryMesh:
        def __init__(self, *args, **kwargs):
            pass

        def store(self, *args, **kwargs):
            pass

        def retrieve(self, *args, **kwargs):
            return None


from typing import Any, Dict, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("logs/memory_mesh_bridge.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class MemoryMeshBridge:
    """
    Bridge adapter to make MemoryMesh compatible with existing BROCKSTON code
    Provides the same interface as old MemoryManager but with MemoryMesh power
    """

    def __init__(
        self,
        memory_dir: str = "./brockston_memory",
        encryption_key: Optional[bytes] = None,
    ):
        """
        Initialize MemoryMesh with bridge interface

        Args:
            memory_dir: Directory for memory files
            encryption_key: Optional Fernet key for encryption
        """
        try:
            self.mesh = MemoryMesh(memory_dir=memory_dir, encryption_key=encryption_key)
            self.memory_file = self.mesh.memory_dir / "persistent_memory.json"
            logger.info("🧠 Memory Mesh Bridge initialized")
        except Exception as e:
            logger.error(f"Failed to initialize MemoryMesh: {e}")
            raise RuntimeError(f"Cannot initialize MemoryMeshBridge: {e}")

    def load(self):
        """Load memories (already done in MemoryMesh.__init__)"""
        if not hasattr(self, "mesh") or self.mesh is None:
            logger.error("MemoryMesh not initialized")
            raise RuntimeError("MemoryMesh not initialized")
        try:
            self.mesh.load_memories()
            logger.info("🧠 Memory Mesh Bridge loaded")
        except Exception as e:
            logger.error(f"Failed to load memories: {e}")
            raise

    def save(self):
        """Save memories to disk - consolidate working memory first"""
        if not hasattr(self, "mesh") or self.mesh is None:
            logger.error("MemoryMesh not initialized")
            raise RuntimeError("MemoryMesh not initialized")
        try:
            self.mesh.consolidate_all(force=True)
            self.mesh.save_memories()
            logger.info("💾 Memories saved via bridge")
        except Exception as e:
            logger.error(f"Failed to save memories: {e}")
            raise

    def store(self, key: str, value: Any):
        """
        Store a memory - intelligently categorizes and manages

        Args:
            key: Memory key/identifier (str)
            value: Memory value/content
        """
        if not hasattr(self, "mesh") or self.mesh is None:
            logger.error("MemoryMesh not initialized")
            raise RuntimeError("MemoryMesh not initialized")
        if not isinstance(key, str) or not key.strip():
            logger.error("Invalid key: must be non-empty string")
            raise ValueError("Key must be a non-empty string")

        content = f"{key}: {str(value)}"
        importance = 0.5

        if any(
            word in str(value).lower()
            for word in ["learn", "important", "remember", "critical"]
        ):
            importance = 0.8

        try:
            self.mesh.store(
                content=content,
                category="auto",
                importance=importance,
                metadata={"key": key},
            )
            logger.info(f"💾 Stored memory: {content[:50]}...")
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise

    def retrieve_relevant(self, query: str) -> str:
        """
        Retrieve memories relevant to query

        Args:
            query: Search query (str)

        Returns:
            Formatted string of relevant memories
        """
        if not hasattr(self, "mesh") or self.mesh is None:
            logger.error("MemoryMesh not initialized")
            raise RuntimeError("MemoryMesh not initialized")
        if not isinstance(query, str) or not query.strip():
            logger.error("Invalid query: must be non-empty string")
            return ""

        try:
            results = self.mesh.retrieve(query, limit=5)
            if not results:
                logger.info(f"No memories found for query '{query}'")
                return ""

            formatted = []
            for mem in results:
                content = mem["content"]
                category = mem.get("category", "context")
                formatted.append(f"[{category}] {content}")

            logger.info(f"Retrieved {len(formatted)} memories for query '{query}'")
            return " | ".join(formatted)
        except Exception as e:
            logger.error(f"Failed to retrieve memories for query '{query}': {e}")
            return ""

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about BROCKSTON's memory"""
        if not hasattr(self, "mesh") or self.mesh is None:
            logger.error("MemoryMesh not initialized")
            return {}
        try:
            stats = self.mesh.get_stats()
            stats["memory_file_exists"] = self.memory_file.exists()

            access_counts = self.mesh.memory_access_count
            if access_counts:
                top_accessed = sorted(
                    access_counts.items(), key=lambda x: x[1], reverse=True
                )[:5]
                stats["most_accessed"] = [mem_id for mem_id, _ in top_accessed]
            else:
                stats["most_accessed"] = []

            stats["long_term_memories"] = stats["episodic_memory_count"]
            stats["session_memories"] = stats["working_memory_count"]
            stats["recent_conversations"] = len(self.mesh.get_recent_memories(hours=24))

            return stats
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {}

    def get_working_context(self) -> str:
        """Get current working memory as context string"""
        if not hasattr(self, "mesh") or self.mesh is None:
            logger.error("MemoryMesh not initialized")
            return ""
        try:
            working = self.mesh.get_working_memory()
            if not working:
                return ""

            context_parts = [mem["content"] for mem in working]
            return " | ".join(context_parts)
        except Exception as e:
            logger.error(f"Failed to get working context: {e}")
            return ""

    def get_recent_context(self, hours: int = 2) -> str:
        """
        Get recent conversation context

        Args:
            hours: How many hours back to retrieve

        Returns:
            Formatted string of recent memories
        """
        if not hasattr(self, "mesh") or self.mesh is None:
            logger.error("MemoryMesh not initialized")
            return ""
        try:
            recent = self.mesh.get_recent_memories(hours=hours, limit=10)
            if not recent:
                return ""

            context_parts = [mem["content"] for mem in recent]
            return " | ".join(context_parts)
        except Exception as e:
            logger.error(f"Failed to get recent context: {e}")
            return ""

    def consolidate(self, force: bool = False):
        """Manually trigger memory consolidation"""
        if not hasattr(self, "mesh") or self.mesh is None:
            logger.error("MemoryMesh not initialized")
            raise RuntimeError("MemoryMesh not initialized")
        try:
            self.mesh.consolidate_all(force=force)
            logger.info("✅ Consolidation triggered via bridge")
        except Exception as e:
            logger.error(f"Failed to consolidate memories: {e}")
            raise

    def get_category_context(self, category: str) -> str:
        """
        Get memories from specific category

        Args:
            category: "conversation", "learning", "preferences", etc.

        Returns:
            Formatted string of category memories
        """
        if not hasattr(self, "mesh") or self.mesh is None:
            logger.error("MemoryMesh not initialized")
            return ""
        if not isinstance(category, str) or not category.strip():
            logger.error("Invalid category: must be non-empty string")
            return ""

        try:
            memories = self.mesh.get_by_category(category, limit=5)
            if not memories:
                return ""

            context_parts = [mem["content"] for mem in memories]
            return " | ".join(context_parts)
        except Exception as e:
            logger.error(f"Failed to get category context for '{category}': {e}")
            return ""


# ==============================================================================
# © 2025 Everett Nathaniel Christman
# The Christman AI Project — Luma Cognify AI
# All rights reserved. Unauthorized use, replication, or derivative training
# of this material is prohibited.
#
# Core Directive: "How can I help you love yourself more?"
# Autonomy & Alignment Protocol v3.0
# ==============================================================================
