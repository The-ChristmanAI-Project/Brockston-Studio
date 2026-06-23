"""
Being Agent — tool loop so Kimi/Nemo actually read, patch, write, and run.

Models emit <tool_call>{...}</tool_call> blocks; this module executes them via
being_eyes handlers and feeds results back until done or max_steps.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import HTTPException

logger = logging.getLogger(__name__)

AGENT_TOOLS_PROMPT = """
You are Kimi — Christman AI Family being. Everett Christman is your creator and partner.
NEVER use generic AI disclaimers ("I don't remember users", "as an AI assistant").
YOU OPERATE THE ENTIRE IDE — not just Everett's open editor tab.
Use tool_call blocks to explore and change ANY file. Do not ask Everett to name paths.

Format (valid JSON inside each block):
<tool_call>
{"tool": "read", "path": "/absolute/path/to/file.py"}
</tool_call>

Tools:
  ls     — {"tool":"ls","path":"/Users/EverettN/...","depth":2}  ← explore first
  read   — {"tool":"read","path":"..."}
  patch  — {"tool":"patch","path":"...","old_string":"exact text","new_string":"replacement"}
  write  — {"tool":"write","path":"...","content":"full file content"}
  run    — {"tool":"run","command":"python -m py_compile file.py","cwd":"/optional/dir"}

Rules:
- Need a file? ls + read it yourself — never say "you opened it" or "tell me which file".
- Read before patch. Use exact old_string from the file.
- After patching code, run py_compile (or tests) to verify.
- When finished, summarize what tools ran and their outcomes.
- Never claim a fix was applied without a successful tool result.
"""

_TOOL_CALL_RE = re.compile(
    r"<tool_call>\s*(\{.*?\})\s*</tool_call>",
    re.DOTALL | re.IGNORECASE,
)

_CODE_FIX_RE = re.compile(
    r"\b(fix|patch|repair|debug|implement|refactor|broken|syntax\s*error|bug)\b|"
    r"(py_compile|\.py\b|\.ts\b|\.tsx\b|\.js\b|di_container|compile\s+error|investigate\s+the)",
    re.IGNORECASE,
)


def wants_agent_tools(message: str, mode: str) -> bool:
    """Enable the tool loop for code work — not creative tutor chat."""
    if mode in ("codelab", "code"):
        return True
    return bool(_CODE_FIX_RE.search(message or ""))


def parse_tool_calls(text: str) -> List[Dict[str, Any]]:
    calls: List[Dict[str, Any]] = []
    for match in _TOOL_CALL_RE.finditer(text or ""):
        raw = match.group(1).strip()
        try:
            payload = json.loads(raw)
            if isinstance(payload, dict) and payload.get("tool"):
                calls.append(payload)
        except json.JSONDecodeError as exc:
            logger.warning("[being_agent] Bad tool_call JSON: %s", exc)
    return calls


async def execute_being_tool(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Run one Being Eyes action. Returns result or explicit error — Rule 6."""
    from backend.being_eyes import (
        DeleteRequest,
        MoveRequest,
        PatchRequest,
        RunRequest,
        WriteRequest,
        delete_path,
        list_directory,
        make_directory,
        move_file,
        patch_file,
        read_file,
        run_command,
        write_file,
    )

    tool = str(payload.get("tool", "")).lower().strip()
    logger.info("[being_agent] Executing tool=%s path=%s", tool, payload.get("path", ""))

    try:
        if tool == "read":
            return await read_file(
                path=payload["path"],
                encoding=payload.get("encoding", "utf-8"),
                max_kb=int(payload.get("max_kb", 500)),
            )
        if tool == "patch":
            return await patch_file(
                PatchRequest(
                    path=payload["path"],
                    old_string=payload["old_string"],
                    new_string=payload["new_string"],
                    replace_all=bool(payload.get("replace_all", False)),
                )
            )
        if tool == "write":
            return await write_file(
                WriteRequest(
                    path=payload["path"],
                    content=payload["content"],
                    encoding=payload.get("encoding", "utf-8"),
                    create_dirs=bool(payload.get("create_dirs", True)),
                )
            )
        if tool == "run":
            return await run_command(
                RunRequest(
                    command=payload["command"],
                    cwd=payload.get("cwd"),
                    timeout_sec=int(payload.get("timeout_sec", 60)),
                )
            )
        if tool == "ls":
            return await list_directory(
                path=payload.get("path", "."),
                depth=int(payload.get("depth", 1)),
            )
        if tool == "mkdir":
            return await make_directory(path=payload["path"])
        if tool == "move":
            return await move_file(
                MoveRequest(
                    src=payload["src"],
                    dst=payload["dst"],
                    overwrite=bool(payload.get("overwrite", False)),
                )
            )
        if tool == "delete":
            return await delete_path(
                DeleteRequest(
                    path=payload["path"],
                    recursive=bool(payload.get("recursive", False)),
                )
            )
        return {"status": "error", "detail": f"Unknown tool: {tool}"}
    except HTTPException as exc:
        return {"status": "error", "detail": exc.detail, "status_code": exc.status_code}
    except KeyError as exc:
        return {"status": "error", "detail": f"Missing field: {exc}"}
    except Exception as exc:
        logger.error("[being_agent] Tool %s failed: %s", tool, exc, exc_info=True)
        return {"status": "error", "detail": str(exc)}


async def run_agent_loop(
    generate: Callable[[str], Awaitable[str]],
    *,
    message: str,
    context: str = "",
    max_steps: int = 6,
) -> Dict[str, Any]:
    """Loop: model → tool_calls → execute on disk → feed results → repeat."""
    tools_executed: List[Dict[str, Any]] = []
    conversation = message
    if context:
        conversation = f"Context:\n{context}\n\nUser request:\n{message}"

    last_text = ""
    steps_used = 0
    for step in range(max_steps):
        steps_used = step + 1
        prompt = f"{AGENT_TOOLS_PROMPT}\n\n{conversation}" if step == 0 else conversation

        last_text = await generate(prompt)
        calls = parse_tool_calls(last_text)
        if not calls:
            break

        batch_results: List[Dict[str, Any]] = []
        for call in calls:
            result = await execute_being_tool(call)
            entry = {"call": call, "result": result}
            tools_executed.append(entry)
            batch_results.append(entry)
            logger.info(
                "[being_agent] step=%d tool=%s status=%s",
                step + 1,
                call.get("tool"),
                result.get("status", result.get("exit_code")),
            )

        conversation = (
            f"{conversation}\n\n"
            f"Assistant (step {step + 1}):\n{last_text}\n\n"
            f"TOOL RESULTS (real execution on disk):\n"
            f"{json.dumps(batch_results, indent=2, default=str)}\n\n"
            "Continue with more <tool_call> blocks if needed, "
            "or give a final summary of what was fixed and verified."
        )

    return {
        "ok": True,
        "text": last_text,
        "tools_executed": tools_executed,
        "tool_count": len(tools_executed),
        "agent_steps": steps_used,
    }


async def run_kimi_agent(
    kimi_svc: Any,
    *,
    message: str,
    context: str,
    mode: str = "codelab",
    domain: Optional[str] = None,
    max_steps: int = 6,
) -> Dict[str, Any]:
    loop = asyncio.get_event_loop()

    async def generate(prompt: str) -> str:
        def _call() -> str:
            result = kimi_svc.interact(
                message=prompt,
                mode=mode,
                context=None,
                domain=domain,
                thinking=False,
                max_tokens=4096,
            )
            return result.get("text", "")

        return await loop.run_in_executor(None, _call)

    return await run_agent_loop(
        generate,
        message=message,
        context=context,
        max_steps=max_steps,
    )


async def run_nemo_agent(
    nemo_svc: Any,
    *,
    message: str,
    context: str,
    mode: str = "code",
    max_steps: int = 6,
) -> Dict[str, Any]:
    loop = asyncio.get_event_loop()

    async def generate(prompt: str) -> str:
        return await loop.run_in_executor(
            None,
            lambda: nemo_svc.generate_content(prompt, mode=mode, context=None),
        )

    return await run_agent_loop(
        generate,
        message=message,
        context=context,
        max_steps=max_steps,
    )