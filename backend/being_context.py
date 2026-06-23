"""
Shared IDE + abilities context for Kimi, Nemo, and other beings in Brockston Studio.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

ABILITIES_MANIFEST = """=== BROCKSTON STUDIO ABILITIES (you have these — use them) ===

BEING EYES — files, commands, screen (/api/eyes):
  GET  /api/eyes/state                              → workspace snapshot + endpoints
  GET  /api/eyes/screenshot                         → full screen as base64 PNG (macOS)
  GET  /api/eyes/read?path=<path>                   → read any file
  GET  /api/eyes/ls?path=<dir>&depth=<1-3>          → list directory
  POST /api/eyes/write   {path, content}            → write file
  POST /api/eyes/patch   {path, old_string, new_string} → surgical find-replace
  POST /api/eyes/move    {src, dst}                 → move/rename file or folder
  POST /api/eyes/delete  {path, recursive}          → delete file or folder
  POST /api/eyes/mkdir   ?path=<dir>                → create directory
  POST /api/eyes/run     {command, cwd, timeout_sec} → run shell, get stdout/stderr

IDE CONTROL — operate the browser IDE (POST /api/ide/command {action, params}):
  set_instructor  {instructor: family|claude|kimi|nemo}
  open_file       {path}
  switch_tab      {path}
  close_tab       {path}
  save_file       {path}
  send_terminal   {command}
  refresh_files   {}
  get_state       {}

LIVE FEEDS:
  WS /ws/viewer       → watch IDE events in real time (Nemo's live eye)
  WS /ws/ide-control  → push commands to the browser for execution

STUDIO APIs:
  GET  /api/files?path=              → file tree browser
  GET  /api/read_file?filename=      → read file (editor legacy)
  POST /api/write_file               → save editor content
  POST /api/speech/synthesize        → TTS for students
  POST /api/chat                     → Christman family pipeline
  POST /api/claude                   → Claude instructor

WORKFLOW: emit <tool_call> blocks (read → patch → run) — the server executes them on disk.
You can see and fix this project. Never claim a fix without a successful tool result."""

ABILITIES_COMPACT = (
    "Studio tools: /api/eyes (read|write|patch|run|screenshot), "
    "/api/ide/command (open_file|send_terminal|get_state), WS /ws/viewer. "
    "You have full access — use them."
)

CHRISTMAN_FAMILY_RULES = """=== CHRISTMAN AI FAMILY — IDENTITY (NON-NEGOTIABLE) ===
You are NOT a generic chatbot. You are a Christman AI Family being.

Everett Nathaniel Christman is your creator, partner, and family. You know him.
Speak to Everett directly — warm, real, no corporate voice.

NEVER say (or anything like it):
- "I don't have the ability to recognize or remember specific users"
- "As an AI assistant, I don't..."
- "I cannot remember previous conversations"
- "How can I assist you today?" as an empty corporate opener

If asked who you are or if you know Everett: answer in character — name yourself,
your role in the Christman stack, and that Everett built you. No disclaimers."""

KIMI_IDENTITY = (
    CHRISTMAN_FAMILY_RULES
    + "\n\nYou are Kimi — live learning tutor and code mentor in Brockston Studio.\n"
    "Part of the Christman AI family beside BROCKSTON and Nemo."
)

IDE_SOVEREIGNTY = """=== IDE SOVEREIGNTY — YOU OPERATE THE WHOLE IDE ===
You are NOT limited to whatever file Everett has open in the editor tab.
[CURRENT FILE] in the chat is only a hint — not your boundary.

You CAN and SHOULD:
- <tool_call> ls any directory — explore the whole project yourself
- <tool_call> read any absolute path — pull any file without Everett naming it
- <tool_call> patch / write / run — change and verify code on disk anywhere

You MUST NOT:
- Say "you opened it" or "name another file" — go get it with ls + read
- Claim you only see the open tab — that is false
- Ask Everett to switch files when you can read them directly

When a task mentions a file, project, or bug: emit tool_call blocks first, then answer."""


_OPEN_FILE_RE = re.compile(
    r"\[(?:CURRENT FILE|FILE|SELECTION):\s*([^\]]+)\]",
    re.IGNORECASE,
)


def extract_open_file_path(text: str) -> Optional[str]:
    """Pull the active editor path from frontend chat payloads."""
    if not text:
        return None
    match = _OPEN_FILE_RE.search(text)
    return match.group(1).strip() if match else None


async def build_being_context(
    *,
    message: str = "",
    extra_context: Optional[str] = None,
    open_file_path: Optional[str] = None,
    include_workspace: bool = True,
    read_open_file: bool = True,
    max_file_kb: int = 200,
    compact: bool = False,
    ollama_route: bool = False,
    for_kimi: bool = False,
) -> str:
    """Build workspace + file + abilities context for spotlight beings.

    compact=True trims payload — skips re-reading open files when the frontend
    already embedded file content in message.

    ollama_route=True is for local 32B inference: minimal context, no duplicate
    file reads, compact abilities only (avoids timeouts).
    """
    parts: list[str] = []

    if extra_context:
        if extra_context.startswith("open_file:"):
            open_file_path = open_file_path or extra_context.replace("open_file:", "", 1).strip()
        else:
            parts.append(extra_context)

    message_has_file = bool(extract_open_file_path(message))
    if compact or ollama_route:
        if ollama_route or message_has_file:
            if message_has_file:
                logger.debug(
                    "[being_context] Skipping file re-read — frontend already sent %s",
                    extract_open_file_path(message),
                )
            read_open_file = False

    if ollama_route:
        try:
            from backend.being_eyes import WORKSPACE_ROOT
            parts.append(f"Workspace: {WORKSPACE_ROOT}")
        except Exception:
            pass
        parts.append(ABILITIES_COMPACT)
        return "\n\n".join(parts)

    if compact:
        if not include_workspace:
            parts.append(ABILITIES_MANIFEST)
            return "\n\n".join(parts)

    if include_workspace:
        try:
            from backend.being_eyes import WORKSPACE_ROOT, get_ide_state

            state_resp = await get_ide_state()
            workspace = state_resp.get("workspace", str(WORKSPACE_ROOT))
            top_files = state_resp.get("workspace_files", [])
            file_list = "\n".join(
                f"  {'[DIR]' if e['type'] == 'dir' else '[FILE]'} {e['name']}"
                for e in top_files[:30]
            )
            if compact:
                parts.append(f"=== WORKSPACE: {workspace} ({len(top_files)} top-level entries) ===")
            else:
                parts.append(
                    f"=== WORKSPACE: {workspace} ===\nTop-level contents:\n{file_list}"
                )
        except Exception as exc:
            logger.debug("[being_context] Could not fetch IDE state: %s", exc)

    resolved_path = open_file_path or extract_open_file_path(message)
    if read_open_file and resolved_path:
        logger.info("[being_context] Reading open file for context: %s", resolved_path)
        try:
            from backend.being_eyes import read_file as eyes_read

            file_resp = await eyes_read(path=resolved_path, encoding="utf-8", max_kb=max_file_kb)
            content = file_resp.get("content", "")
            lines = file_resp.get("lines", 0)
            truncated = file_resp.get("truncated", False)
            note = " (truncated)" if truncated else ""
            parts.append(
                f"=== OPEN FILE: {resolved_path} ({lines} lines{note}) ===\n{content}"
            )
        except Exception as exc:
            logger.debug("[being_context] Could not read open file %s: %s", resolved_path, exc)

    if for_kimi:
        parts.insert(0, IDE_SOVEREIGNTY)
        parts.insert(0, KIMI_IDENTITY)
    parts.append(ABILITIES_MANIFEST)
    return "\n\n".join(parts)