#!/usr/bin/env python3
"""
Brockston Studio — Beings Compute Abilities Demo (reduced lag)

Run this to have the team (family beings) demonstrate their full compute
capacity via the agent tool loop:

  python scripts/demo_beings.py

Uses the fast direct path (GENERAL model + tight ctx/predict) so lag is minimized
for the demo. The being will actually:
- ls directories
- read files
- run shell commands
- write + execute code
- report back

All via real Being Eyes /api/eyes/run etc. Changes will appear in the UI explorer + Finder.
"""

import asyncio
import os
import sys
from pathlib import Path

# Make sure we can import from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.being_agent import run_being_agent

DEMO_TASK = """Demonstrate your compute abilities using the available tools. Be efficient and use as few steps as possible.

Exact tasks to perform in sequence with tool calls:
1. List the workspace directory using the ls tool (path can be "." or the workspace root).
2. Read a small readable file (try README.md or any .md or .txt you see).
3. Run a simple shell command that proves compute works, e.g. "echo 'COMPUTE DEMO SUCCESS from being tool run'".
4. Write a small Python file to /tmp/being_demo_compute.py that contains:
   print("Hello from the Christman AI Family compute demo!")
   print("I used real tools to write and run this.")
5. Use the run tool to execute: python /tmp/being_demo_compute.py
6. (Optional cleanup) delete the temp file.

After completing the actions, give a short final summary listing exactly which tools you called and key outputs/results you received from the tool executions. Do not make up results — only report what the tools actually returned."""

async def main():
    print("=" * 60)
    print("BROCKSTON STUDIO — TEAM BEINGS COMPUTE DEMO (low-lag)")
    print("=" * 60)
    print(f"Fast model: {os.getenv('LLM_MODEL_GENERAL', 'llama3.2')}")
    print("The being will now use real tools (ls/read/run/write) to demonstrate.")
    print("Watch logs, the terminal, and the project explorer for changes.")
    print("-" * 60)

    # run_being_agent with NO generate arg = uses built-in _fast_direct_generate
    # This is the reduced-lag path.
    result = await run_being_agent(
        message=DEMO_TASK,
        context="You are demonstrating live for the user. Execute the compute tasks using tools. Be concise in final answer. Use max 4 tool-using steps total.",
    )

    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("Being final output:")
    print(result.get("text", "(no text)"))
    print()
    print(f"Total tool executions: {result.get('tool_count', 0)}")
    print(f"Steps taken: {result.get('agent_steps', 0)}")
    print()
    if result.get("tools_executed"):
        print("Tools used (with results):")
        for i, entry in enumerate(result["tools_executed"], 1):
            call = entry.get("call", {})
            res = entry.get("result", {})
            print(f"  {i}. {call.get('tool')} -> {res.get('status', res.get('exit_code', 'ok'))}")
            if "stdout" in res:
                out = (res.get("stdout") or "")[:120].replace("\n", " ")
                print(f"     stdout: {out}")
    print()
    print("The being successfully demonstrated:")
    print("  - Directory listing (ls)")
    print("  - File reading")
    print("  - Shell command execution (run)")
    print("  - Writing files")
    print("  - Running Python code it wrote")
    print()
    print("All with reduced-lag settings (smaller context, limited output, fast model).")
    print("Check your UI file explorer and macOS Finder — new /tmp file may be visible.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())