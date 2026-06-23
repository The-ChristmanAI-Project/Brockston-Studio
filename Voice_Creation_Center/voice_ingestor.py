"""
Voice Creation Center — front door for incoming WAV/MP3 files.

Drop files into incoming/{being}/ then run:
  python Voice_Creation_Center/voice_ingestor.py --being kimi --watch
  python scripts/ingest_being_wav.py --being kimi --wav path/to/file.wav
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.christman_sound_config import BEINGS, incoming_dir, ensure_voice_folders  # noqa: E402


def ingest_file(being: str, path: Path, build_pack: bool) -> int:
    script = ROOT / "scripts" / "ingest_being_wav.py"
    cmd = [sys.executable, str(script), "--being", being, "--wav", str(path)]
    if build_pack:
        cmd.append("--build-pack")
    return subprocess.call(cmd)


def scan_incoming(being: str, build_pack: bool) -> int:
    folder = incoming_dir(being)
    if not folder.is_dir():
        print(f"No incoming folder: {folder}")
        return 1
    pending = [
        p for p in folder.glob("*")
        if p.suffix.lower() in (".wav", ".mp3", ".m4a")
        and not p.name.startswith(".")
    ]
    if not pending:
        print(f"No audio waiting in {folder}")
        return 0
    rc = 0
    for path in pending:
        if path.suffix.lower() != ".wav":
            print(f"  Skip non-wav (convert first): {path.name}")
            continue
        rc = ingest_file(being, path, build_pack) or rc
    return rc


def watch(being: str, build_pack: bool) -> None:
    folder = incoming_dir(being)
    folder.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    print(f"Watching {folder} — drop .wav files for {being}")
    while True:
        for path in folder.glob("*.wav"):
            key = f"{path.name}:{path.stat().st_mtime_ns}"
            if key in seen:
                continue
            seen.add(key)
            print(f"\nNew file: {path.name}")
            ingest_file(being, path, build_pack)
        time.sleep(2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Christman Voice Creation Center ingestor")
    parser.add_argument("--being", required=True, help="Being id (kimi, alphavox, ...)")
    parser.add_argument("--watch", action="store_true", help="Watch incoming folder")
    parser.add_argument("--build-pack", action="store_true", help="Build voicepack after ingest")
    parser.add_argument("--scan", action="store_true", help="Ingest all WAVs currently in folder")
    args = parser.parse_args()

    ensure_voice_folders()
    being = args.being.lower()
    if being not in BEINGS:
        print(f"Unknown being: {being}. Known: {', '.join(BEINGS)}")
        return 1

    if args.watch:
        watch(being, args.build_pack)
        return 0
    if args.scan:
        return scan_incoming(being, args.build_pack)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())