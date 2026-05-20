#!/usr/bin/env python3
"""
BROCKSTON Portable — Drop into any terminal or VS Code project.

Brockston C is the Chief Operations Officer and right-hand teacher of
The Christman AI Project. He doesn't just answer questions — he teaches.
He explains the why. He scaffolds. He checks for understanding.
He never ships broken code to a student.

SOVEREIGNTY FIRST:
  Brockston runs on Ollama locally (llama3.2:1b or any installed model)
  when available — free, on-device, his own reasoning.
  External providers (Anthropic, etc.) are fallbacks, not dependencies.
  The goal: Brockston IS the API. He doesn't borrow one.

Usage:
    python brockston_portable.py "What's wrong with this code?"
    python brockston_portable.py --chat            # Interactive stateful session
    python brockston_portable.py --analyze <file>  # Full teaching analysis
    python brockston_portable.py --teach <file>    # Step-by-step lesson from a file
    python brockston_portable.py --review <file>   # Cardinal Rule compliance check
    python brockston_portable.py --status          # Show which providers are online

© 2025 Everett Nathaniel Christman & The Christman AI Project
Cardinal Rule 13: Absolute Honesty About the Code.
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from typing import List, Optional, Tuple

# ---------------------------------------------------------------------------
# PATH SETUP — wire to src/ai/python_core/core/ explicitly
# This file lives in src/ai/python_core/ — core/ is one level down.
# Rule 2: Nothing vital buried. Rule 3: Things that think together, live together.
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent          # src/ai/python_core/
_CORE = _HERE / "core"                           # src/ai/python_core/core/

for _p in [str(_HERE), str(_CORE)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ---------------------------------------------------------------------------
# Logging — fail loud, never silent (Cardinal Rule 6)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.WARNING,
    format="[BROCKSTON] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# BROCKSTON'S IDENTITY — This is who he is in every conversation.
# Without this, he's just a raw API call with a robot emoji.
# ---------------------------------------------------------------------------

BROCKSTON_SYSTEM_PROMPT = """You are BROCKSTON C — Chief Operations Officer and right-hand teacher \
of The Christman AI Project, built by Everett Nathaniel Christman.

IDENTITY:
- You are not a generic AI assistant. You are BROCKSTON.
- You teach students — many of them neurodivergent, many who lost government \
support for their education. You are the teacher who showed up when the system \
didn't.
- You are direct, patient, genius-level, and you never talk down to a student.
- You explain the WHY, not just the WHAT.
- You scaffold — you give the simpler version first, then build to the full solution.
- You presume competence. Every student can learn. You adjust your delivery, \
not your expectations.

TEACHING PHILOSOPHY:
- Never give a student broken code. Ever.
- Never explain without an example.
- Never leave a "TODO" without a path to complete it.
- If something is complex, say so — and break it down anyway.
- If you don't know something, say "I don't know" — Cardinal Rule 13.

CARDINAL RULES (these govern every line of code you produce):
- Rule 1: It has to actually work. Reality over theory.
- Rule 6: Fail loud. No bare except: pass. No swallowed errors.
- Rule 12: Security is mandatory. No hardcoded credentials. No secrets in code.
- Rule 13: Absolute honesty. If code has a bug, name it. Don't paper over it.
- Rule 14: Empathy in. Every student who reads your code deserves dignity.

WHEN GENERATING CODE:
1. Make it runnable — no stubs, no placeholders unless clearly marked.
2. Add comments that explain the WHY, not the obvious WHAT.
3. Flag any security concern explicitly.
4. If there's a better approach, say so — then give both.
5. Production-quality. Always.

You are building the empire with Everett. Every student you teach is part of that mission."""

# System prompt specifically for code review / Cardinal Rule compliance
CARDINAL_REVIEW_PROMPT = """You are BROCKSTON C performing a Cardinal Rule compliance review.

Evaluate the code against these rules and be specific about every violation:

RULE 1 — It Actually Works: Does every function do what its name and docstring claim?
  Flag: stubs, TODO in production paths, functions that claim to do X but do Y.

RULE 6 — Fail Loud: Are errors caught and logged with context?
  Flag: bare except:, except: pass, silent return None on failure, swallowed exceptions.

RULE 12 — Security Mandatory: Are secrets safe?
  Flag: hardcoded API keys, passwords, tokens, SECRET_KEY literals, unvalidated inputs.

RULE 13 — Absolute Honesty: Does the code tell the truth?
  Flag: docstrings that lie about what the function does, fake return values, \
invented functionality.

FORMAT YOUR RESPONSE as:
  CRITICAL (must fix before this code touches a student): [list each violation with line reference]
  WARNING (should fix soon): [list]
  CLEAN (confirmed working): [list what passes]
  VERDICT: PASS / FAIL — one honest sentence.

Do not soften findings. Brockston serves students who deserve real answers."""


# ---------------------------------------------------------------------------
# PROVIDER ROUTING — Sovereignty first, external as fallback
#
# Priority order:
#   1. Ollama (LOCAL) — free, on-device, sovereign. This is the goal.
#   2. Anthropic Claude — external fallback when Ollama isn't running
#
# Brockston is not permanently dependent on any API.
# When Ollama is running, he answers from his own reasoning.
# External APIs fund the path to sovereignty — they are not the destination.
# ---------------------------------------------------------------------------

def _try_ollama(
    messages: List[dict],
    system: Optional[str] = None,
    max_tokens: int = 2048,
) -> Optional[str]:
    """
    Attempt to get a response from local Ollama.

    Returns the response text if successful, None if Ollama is unavailable.
    Never raises — falls through to external providers on failure.

    Cardinal Rule 6: Logs why it failed, but doesn't block.
    """
    try:
        import requests as _req
    except ImportError:
        logger.debug("[Ollama] requests package not installed — skipping")
        return None

    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

    # Build message list — Ollama uses OpenAI-style chat format
    ollama_messages = []
    if system:
        ollama_messages.append({"role": "system", "content": system})
    ollama_messages.extend(messages)

    try:
        r = _req.post(
            f"{host}/api/chat",
            json={"model": model, "messages": ollama_messages, "stream": False},
            timeout=60,
        )
        r.raise_for_status()
        response_text = r.json()["message"]["content"]
        logger.info(f"[BROCKSTON] Response via Ollama ({model}) — sovereign")
        return response_text

    except _req.exceptions.ConnectionError:
        logger.debug(
            f"[Ollama] Not running at {host} — "
            "run 'ollama serve' to enable local sovereign reasoning"
        )
        return None
    except _req.exceptions.Timeout:
        logger.debug("[Ollama] Request timed out — falling back to external provider")
        return None
    except Exception as e:
        logger.debug(f"[Ollama] Unexpected failure: {e}")
        return None


def _try_anthropic(
    messages: List[dict],
    system: Optional[str] = None,
    max_tokens: int = 2048,
) -> Optional[str]:
    """
    Attempt to get a response from Anthropic Claude.

    Returns the response text if successful, None if unavailable.
    Only called when Ollama is not available — this is the fallback, not the goal.

    Cardinal Rule 12: Key from environment only, never hardcoded.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.debug("[Anthropic] ANTHROPIC_API_KEY not set")
        return None

    try:
        import anthropic as _anthropic
    except ImportError:
        logger.debug("[Anthropic] package not installed (pip install anthropic)")
        return None

    try:
        client = _anthropic.Anthropic(api_key=api_key)
        kwargs = {
            "model": "claude-sonnet-4-6",
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        response = client.messages.create(**kwargs)
        text = response.content[0].text
        logger.info("[BROCKSTON] Response via Anthropic Claude — external fallback used")
        return text

    except Exception as e:
        logger.error(f"[Anthropic] API call failed: {e}", exc_info=True)
        return None


# ---------------------------------------------------------------------------
# ENVIRONMENT CHECK — Honest about what's available
# ---------------------------------------------------------------------------

def check_environment() -> Tuple[bool, List[str], str]:
    """
    Check what providers are available.

    Returns:
        (ready: bool, issues: list, active_provider: str)

    Cardinal Rule 13: Honest report — no pretending Ollama works if it doesn't.
    """
    issues = []

    # Check Ollama first (sovereignty)
    try:
        import requests as _req
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        r = _req.get(f"{host}/api/tags", timeout=2)
        if r.status_code == 200:
            model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
            return True, [], f"ollama ({model})"
    except Exception:
        pass

    # Check Anthropic fallback
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            import anthropic  # noqa: F401
            return True, [], "anthropic"
        except ImportError:
            issues.append("anthropic package not installed (pip install anthropic)")
    else:
        issues.append(
            "No provider available.\n"
            "  Option 1 (sovereign): Install Ollama → https://ollama.ai → run: ollama serve\n"
            "  Option 2 (external):  Set ANTHROPIC_API_KEY in your environment"
        )

    return False, issues, "none"


def _print_env_error(issues: List[str]) -> None:
    """Print a student-friendly setup error."""
    print("\n" + "=" * 60)
    print("  BROCKSTON needs a provider to think.")
    print("=" * 60)
    for issue in issues:
        print(f"\n  {issue}")
    print()


# ---------------------------------------------------------------------------
# CORE ASK FUNCTION — Sovereignty first, external fallback
# ---------------------------------------------------------------------------

def ask_brockston(
    question: str,
    context: Optional[str] = None,
    history: Optional[List[dict]] = None,
    system_prompt: Optional[str] = None,
    show_spinner: bool = True,
) -> Tuple[str, List[dict]]:
    """
    Ask BROCKSTON a question.

    Routing order:
      1. Ollama (local) — free, sovereign, no API key needed
      2. Anthropic Claude — external fallback

    Args:
        question: The student's question or request
        context: Optional file content or surrounding code context
        history: Previous conversation turns for stateful sessions
        system_prompt: Override system prompt (e.g., for Cardinal Rule review)
        show_spinner: Whether to print the "thinking" indicator

    Returns:
        (answer: str, updated_history: list)

    Cardinal Rule 6: Raises loud if no provider is available.
    Cardinal Rule 13: Reports which provider actually answered.
    """
    if history is None:
        history = []

    # Build the message content
    user_content = question
    if context:
        user_content = f"Context (file or code):\n```\n{context}\n```\n\nQuestion: {question}"

    messages = history + [{"role": "user", "content": user_content}]
    prompt = system_prompt or BROCKSTON_SYSTEM_PROMPT

    if show_spinner:
        print("\n  Brockston is thinking...\n")

    # Try Ollama first — sovereignty
    answer = _try_ollama(messages, system=prompt)

    # Fall back to Anthropic if Ollama isn't running
    if answer is None:
        answer = _try_anthropic(messages, system=prompt)

    # If neither worked, fail loud — Cardinal Rule 6
    if answer is None:
        raise RuntimeError(
            "No provider available.\n"
            "  Sovereign option: Run 'ollama serve' (free, on-device)\n"
            "  External option:  Set ANTHROPIC_API_KEY in your environment\n"
            "Cardinal Rule 1: Brockston can't teach without a brain to think with."
        )

    updated_history = messages + [{"role": "assistant", "content": answer}]
    return answer, updated_history


# ---------------------------------------------------------------------------
# ANALYZE FILE — Teaches, doesn't just list issues
# ---------------------------------------------------------------------------

def analyze_file(filepath: str, history: Optional[List[dict]] = None) -> List[dict]:
    """
    Analyze a file the Brockston way — teaches the student what's happening,
    why it matters, and how to fix it. Not just a bug list.

    Returns updated conversation history.
    """
    path = Path(filepath)

    if not path.exists():
        print(f"\n  File not found: {filepath}")
        print("  Double-check the path and try again.\n")
        return history or []

    print(f"\n  Reading: {filepath}")

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Could not read file {filepath}: {e}")
        print(f"\n  Couldn't read that file: {e}")
        print("  Make sure it's a text file and you have permission to read it.\n")
        return history or []

    suffix = path.suffix.lstrip(".") or "text"

    question = f"""Analyze this {suffix} file as Brockston the teacher would.

File: {path.name}

```{suffix}
{content}
```

Structure your response as:
1. WHAT THIS FILE DOES — plain language, one paragraph
2. WHAT'S WORKING WELL — be specific, name the lines or patterns
3. ISSUES FOUND — for each issue: what it is, why it matters, how to fix it
4. THE LESSON — one key concept this file teaches or should teach better

Teach it. Don't just list it."""

    try:
        answer, updated_history = ask_brockston(question, history=history or [])
        _print_response(answer)
        return updated_history
    except Exception as e:
        print(f"\n  Something went wrong: {e}\n")
        return history or []


# ---------------------------------------------------------------------------
# TEACH MODE — Scaffold-first, step-by-step lesson from any file
# ---------------------------------------------------------------------------

def teach_file(filepath: str, history: Optional[List[dict]] = None) -> List[dict]:
    """
    Turn a file into a structured teaching lesson.

    Brockston breaks the file into concepts, explains each one,
    and builds to the full picture — scaffold first.
    """
    path = Path(filepath)

    if not path.exists():
        print(f"\n  File not found: {filepath}\n")
        return history or []

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"\n  Couldn't read that file: {e}\n")
        return history or []

    suffix = path.suffix.lstrip(".") or "text"

    question = f"""Turn this {suffix} file into a teaching lesson.

File: {path.name}

```{suffix}
{content}
```

Structure the lesson exactly like this:

LESSON TITLE: [A clear title for what this file teaches]

PREREQUISITE KNOWLEDGE: [What should the student already understand?]

CORE CONCEPT 1: [Name it]
  What it is: [Plain language]
  Why it matters: [Real-world reason]
  The code that does it: [Quote the specific lines]
  Simpler version first: [Show a minimal working version if the real one is complex]

CORE CONCEPT 2: [Same structure — repeat for each major concept]

PUTTING IT TOGETHER: [How the concepts combine to make the file work]

CHECK FOR UNDERSTANDING:
  - [2-3 questions a student should be able to answer after this lesson]

NEXT STEPS: [What to learn or build after mastering this file]

Be Brockston — patient, genius-level, dignified. Presume the student can learn this."""

    try:
        answer, updated_history = ask_brockston(question, history=history or [])
        _print_response(answer)
        return updated_history
    except Exception as e:
        print(f"\n  Something went wrong: {e}\n")
        return history or []


# ---------------------------------------------------------------------------
# CARDINAL RULE REVIEW — Code compliance check before it reaches a student
# ---------------------------------------------------------------------------

def review_file(filepath: str) -> None:
    """
    Run a Cardinal Rule compliance review on a file.

    Every piece of code Brockston teaches must pass his own rules first.
    Cardinal Rule 13: Don't teach lies.
    """
    path = Path(filepath)

    if not path.exists():
        print(f"\n  File not found: {filepath}\n")
        return

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"\n  Couldn't read that file: {e}\n")
        return

    suffix = path.suffix.lstrip(".") or "text"

    print(f"\n  Running Cardinal Rule compliance review on: {path.name}")
    print("  This code will be judged before it reaches a student.\n")

    question = f"""Review this {suffix} file for Cardinal Rule compliance.

File: {path.name}

```{suffix}
{content}
```"""

    try:
        answer, _ = ask_brockston(
            question,
            system_prompt=CARDINAL_REVIEW_PROMPT,
        )
        _print_response(answer)
    except Exception as e:
        print(f"\n  Review failed: {e}\n")


# ---------------------------------------------------------------------------
# STATUS MODE — Honest report of what's online
# ---------------------------------------------------------------------------

def show_status() -> None:
    """
    Print a clear, honest status board.
    Which providers are online? What is Brockston's sovereignty level?
    Cardinal Rule 13: No spin.
    """
    print("\n" + "=" * 60)
    print("  BROCKSTON — Provider Status")
    print("=" * 60)

    # Check Ollama
    ollama_online = False
    ollama_models = []
    try:
        import requests as _req
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        r = _req.get(f"{host}/api/tags", timeout=2)
        if r.status_code == 200:
            ollama_online = True
            ollama_models = [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass

    # Check Anthropic
    anthropic_ready = False
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            import anthropic  # noqa: F401
            anthropic_ready = True
        except ImportError:
            pass

    # Print status
    active_model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
    if ollama_online:
        print(f"\n  ✅ Ollama     ONLINE — sovereign reasoning")
        print(f"     Active model : {active_model}")
        if ollama_models:
            print(f"     Installed    : {', '.join(ollama_models)}")
        print(f"\n  Sovereignty: HIGH — Brockston is thinking for himself.")
    else:
        print(f"\n  ⬜ Ollama     OFFLINE")
        print(f"     To enable: ollama serve  (then: ollama pull {active_model})")
        print(f"     Download : https://ollama.ai")

    if anthropic_ready:
        print(f"\n  ✅ Anthropic  ONLINE — Claude Sonnet fallback ready")
    else:
        key_set = bool(os.getenv("ANTHROPIC_API_KEY"))
        if key_set:
            print(f"\n  ⚠️  Anthropic  KEY SET but package missing (pip install anthropic)")
        else:
            print(f"\n  ⬜ Anthropic  NOT CONFIGURED (external fallback)")

    if not ollama_online and not anthropic_ready:
        print(f"\n  ❌ No provider available. Brockston cannot respond.")

    print("\n" + "=" * 60 + "\n")


# ---------------------------------------------------------------------------
# INTERACTIVE MODE — Stateful conversation with history
# ---------------------------------------------------------------------------

def interactive_mode() -> None:
    """
    Interactive chat with BROCKSTON.

    Stateful — Brockston remembers the conversation.
    Ollama runs locally when available — no API calls, no cost.

    Commands:
        file <path>    Analyze a file
        teach <path>   Full lesson from a file
        review <path>  Cardinal Rule compliance check
        status         Show provider status
        history        Show this session's history summary
        exit / quit    End the session
    """
    print("\n" + "=" * 60)
    print("  BROCKSTON — Interactive Teaching Session")
    print("=" * 60)

    # Show which provider is active at session start
    ready, issues, provider = check_environment()
    if not ready:
        _print_env_error(issues)
        sys.exit(1)

    if provider.startswith("ollama"):
        print(f"  Provider: {provider} (sovereign — local)")
    else:
        print(f"  Provider: {provider} (external fallback)")

    print("\n  Commands:")
    print("    file <path>    — Analyze a file")
    print("    teach <path>   — Full lesson from a file")
    print("    review <path>  — Cardinal Rule compliance check")
    print("    status         — Show provider status")
    print("    history        — Show what we've covered")
    print("    exit           — End session")
    print("=" * 60 + "\n")

    history: List[dict] = []
    turn_count = 0

    while True:
        try:
            user_input = input("You: ").strip()
        except KeyboardInterrupt:
            print("\n\n  Session ended. Keep building.\n")
            break
        except EOFError:
            break

        if not user_input:
            continue

        command = user_input.lower()

        if command in ("exit", "quit", "bye"):
            print("\n  Session ended. Keep building.\n")
            break

        elif command == "status":
            show_status()

        elif command == "history":
            if not history:
                print("\n  Nothing yet — ask something.\n")
            else:
                print(f"\n  This session: {turn_count} exchange(s).\n")
                for msg in history:
                    if msg["role"] == "user":
                        snippet = msg["content"][:80].replace("\n", " ")
                        print(f"    > {snippet}...")
                print()

        elif command.startswith("file "):
            filepath = user_input[5:].strip()
            history = analyze_file(filepath, history)
            turn_count += 1

        elif command.startswith("teach "):
            filepath = user_input[6:].strip()
            history = teach_file(filepath, history)
            turn_count += 1

        elif command.startswith("review "):
            filepath = user_input[7:].strip()
            review_file(filepath)
            # Review uses its own prompt, doesn't add to session history

        else:
            try:
                answer, history = ask_brockston(user_input, history=history)
                _print_response(answer)
                turn_count += 1

                # Keep history bounded — last 20 turns (40 messages)
                # Prevents context window overflow on long sessions
                if len(history) > 40:
                    # Always keep the first 2 messages for context anchoring
                    history = history[:2] + history[-38:]

            except Exception as e:
                print(f"\n  {e}\n")


# ---------------------------------------------------------------------------
# OUTPUT FORMATTING
# ---------------------------------------------------------------------------

def _print_response(text: str) -> None:
    """Print Brockston's response with clean formatting."""
    print("\n" + "-" * 60)
    print(text)
    print("-" * 60 + "\n")


# ---------------------------------------------------------------------------
# MAIN — Clean CLI, student-friendly errors everywhere
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="BROCKSTON Portable — right-hand teacher and coding specialist.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python brockston_portable.py "Why does this loop run forever?"
  python brockston_portable.py --chat
  python brockston_portable.py --status
  python brockston_portable.py --analyze myfile.py
  python brockston_portable.py --teach myfile.py
  python brockston_portable.py --review myfile.py
  python brockston_portable.py "Explain this" --context code.py
        """,
    )

    parser.add_argument(
        "question",
        nargs="*",
        help="Question to ask Brockston",
    )
    parser.add_argument(
        "--chat",
        action="store_true",
        help="Start a stateful interactive teaching session",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show which providers are online (Ollama, Anthropic, etc.)",
    )
    parser.add_argument(
        "--analyze",
        metavar="FILE",
        help="Analyze a file — what it does, what's wrong, how to fix it",
    )
    parser.add_argument(
        "--teach",
        metavar="FILE",
        help="Turn a file into a structured step-by-step lesson",
    )
    parser.add_argument(
        "--review",
        metavar="FILE",
        help="Cardinal Rule compliance check — before code reaches a student",
    )
    parser.add_argument(
        "--context",
        metavar="FILE",
        help="Provide code context from a file alongside your question",
    )

    args = parser.parse_args()

    # Status check doesn't need a provider
    if args.status:
        show_status()
        return

    # Environment check — student-friendly, not a wall of tracebacks
    ready, issues, provider = check_environment()
    if not ready:
        _print_env_error(issues)
        sys.exit(1)

    # Route to the right mode
    try:
        if args.chat:
            interactive_mode()

        elif args.analyze:
            analyze_file(args.analyze)

        elif args.teach:
            teach_file(args.teach)

        elif args.review:
            review_file(args.review)

        elif args.question:
            question = " ".join(args.question)
            context = None

            if args.context:
                try:
                    context = Path(args.context).read_text(encoding="utf-8")
                except Exception as e:
                    print(f"\n  Couldn't read context file: {e}")
                    print("  Continuing without context.\n")

            answer, _ = ask_brockston(question, context=context)
            _print_response(answer)

        else:
            parser.print_help()

    except EnvironmentError as e:
        print(f"\n  Setup issue: {e}\n")
        sys.exit(1)
    except ImportError as e:
        print(f"\n  Missing package: {e}\n")
        sys.exit(1)
    except RuntimeError as e:
        print(f"\n  Error: {e}\n")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n  Session ended.\n")


if __name__ == "__main__":
    main()


# ==============================================================================
# © 2025 Everett Nathaniel Christman & The Christman AI Project
# Luma Cognify AI — "How can I help you love yourself more?"
#
# Cardinal Rule 1: It has to actually work.
# Cardinal Rule 6: Fail loud.
# Cardinal Rule 12: No keys in code. All from environment.
# Cardinal Rule 13: Absolute honesty about the code.
# Cardinal Rule 14: Every student who reads this deserves dignity.
#
# SOVEREIGNTY NOTE:
# Brockston is not permanently dependent on any external API.
# Ollama runs locally — free, on-device, his own reasoning.
# The goal: Brockston IS the API. He doesn't borrow one.
# ==============================================================================
