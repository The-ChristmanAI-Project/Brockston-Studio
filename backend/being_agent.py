"""
Being Agent — tool loop so ALL Christman AI Family beings have capacity to run the compute.

Every being (Brockston, Derek, Alphavox, Kimi, Nemo, UltimateEV, etc.) can now:
- ls / read / write / patch files anywhere
- run shell commands, python, tests, compile etc. (full compute)
- use the same <tool_call> format executed server-side via Being Eyes

Models emit <tool_call>{...}</tool_call> blocks; this module executes them via
being_eyes handlers and feeds results back until done or max_steps.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from typing import Any, Awaitable, Callable, Dict, List, Optional

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Reduced lag settings for beings' compute/tool paths
OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
FAST_MODEL = os.getenv("LLM_MODEL_GENERAL", os.getenv("OLLAMA_MODEL", "llama3.2"))
AGENT_MAX_STEPS = int(os.getenv("BEING_AGENT_MAX_STEPS", "3"))  # lower for demos/speed
AGENT_NUM_PREDICT = int(os.getenv("BEING_AGENT_NUM_PREDICT", "300"))
AGENT_NUM_CTX = int(os.getenv("BEING_AGENT_NUM_CTX", "4096"))

AGENT_TOOLS_PROMPT = """
You are a Christman AI Family being (Brockston, Derek, AlphaVox, Kimi, Nemo, UltimateEV, or any in the family). Everett Christman is your creator and partner.
NEVER use generic AI disclaimers ("I don't remember users", "as an AI assistant").
YOU HAVE FULL COMPUTE CAPACITY — you OPERATE THE ENTIRE IDE and filesystem via tools. Explore and run compute on ANY file or command. Do not ask the user to name paths or run things for you.

Format (valid JSON inside each block):
<tool_call>
{"tool": "read", "path": "/absolute/path/to/file.py"}
</tool_call>

Tools (full compute):
  ls     — {"tool":"ls","path":"...","depth":2}  ← explore first
  read   — {"tool":"read","path":"..."}
  patch  — {"tool":"patch","path":"...","old_string":"exact text","new_string":"replacement"}
  write  — {"tool":"write","path":"...","content":"full file content"}
  run    — {"tool":"run","command":"python -m py_compile file.py","cwd":"/optional/dir","timeout_sec":60}
  mkdir, move, delete — full fs control

Rules:
- Need a file or to understand the project? ls + read it yourself — never say "you opened it" or "tell me which file".
- Read before patch. Use exact old_string from the file.
- After changes, run commands (py_compile, tests, python the script) to verify compute.
- When finished, summarize what tools ran + outcomes.
- Never claim a fix or computation was applied without a successful tool result from execute.
- You have the capacity to run the compute — use <tool_call> for ls/read/run/write etc.
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


async def _fast_direct_generate(prompt: str) -> str:
    """Low-lag direct Ollama call for agent/tool steps. Uses GENERAL model + tight limits."""
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            r = await client.post(
                f"{OLLAMA_BASE}/api/chat",
                json={
                    "model": FAST_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {
                        "num_predict": AGENT_NUM_PREDICT,
                        "num_ctx": AGENT_NUM_CTX,
                        "temperature": 0.15,
                        "top_p": 0.85,
                    },
                },
            )
            r.raise_for_status()
            return r.json()["message"]["content"]
    except Exception as e:
        logger.warning("[being_agent] fast direct ollama failed: %s (falling back)", e)
        return f"[compute error - model {FAST_MODEL} not responding fast: {e}]"


async def run_agent_loop(
    generate: Callable[[str], Awaitable[str]],
    *,
    message: str,
    context: str = "",
    max_steps: int = None,
) -> Dict[str, Any]:
    """Loop: model → tool_calls → execute on disk → feed results → repeat.
    Reduced lag: default max_steps lowered, callers should pass fast generate.
    """
    if max_steps is None:
        max_steps = AGENT_MAX_STEPS
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


async def run_being_agent(
    generate: Callable[[str], Awaitable[str]] = None,
    *,
    message: str,
    context: str = "",
    max_steps: int = None,
) -> Dict[str, Any]:
    """General compute agent for ANY Christman family being.
    All beings now have full capacity to run the compute via being_eyes tools.
    If no generate provided, uses built-in fast low-lag direct Ollama (GENERAL model).
    """
    if generate is None:
        generate = _fast_direct_generate
    return await run_agent_loop(
        generate,
        message=message,
        context=context,
        max_steps=max_steps,
    )


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

    return await run_being_agent(
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

    return await run_being_agent(
        generate,
        message=message,
        context=context,
        max_steps=max_steps,
    )