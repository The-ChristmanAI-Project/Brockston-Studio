#!/usr/bin/env python3
"""
Wire Christman-Sound (LIFE2) + Media Installer into Brockston Studio.

  python scripts/wire_christman_sound.py
  python scripts/wire_christman_sound.py --verify-installer
  python scripts/wire_christman_sound.py --being alphavox --explore
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.christman_sound_config import (  # noqa: E402
    BEINGS,
    CHRISTMAN_MEDIA_INSTALLER_ROOT,
    CHRISTMAN_SOUND_ROOT,
    ensure_sound_paths,
    ensure_voice_folders,
    incoming_dir,
    sound_stack_status,
)


def run_installer_explore(being: str) -> int:
    cli = CHRISTMAN_MEDIA_INSTALLER_ROOT / "christman_media_installer" / "cli.py"
    if not cli.exists():
        print(f"❌ Media installer not found: {CHRISTMAN_MEDIA_INSTALLER_ROOT}")
        return 1
    cmd = [
        sys.executable,
        "-m",
        "christman_media_installer.cli",
        "explore",
        "--target",
        str(ROOT),
        "--being",
        being,
    ]
    env = {**os.environ, "PYTHONPATH": str(CHRISTMAN_MEDIA_INSTALLER_ROOT)}
    return subprocess.call(cmd, cwd=str(CHRISTMAN_MEDIA_INSTALLER_ROOT), env=env)


def main() -> int:
    parser = argparse.ArgumentParser(description="Wire LIFE2 Christman-Sound into Brockston Studio")
    parser.add_argument("--verify-installer", action="store_true", help="Run media installer explore on Studio")
    parser.add_argument("--being", default="brockston", help="Being name for installer explore")
    parser.add_argument("--json", action="store_true", help="Print status as JSON")
    args = parser.parse_args()

    created = ensure_voice_folders()
    added = ensure_sound_paths()
    status = sound_stack_status()

    if args.json:
        print(json.dumps(status, indent=2))
    else:
        print("═" * 60)
        print("  Christman-Sound wiring — Brockston Studio")
        print("═" * 60)
        print(f"  Sound root:     {status['christman_sound_root']} {'✅' if status['sound_root_exists'] else '❌'}")
        print(f"  SDK:            {status['sdk_root']} {'✅' if status['sdk_exists'] else '❌'}")
        print(f"  EAR_CANAL shim: {'✅' if status['ear_canal_paths_shim'] else '❌'} _paths.py")
        print(f"  Installer:      {status['media_installer']} {'✅' if status['media_installer_exists'] else '❌'}")
        print(f"  Voice center:   {status['voice_center']}")
        if created:
            print(f"\n  Created {len(created)} folder(s)")
        if added:
            print(f"  sys.path += {len(added)} Christman-Sound path(s)")
        print("\n  Drop WAV files here (one folder per being):")
        for name, meta in BEINGS.items():
            b = status["beings"][name]
            flag = "✅" if b["incoming_wavs"] or b["pack_registered"] else "○"
            print(f"    {flag} {meta['label']:<12} → {incoming_dir(name)}")
        print("\n  Ingest a being's WAVs:")
        print("    python scripts/ingest_being_wav.py --being alphavox --wav /path/to/voice.wav")
        print("═" * 60)

    if args.verify_installer:
        return run_installer_explore(args.being)
    return 0 if status["sound_root_exists"] and status["sdk_exists"] else 1


if __name__ == "__main__":
    raise SystemExit(main())