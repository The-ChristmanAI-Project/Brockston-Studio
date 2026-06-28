"""
voice_command_loop.py — Brockston Studio Voice Command Daemon
Part of The Christman AI Project | Luma Cognify AI

Polls Hermes bridge (localhost:8765/latest) for transcribed speech,
parses it into IDE or chat commands, and routes to Brockston Studio API.
Speaks responses back via macOS say.

Run:   python3 voice_command_loop.py
Stop:  SIGTERM / Ctrl+C
Log:   ~/Library/Logs/voice_command_loop.log
"""

# ── Christman AI Project Header ────────────────────────────────────────────
# Project  : The Christman AI Project / Luma Cognify AI
# File     : voice_command_loop.py
# Purpose  : Voice-driven command loop for Brockston Studio
# Author   : Everett Nathaniel Christman
# License  : Proprietary — All Rights Reserved © 2026
# Patent   : Pending TCAP-2026-001
# ──────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import json
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import httpx

# ── Logging setup ─────────────────────────────────────────────────────────
LOG_PATH = Path.home() / "Library" / "Logs" / "voice_command_loop.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [VCL] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("voice_command_loop")

# ── Config ─────────────────────────────────────────────────────────────────
HERMES_URL      = "http://localhost:8765/latest"
BROCKSTON_URL   = "http://localhost:8000"
POLL_INTERVAL   = 0.5   # seconds between Hermes polls
MIN_TEXT_LEN    = 3     # ignore utterances shorter than this
SPEAK_RESPONSES = True  # set False to silence TTS output

# Commands that map directly to IDE actions (checked before chat fallback)
IDE_COMMAND_MAP = {
    "open file":       "open_file",
    "switch to":       "switch_tab",
    "close tab":       "close_tab",
    "use claude":      ("set_instructor", {"instructor": "claude"}),
    "use kimi":        ("set_instructor", {"instructor": "kimi"}),
    "use nemo":        ("set_instructor", {"instructor": "nemo"}),
    "use brockston":   ("set_instructor", {"instructor": "brockston"}),
    "use family":      ("set_instructor", {"instructor": "family"}),
    "list files":      ("list_files", {}),
    "show files":      ("list_files", {}),
}

_running = True
_last_text: str = ""
_last_timestamp: str = ""


# ── TTS ────────────────────────────────────────────────────────────────────
def speak(text: str) -> None:
    """Speak text via macOS say. Non-blocking."""
    if not SPEAK_RESPONSES:
        return
    try:
        subprocess.Popen(["say", "-v", "Samantha", text])
    except Exception as e:
        logger.warning(f"TTS failed: {e}")


# ── Hermes poll ────────────────────────────────────────────────────────────
def poll_hermes() -> tuple[str, str]:
    """
    Fetch latest transcribed text from Hermes bridge.
    Returns (text, timestamp). Empty strings on failure.
    """
    try:
        r = httpx.get(HERMES_URL, timeout=1.5)
        data = r.json()
        text = (data.get("text") or "").strip()
        ts   = str(data.get("timestamp") or data.get("ts") or "")
        return text, ts
    except Exception:
        return "", ""


# ── Command parser ─────────────────────────────────────────────────────────
def parse_command(text: str) -> dict | None:
    """
    Check if text matches a known IDE command.
    Returns {action, params} dict or None (falls through to chat).
    """
    lower = text.lower().strip()

    for trigger, mapping in IDE_COMMAND_MAP.items():
        if lower.startswith(trigger):
            if isinstance(mapping, tuple):
                action, params = mapping
                return {"action": action, "params": params}
            # extract trailing argument (e.g. "open file main.py" → path=main.py)
            arg = text[len(trigger):].strip()
            return {"action": mapping, "params": {"path": arg} if arg else {}}

    return None  # not an IDE command — route to chat


# ── Dispatch ────────────────────────────────────────────────────────────────
def dispatch_ide_command(action: str, params: dict) -> str:
    """POST to /api/ide/command. Returns response text."""
    try:
        r = httpx.post(
            f"{BROCKSTON_URL}/api/ide/command",
            json={"action": action, "params": params},
            timeout=5.0,
        )
        data = r.json()
        return data.get("note") or data.get("message") or f"Done — {action}"
    except Exception as e:
        logger.error(f"IDE command failed: {e}")
        return "Command failed. Check Brockston is running."


def dispatch_chat(text: str) -> str:
    """POST to /api/chat. Returns Brockston's reply text."""
    try:
        r = httpx.post(
            f"{BROCKSTON_URL}/api/chat",
            json={"message": text},
            timeout=30.0,
        )
        data = r.json()
        # response field varies by provider
        reply = (
            data.get("response")
            or data.get("content")
            or data.get("message")
            or data.get("text")
            or "Got it."
        )
        return str(reply).strip()
    except Exception as e:
        logger.error(f"Chat dispatch failed: {e}")
        return "I couldn't reach Brockston. Is the server running?"


# ── Process one utterance ───────────────────────────────────────────────────
def process(text: str) -> None:
    logger.info(f"Voice input: {text!r}")

    cmd = parse_command(text)
    if cmd:
        logger.info(f"IDE command → {cmd['action']} {cmd['params']}")
        reply = dispatch_ide_command(cmd["action"], cmd["params"])
    else:
        logger.info("Routing to chat")
        reply = dispatch_chat(text)

    logger.info(f"Response: {reply[:120]}")
    speak(reply)


# ── Main loop ───────────────────────────────────────────────────────────────
def shutdown(sig, frame):
    global _running
    logger.info("Shutdown signal received — voice command loop stopping.")
    speak("Voice loop stopping.")
    _running = False


def main() -> None:
    global _last_text, _last_timestamp

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    logger.info("=" * 60)
    logger.info("Brockston Studio — Voice Command Loop STARTED")
    logger.info(f"Hermes : {HERMES_URL}")
    logger.info(f"Studio : {BROCKSTON_URL}")
    logger.info(f"Poll   : {POLL_INTERVAL}s")
    logger.info("=" * 60)

    speak("Voice command loop online. I'm listening.")

    while _running:
        text, ts = poll_hermes()

        # Only process if text is new, non-empty, and long enough
        if (
            text
            and len(text) >= MIN_TEXT_LEN
            and text != _last_text
            and ts != _last_timestamp
        ):
            _last_text = text
            _last_timestamp = ts
            try:
                process(text)
            except Exception as e:
                logger.error(f"Processing error: {e}", exc_info=True)

        time.sleep(POLL_INTERVAL)

    logger.info("Voice command loop STOPPED.")


if __name__ == "__main__":
    main()
