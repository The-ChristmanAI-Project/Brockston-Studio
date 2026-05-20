#!/usr/bin/env python3
"""
MEMORY ENGINE v4.0.0
====================

Single source of truth for conversation memory.

Consolidates:
- long-term history (JSON on disk)
- short-term episodic buffer (RAM only)
- discrete learned facts (knowledge base sidecar)
- hooks for observers to react without reading raw memory

Cardinal rules:
- Never fabricate memory. Never invent history.
- Fail loud if storage fails.
- No keys in code. Encryption key from environment only.
- No cross-being side doors. Observers see events, not raw memory.
"""

import json
import logging
import os
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Optional dependency: cryptography
try:
    from cryptography.fernet import Fernet, InvalidToken

    _FERNET_AVAILABLE = True
except ImportError:
    _FERNET_AVAILABLE = False
    logger.warning(
        "cryptography package not installed — encryption support disabled. "
        "Install with: pip install cryptography"
    )

_EPISODIC_MAX = 50          # Hard cap on the short-term session buffer
_BACKUP_EVERY_N_SAVES = 10  # Auto-backup frequency


class MemoryEngine:
    """
    Central memory engine.

    Responsibilities:
        1. Persist and load long-term conversation history (JSON on disk).
        2. Maintain a short-term episodic buffer (in RAM, cleared per session).
        3. Provide keyword-based retrieval with optional intent-type scoring.
        4. Store and recall discrete learned facts (knowledge base sidecar).
        5. Auto-backup to a .bak file every N saves.
        6. Fire registered hooks on key events so observers can react.
        7. Optionally encrypt all disk writes with a Fernet key from env.
        8. Protect all write operations with a threading.Lock.

    This engine:
        - never shares internal data structures with other systems;
          hooks receive small metadata payloads only.
        - never fabricates or guesses stored memories.
        - never accepts an encryption key from code or disk; env-only.
    """

    def __init__(
        self,
        file_path: str = "./memory/semantic_memory.json",
        encryption_key: Optional[str] = None,
    ) -> None:
        """
        Initialise the memory engine.

        Args:
            file_path:
                Path to the primary JSON memory file. Relative paths starting
                with "./" are resolved against the project root (two levels above
                this module's directory).
            encryption_key:
                Ignored if provided; kept only for call-site compatibility.
                The real key is read exclusively from MEMORY_ENCRYPTION_KEY
                in the environment.
        """
        if encryption_key is not None:
            logger.warning(
                "MemoryEngine.__init__: 'encryption_key' argument was provided but "
                "will be ignored. Keys must come from the environment variable "
                "MEMORY_ENCRYPTION_KEY."
            )

        # Path resolution
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_root = os.path.dirname(backend_dir)

        if file_path.startswith("./"):
            self.file_path = os.path.join(project_root, file_path[2:])
        elif not os.path.isabs(file_path):
            self.file_path = os.path.join(project_root, file_path)
        else:
            self.file_path = file_path

        base, ext = os.path.splitext(self.file_path)
        self._kb_path = f"{base}_kb{ext}"

        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

        self._lock: threading.Lock = threading.Lock()
        self._memory: List[Dict[str, Any]] = []
        self._episodic: deque = deque(maxlen=_EPISODIC_MAX)
        self._knowledge: Dict[str, Dict[str, str]] = {}
        self._hooks: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {
            "on_save": [],
            "on_crisis_detected": [],
            "on_session_clear": [],
        }
        self._save_count: int = 0

        self._fernet = self._init_encryption()

        self.load_memory()
        self._load_knowledge()

    # ------------------------------------------------------------------
    # Encryption
    # ------------------------------------------------------------------

    def _init_encryption(self) -> Optional[Any]:
        """
        Read MEMORY_ENCRYPTION_KEY from the environment and return a Fernet
        instance, or None if unset.
        """
        raw_key = os.environ.get("MEMORY_ENCRYPTION_KEY")
        if not raw_key:
            logger.debug("MEMORY_ENCRYPTION_KEY not set — using plaintext storage.")
            return None
        if not _FERNET_AVAILABLE:
            raise RuntimeError(
                "MEMORY_ENCRYPTION_KEY is set but 'cryptography' is not installed. "
                "Install with: pip install cryptography"
            )
        try:
            fernet = Fernet(raw_key.encode())
            logger.info("Memory encryption enabled (Fernet).")
            return fernet
        except Exception as exc:
            raise ValueError(
                f"MEMORY_ENCRYPTION_KEY is set but is not a valid Fernet key: {exc}"
            ) from exc

    def _encrypt_payload(self, payload: str) -> str:
        """
        Encrypt a plaintext string with the configured Fernet key.

        Returns the ciphertext as a UTF-8 string. If no key is configured,
        returns the payload unchanged.
        """
        if self._fernet is None:
            return payload
        return self._fernet.encrypt(payload.encode()).decode()

    def _decrypt_payload(self, payload: str) -> str:
        """
        Decrypt a ciphertext string. On failure, logs and returns the raw
        payload so reads can degrade gracefully instead of crashing.
        """
        if self._fernet is None:
            return payload
        try:
            return self._fernet.decrypt(payload.encode()).decode()
        except InvalidToken as exc:
            logger.error(
                "Memory decryption failed (invalid token or wrong key). "
                "Returning raw payload. Detail: %s",
                exc,
            )
            return payload
        except Exception as exc:
            logger.error(
                "Unexpected error during memory decryption: %s. "
                "Returning raw payload.",
                exc,
            )
            return payload

    # ------------------------------------------------------------------
    # Disk I/O — long-term memory
    # ------------------------------------------------------------------

    def load_memory(self) -> None:
        """
        Load long-term memory entries from disk.

        Handles legacy dict format and converts it to the current list format.
        On failure, starts with an empty memory list rather than fabricating.
        """
        if not os.path.exists(self.file_path):
            logger.info("No existing memory file found, starting fresh.")
            self._memory = []
            return

        try:
            with open(self.file_path, "r", encoding="utf-8") as fh:
                raw = fh.read()

            raw = self._decrypt_payload(raw)
            data = json.loads(raw)

            if isinstance(data, dict):
                logger.info("Converting legacy dict memory format to list format.")
                legacy_entries: List[Dict[str, Any]] = []

                for legacy_key, entry_type in [
                    ("identity", "identity"),
                    ("everett_profile", "everett_profile"),
                    ("brockston_capabilities", "capabilities"),
                    ("relationship_with_everett", "relationship"),
                    ("tech_stack", "tech_stack"),
                ]:
                    if legacy_key in data:
                        legacy_entries.append({"type": entry_type, **data[legacy_key]})

                if "mission_statement" in data:
                    legacy_entries.append(
                        {"type": "mission", "statement": data["mission_statement"]}
                    )

                for _key, value in data.items():
                    if isinstance(value, list):
                        legacy_entries.extend(value)

                self._memory = legacy_entries
                self.save_memory()
                logger.info("Converted and saved %d memory entries.", len(self._memory))

            elif isinstance(data, list):
                self._memory = data
                logger.info("Loaded %d memory entries.", len(self._memory))
            else:
                logger.error(
                    "Unexpected memory file format: %s. Starting fresh.",
                    type(data).__name__,
                )
                self._memory = []

        except json.JSONDecodeError as exc:
            logger.error(
                "Memory file contains invalid JSON and cannot be loaded: %s. "
                "Starting fresh.",
                exc,
            )
            self._memory = []
        except OSError as exc:
            logger.error(
                "OS error reading memory file '%s': %s. Starting fresh.",
                self.file_path,
                exc,
            )
            self._memory = []
        except Exception as exc:
            logger.error(
                "Unexpected error loading memory file: %s. Starting fresh.", exc
            )
            self._memory = []

    def save_memory(self) -> None:
        """
        Persist long-term memory to disk.

        Thread-safe. Increments an internal save counter and triggers
        auto-backup on every Nth save. Fires 'on_save' hook after success.
        """
        with self._lock:
            try:
                payload = json.dumps(self._memory, indent=2)
                payload = self._encrypt_payload(payload)
                with open(self.file_path, "w", encoding="utf-8") as fh:
                    fh.write(payload)
                logger.info("Saved %d memory entries.", len(self._memory))
            except OSError as exc:
                logger.error(
                    "CRITICAL: Failed to save memory to '%s': %s",
                    self.file_path,
                    exc,
                )
                raise

            self._save_count += 1
            if self._save_count % _BACKUP_EVERY_N_SAVES == 0:
                self._auto_backup()

        self._fire_hook("on_save", {"entry_count": len(self._memory)})

    def _auto_backup(self) -> None:
        """
        Write a .bak copy of the memory file.

        Backup failures are warning-logged only and never raise.
        """
        bak_path = self.file_path + ".bak"
        try:
            payload = json.dumps(self._memory, indent=2)
            payload = self._encrypt_payload(payload)
            with open(bak_path, "w", encoding="utf-8") as fh:
                fh.write(payload)
            logger.debug("Auto-backup written to '%s'.", bak_path)
        except Exception as exc:
            logger.warning(
                "Auto-backup to '%s' failed (non-fatal): %s", bak_path, exc
            )

    # ------------------------------------------------------------------
    # Disk I/O — knowledge base
    # ------------------------------------------------------------------

    def _load_knowledge(self) -> None:
        """
        Load the knowledge base from its sidecar JSON file.

        Starts with an empty KB if the file is missing or invalid.
        """
        if not os.path.exists(self._kb_path):
            logger.debug("No knowledge base file found, starting with empty KB.")
            self._knowledge = {}
            return

        try:
            with open(self._kb_path, "r", encoding="utf-8") as fh:
                raw = fh.read()
            raw = self._decrypt_payload(raw)
            self._knowledge = json.loads(raw)
            logger.info("Loaded %d knowledge base domains.", len(self._knowledge))
        except json.JSONDecodeError as exc:
            logger.error(
                "Knowledge base file contains invalid JSON: %s. Starting empty.", exc
            )
            self._knowledge = {}
        except OSError as exc:
            logger.error("OS error reading knowledge base: %s. Starting empty.", exc)
            self._knowledge = {}
        except Exception as exc:
            logger.error(
                "Unexpected error loading knowledge base: %s. Starting empty.", exc
            )
            self._knowledge = {}

    def _save_knowledge(self) -> None:
        """
        Persist the knowledge base sidecar to disk.

        Thread-safe. Logs and re-raises on write failure.
        """
        with self._lock:
            try:
                payload = json.dumps(self._knowledge, indent=2)
                payload = self._encrypt_payload(payload)
                with open(self._kb_path, "w", encoding="utf-8") as fh:
                    fh.write(payload)
                logger.debug("Knowledge base saved (%d domains).", len(self._knowledge))
            except OSError as exc:
                logger.error(
                    "Failed to save knowledge base to '%s': %s", self._kb_path, exc
                )
                raise

    # ------------------------------------------------------------------
    # Public API — save / query
    # ------------------------------------------------------------------

    def save(self, entry: Dict[str, Any]) -> None:
        """
        Save a new entry into long-term memory and persist to disk.

        Adds a UTC ISO-8601 timestamp and mirrors the entry into the
        episodic buffer.
        """
        entry = dict(entry)
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()

        with self._lock:
            self._memory.append(entry)
            self._episodic.append(entry)

        self.save_memory()
        logger.debug("Stored new memory entry: %s", entry)

    def query(self, text: str, intent: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve relevant memory entries using keyword-based scoring.

        Strategy:
            - compute keyword overlap between query and stored input/output
            - optionally boost entries whose 'intent' or 'type' fields match
            - return top 5 scoring entries, or 5 most recent if no matches
        """
        logger.debug("Querying memory for context (intent=%s): %s", intent, text)

        if not self._memory:
            return {"context": "No prior context found."}

        candidates = list(self._memory)

        query_words = set(text.lower().split())
        stop_words = {
            "the", "a", "an", "is", "was", "are", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "shall",
            "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "it", "this", "that", "and", "or", "but", "not", "so",
            "if", "then", "than", "what", "who", "how", "when", "where",
            "i", "you", "he", "she", "we", "they", "me", "my", "your",
        }
        query_keywords = query_words - stop_words

        scored: List[tuple[int, Dict[str, Any]]] = []
        for entry in candidates:
            entry_text = (
                f"{entry.get('input', '')} {entry.get('output', '')}"
            ).lower()
            entry_words = set(entry_text.split())
            score = len(query_keywords & entry_words)

            if intent and (
                entry.get("intent") == intent or entry.get("type") == intent
            ):
                score += 3

            scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)

        if scored and scored[0][0] > 0:
            relevant = [entry for _score, entry in scored[:5]]
        else:
            relevant = candidates[-5:]

        context_snippets = [
            f"{m.get('input', '')} -> {m.get('output', '')}" for m in relevant
        ]
        return {"context": "\n".join(context_snippets)}

    # ------------------------------------------------------------------
    # Episodic buffer
    # ------------------------------------------------------------------

    def get_episodic(self) -> List[Dict[str, Any]]:
        """
        Return a snapshot of the current session's short-term episodic buffer.
        """
        return list(self._episodic)

    def forget_session(self) -> None:
        """
        Clear the short-term episodic buffer for the current session.

        Long-term memory and knowledge base are not affected.
        """
        with self._lock:
            self._episodic.clear()
        logger.info("Episodic session buffer cleared.")
        self._fire_hook("on_session_clear", {})

    # ------------------------------------------------------------------
    # Knowledge base
    # ------------------------------------------------------------------

    def learn(self, key: str, value: str, domain: str = "general") -> None:
        """
        Store a discrete learned fact in the knowledge base.

        Facts are separate from conversation history and never returned by
        query(); use recall_fact() instead.
        """
        with self._lock:
            if domain not in self._knowledge:
                self._knowledge[domain] = {}
            if key in self._knowledge[domain]:
                logger.debug(
                    "Knowledge base: overwriting existing fact [%s/%s].", domain, key
                )
            self._knowledge[domain][key] = value

        self._save_knowledge()
        logger.debug("Learned fact [%s/%s] = %r", domain, key, value)

    def recall_fact(self, key: str, domain: Optional[str] = None) -> Optional[str]:
        """
        Retrieve a learned fact by key, optionally restricted to a domain.
        """
        if domain is not None:
            return self._knowledge.get(domain, {}).get(key)

        for _, facts in self._knowledge.items():
            if key in facts:
                return facts[key]

        return None

    # ------------------------------------------------------------------
    # Hooks
    # ------------------------------------------------------------------

    def register_hook(self, event: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register an observer callback for a named memory event.

        Supported events:
            - on_save
            - on_crisis_detected
            - on_session_clear

        Callbacks receive a single dict argument with metadata.
        """
        if event not in self._hooks:
            raise ValueError(
                f"Unknown hook event '{event}'. Valid events: {list(self._hooks.keys())}"
            )
        self._hooks[event].append(callback)
        logger.debug("Registered hook for event '%s'.", event)

    def _fire_hook(self, event: str, payload: Dict[str, Any]) -> None:
        """
        Invoke all registered callbacks for the given event.

        Callback failures are warning-logged and do not propagate.
        """
        for callback in self._hooks.get(event, []):
            try:
                callback(payload)
            except Exception as exc:
                logger.warning(
                    "Hook callback for event '%s' raised an exception (non-fatal): %s",
                    event,
                    exc,
                )

    def fire_crisis_hook(self, context: Dict[str, Any]) -> None:
        """
        Manually fire the 'on_crisis_detected' hook with a context payload.
        """
        logger.warning("Crisis hook fired. Context keys: %s", list(context.keys()))
        self._fire_hook("on_crisis_detected", context)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def get_recent_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Return the most recent long-term memory events, newest first.
        """
        return list(reversed(self._memory[-limit:]))

    def clear(self) -> None:
        """
        Erase ALL long-term memory and the knowledge base.

        Use with extreme caution. Writes empty memory/KB to disk and clears
        the episodic buffer. Fires 'on_session_clear' and 'on_save' hooks.
        """
        with self._lock:
            self._memory = []
            self._episodic.clear()
            self._knowledge = {}

        self.save_memory()
        self._save_knowledge()
        logger.warning("All long-term memory and knowledge base have been cleared.")
        self._fire_hook("on_session_clear", {"reason": "full_clear"})


__all__ = [
    "MemoryEngine",
]


# ==============================================================================
# Patent Pending
# Christman-AI Family
# Shared-neutral implementation for internal system use.
# Core Directive: "How can I help you love yourself more?"
# ==============================================================================
