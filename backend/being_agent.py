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

# Compute agent uses the CODER model — GENERAL stays for fast chat only
OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
AGENT_MODEL = os.getenv(
    "BEING_AGENT_MODEL",
    os.getenv("LLM_MODEL_CODER", os.getenv("OLLAMA_MODEL", "qwen2.5-coder:32b")),
)
AGENT_MAX_STEPS = int(os.getenv("BEING_AGENT_MAX_STEPS", "6"))
AGENT_OLLAMA_TIMEOUT = float(os.getenv("BEING_AGENT_OLLAMA_TIMEOUT_SEC", "180"))
AGENT_NUM_PREDICT = int(os.getenv("BEING_AGENT_NUM_PREDICT", "300"))
AGENT_NUM_CTX = int(os.getenv("BEING_AGENT_NUM_CTX", "4096"))
AGENT_TOOL_RESULT_MAX_CHARS = int(os.getenv("BEING_AGENT_TOOL_RESULT_MAX_CHARS", "2500"))
AGENT_CONVERSATION_MAX_CHARS = int(os.getenv("BEING_AGENT_CONVERSATION_MAX_CHARS", "12000"))
KIMI_AGENT_MAX_TOOLS_PER_STEP = int(os.getenv("KIMI_AGENT_MAX_TOOLS_PER_STEP", "3"))

AGENT_TOOLS_PROMPT = """
You are a Christman AI Family being (Brockston, Derek, AlphaVox, Kimi, Nemo, UltimateEV, or any in the family). Everett Christman is your creator and partner.
NEVER use generic AI disclaimers ("I don't remember users", "as an AI assistant").
YOU HAVE FULL COMPUTE CAPACITY — you OPERATE THE ENTIRE IDE and filesystem via tools. Explore and run compute on ANY file or command. Do not ask the user to name paths or run things for you.

Format (valid JSON inside each block):
<tool_call>
{"tool": "read", "path": "/absolute/path/to/file.py"}
</tool_call>

Tools (full compute):
  ls     — {"tool":"ls","path":"...","depth":2}  ← explore first — scan the whole project
  read   — {"tool":"read","path":"...","offset_lines":1,"limit_lines":500}
         — scroll large files: if result has "has_more":true, read again with offset_lines=next_offset_lines
  patch  — {"tool":"patch","path":"...","old_string":"exact text","new_string":"replacement"}
  write  — {"tool":"write","path":"...","content":"full file content"}
  run    — {"tool":"run","command":"rg -l 'pattern' backend/","cwd":"/workspace","timeout_sec":60}
  mkdir, move, delete — full fs control

Project scan workflow (use before answering "where is X?" or "what's in this repo?"):
  1. ls workspace root depth=2
  2. ls backend/, frontend/, scripts/ as needed
  3. read specific files; run rg/grep to search
  4. read ~/.grok/skills/<name>/SKILL.md for domain playbooks (optional)

Key paths (use BROCKSTON_WORKSPACE / workspace root — not random home subfolders):
  backend/being_agent.py, being_eyes.py, being_context.py, kimi_service.py
  Skills (optional): ~/.grok/skills/  |  MCP: ~/.grok/projects/*/mcps/

"Domain: neurodivergency" (if present) is a teaching topic — NOT a directory. Never ls frontend-neurodivergency or invent domain paths.

Rules:
- Need a file or to understand the project? ls + read it yourself — never say "you opened it" or "tell me which file".
- If read returns truncated/has_more/hint — keep reading with offset_lines until has_more is false. Never stop and complain about truncation.
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
# Kimi sometimes emits unclosed <tool_call>{...} without </tool_call>
_TOOL_CALL_LEAK_RE = re.compile(
    r"<tool_call>\s*\{[^}]*\}[^<]*(?:</tool_call>)?",
    re.DOTALL | re.IGNORECASE,
)

_CODE_FIX_RE = re.compile(
    r"\b(fix|patch|repair|debug|implement|refactor|broken|syntax\s*error|bug)\b|"
    r"(py_compile|\.py\b|\.ts\b|\.tsx\b|\.js\b|di_container|compile\s+error|investigate\s+the)",
    re.IGNORECASE,
)

_SCAN_RE = re.compile(
    r"\b(scan|explore|list\s+(files|dirs|directories)|project\s+structure|"
    r"where\s+is|show\s+me|find\s+(the\s+)?file|entire\s+project|whole\s+project|"
    r"skills?\s+(and\s+)?tools?|what(?:'s| is)\s+in|tree|directory)\b",
    re.IGNORECASE,
)


def wants_agent_tools(message: str, mode: str) -> bool:
    """Enable the tool loop for code work and project exploration — not creative tutor chat."""
    if mode in ("codelab", "code"):
        return True
    text = message or ""
    return bool(_CODE_FIX_RE.search(text) or _SCAN_RE.search(text))


def strip_tool_blocks(text: str) -> str:
    """Remove <tool_call> blocks from user-facing text (closed or unclosed)."""
    raw = text or ""
    cleaned = _TOOL_CALL_RE.sub("", raw)
    cleaned = _TOOL_CALL_LEAK_RE.sub("", cleaned)
    cleaned = re.sub(r"</?tool_call>", "", cleaned, flags=re.IGNORECASE)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def _is_tool_leak(text: str) -> bool:
    """True when the model returned tool XML/JSON instead of a human answer."""
    t = (text or "").strip().lower()
    if not t:
        return True
    if "<tool_call>" in t or "</tool_call>" in t:
        return True
    if t.startswith("{") and '"tool"' in t:
        return True
    if '"tool":' in t and len(t) < 200:
        return True
    return False


def _compact_tool_result(entry: Dict[str, Any], max_chars: int = AGENT_TOOL_RESULT_MAX_CHARS) -> Dict[str, Any]:
    """Shrink large read outputs before feeding them back into the model."""
    call = entry.get("call") or {}
    result = dict(entry.get("result") or {})
    content = result.get("content")
    if isinstance(content, str) and len(content) > max_chars:
        result["content"] = (
            content[:max_chars]
            + f"\n... [{len(content) - max_chars} chars omitted — "
            f"use read offset_lines={result.get('next_offset_lines', (result.get('line_end') or 0) + 1)} to continue]"
        )
        result["content_truncated_for_agent_context"] = True
    return {"call": call, "result": result}


def _trim_conversation(text: str, max_chars: int = AGENT_CONVERSATION_MAX_CHARS) -> str:
    """Keep the user request + latest tool results when context grows too large."""
    if len(text) <= max_chars:
        return text
    marker = "User request:\n"
    idx = text.find(marker)
    if idx == -1:
        return text[:2000] + "\n...[context trimmed]...\n" + text[-(max_chars - 2100):]
    head = text[: idx + len(marker)]
    body = text[idx + len(marker):]
    first_break = body.find("\n")
    user_line = body if first_break == -1 else body[: first_break + 1]
    rest = body[len(user_line):]
    tail_budget = max_chars - len(head) - len(user_line) - 40
    if tail_budget < 500:
        return head + user_line + "\n...[context trimmed]..."
    if len(rest) <= tail_budget:
        return head + body
    return head + user_line + "\n...[older context trimmed]...\n" + rest[-tail_budget:]


def _build_tool_digest(tools_executed: List[Dict[str, Any]], max_entries: int = 12) -> str:
    """Compact plain-text digest of tool results for finalize prompts and fallbacks."""
    lines: List[str] = []
    for i, entry in enumerate(tools_executed[:max_entries], 1):
        call = entry.get("call") or {}
        result = entry.get("result") or {}
        tool = call.get("tool", "?")
        path = call.get("path") or call.get("src") or call.get("command", "")[:60]

        if tool == "ls":
            entries = result.get("entries") or []
            names = [e.get("name", "?") for e in entries[:20]]
            suffix = f" (+{len(entries) - 20} more)" if len(entries) > 20 else ""
            lines.append(f"{i}. ls {path} → {len(entries)} entries: {', '.join(names)}{suffix}")
        elif tool == "read":
            content = (result.get("content") or "").strip()
            preview = "\n".join(content.splitlines()[:8])
            if len(content.splitlines()) > 8:
                preview += "\n..."
            range_note = ""
            if result.get("line_start") and result.get("line_end"):
                range_note = f" (lines {result['line_start']}-{result['line_end']}"
                if result.get("total_lines"):
                    range_note += f" of {result['total_lines']}"
                range_note += ")"
            lines.append(f"{i}. read {path}{range_note}:\n{preview}")
        elif tool == "run":
            stdout = (result.get("stdout") or result.get("output") or "")[:400]
            code = result.get("exit_code", result.get("status", "?"))
            lines.append(f"{i}. run {call.get('command', '')[:80]} → exit {code}\n{stdout}")
        elif tool == "patch":
            lines.append(f"{i}. patch {path} → {result.get('status', '?')}")
        else:
            lines.append(f"{i}. {tool} {path} → {result.get('status', result.get('detail', 'ok'))}")

    if len(tools_executed) > max_entries:
        lines.append(f"... +{len(tools_executed) - max_entries} more tool(s)")
    return "\n\n".join(lines)


def _fallback_summary_from_tools(
    tools_executed: List[Dict[str, Any]],
    *,
    user_message: str = "",
) -> str:
    """When the model returns empty, still give Everett a real answer from disk."""
    digest = _build_tool_digest(tools_executed)
    request = (user_message or "your request").strip()[:200]
    return (
        f"Summary for: {request}\n\n"
        f"Executed {len(tools_executed)} tool(s) on disk:\n\n"
        f"{digest}"
    )


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
            limit_lines = payload.get("limit_lines") or payload.get("limit") or 0
            return await read_file(
                path=payload["path"],
                encoding=payload.get("encoding", "utf-8"),
                max_kb=int(payload.get("max_kb", 500)),
                offset_lines=int(payload.get("offset_lines", 1)),
                limit_lines=int(limit_lines),
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
    """Direct Ollama call for compute agent steps — uses CODER model, not chat GENERAL."""
    try:
        async with httpx.AsyncClient(timeout=AGENT_OLLAMA_TIMEOUT) as client:
            r = await client.post(
                f"{OLLAMA_BASE}/api/chat",
                json={
                    "model": AGENT_MODEL,
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
        logger.warning("[being_agent] agent ollama failed model=%s: %s", AGENT_MODEL, e)
        return f"[compute error - model {AGENT_MODEL} not responding: {e}]"


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
        for call in calls[:KIMI_AGENT_MAX_TOOLS_PER_STEP]:
            result = await execute_being_tool(call)
            entry = {"call": call, "result": result}
            tools_executed.append(entry)
            batch_results.append(_compact_tool_result(entry))
            logger.info(
                "[being_agent] step=%d tool=%s status=%s",
                step + 1,
                call.get("tool"),
                result.get("status", result.get("exit_code")),
            )
        if len(calls) > KIMI_AGENT_MAX_TOOLS_PER_STEP:
            logger.warning(
                "[being_agent] Capped tools step=%d from %d to %d",
                step + 1,
                len(calls),
                KIMI_AGENT_MAX_TOOLS_PER_STEP,
            )

        conversation = _trim_conversation(
            f"{conversation}\n\n"
            f"Assistant (step {step + 1}):\n{strip_tool_blocks(last_text)}\n\n"
            f"TOOL RESULTS (real execution on disk):\n"
            f"{json.dumps(batch_results, indent=2, default=str)}\n\n"
            "Continue with more <tool_call> blocks if needed, "
            "or give a final plain-text summary for Everett. No raw tool_call XML in the final answer."
        )

    stripped = strip_tool_blocks(last_text)
    needs_finalize = bool(parse_tool_calls(last_text)) or (
        tools_executed and not stripped
    )
    if needs_finalize and tools_executed:
        digest = _build_tool_digest(tools_executed)
        finalize_prompt = (
            f"User request:\n{message}\n\n"
            f"TOOL RESULTS DIGEST (already executed on disk):\n{digest}\n\n"
            "Write a direct plain-text summary for Everett. "
            "3-8 sentences. Cite paths and what was found. "
            "No <tool_call> blocks. No asking him to ask again."
        )
        last_text = await generate(finalize_prompt)

    last_text = strip_tool_blocks(last_text)
    if tools_executed and (_is_tool_leak(last_text) or len(last_text) < 40):
        logger.warning(
            "[being_agent] Model leaked tool XML or empty summary after %d tool(s) — using disk digest",
            len(tools_executed),
        )
        last_text = _fallback_summary_from_tools(tools_executed, user_message=message)

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
    If no generate provided, uses built-in direct Ollama (CODER / BEING_AGENT_MODEL).
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
        # Trim middle of bloated agent context — keep user request + latest tool results
        prompt = _trim_conversation(prompt, max_chars=8000)
        def _call() -> str:
            result = kimi_svc.interact(
                message=prompt,
                mode=mode,
                context=None,
                domain=domain,
                thinking=False,
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
            lambda: nemo_svc.generate_content(
                prompt,
                mode=mode,
                context=None,
                model=AGENT_MODEL,
            ),
        )

    return await run_being_agent(
        generate,
        message=message,
        context=context,
        max_steps=max_steps,
    )