"""
voice_command_loop.py — Brockston-Studio voice entry (delegates to tcap-compute).

Canonical implementation: ~/tcap-compute/tcap_compute/voice_loop.py
Bridge :8765/latest → Brockston-Studio IDE :5055

Run:   python3 voice_command_loop.py
Stop:  SIGTERM / Ctrl+C
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _ensure_tcap_compute() -> None:
    root = Path(
        os.getenv("TCAP_COMPUTE_ROOT", str(Path.home() / "tcap-compute"))
    ).expanduser()
    if not (root / "tcap_compute").is_dir():
        raise SystemExit(
            f"tcap-compute not found at {root}. "
            "Clone ~/tcap-compute or set TCAP_COMPUTE_ROOT."
        )
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


_ensure_tcap_compute()

from tcap_compute.voice_loop import main  # noqa: E402

if __name__ == "__main__":
    main()