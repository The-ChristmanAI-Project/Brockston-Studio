#!/usr/bin/env python3
"""
Ingest reference WAV files for a Christman AI being.

Copies WAVs into Voice_Creation_Center/incoming/{being}/,
optionally builds a .voicepack, and registers the pack manifest.

  python scripts/ingest_being_wav.py --being kimi --wav ~/Downloads/kimi_ref.wav
  python scripts/ingest_being_wav.py --being alphavox --wav ref1.wav ref2.wav --build-pack
  python scripts/ingest_being_wav.py --list
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.christman_sound_config import (  # noqa: E402
    BEINGS,
    VOICEPACK_DIR,
    ensure_sound_paths,
    ensure_voice_folders,
    incoming_dir,
    packs_dir,
)


def register_manifest(being: str, voicepack_path: Path | None = None) -> Path:
    being_key = being.lower()
    profile = BEINGS[being_key]
    pack_dir = packs_dir(being_key)
    pack_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "pack_id": being_key,
        "being_name": profile["label"],
        "language": "en-US",
        "voicepack_path": str(voicepack_path) if voicepack_path else "",
        "version": datetime.now(timezone.utc).strftime("%Y.%m.%d.%H%M"),
        "rolled_out_at": datetime.now(timezone.utc).isoformat(),
        "source": "ingest_being_wav.py",
        "reference_wavs": sorted(str(p) for p in incoming_dir(being_key).glob("*.wav")),
    }
    manifest_path = pack_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    index_path = ROOT / "Voice_Creation_Center" / "inventory" / "index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    if index_path.exists():
        index = json.loads(index_path.read_text(encoding="utf-8"))
    else:
        index = {"packs": []}
    index["packs"] = [p for p in index.get("packs", []) if p.get("pack_id") != being_key]
    index["packs"].append(manifest)
    index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return manifest_path


def _to_wav(src: Path, dest_dir: Path) -> Path:
    """Copy or convert audio into dest_dir as .wav."""
    suffix = src.suffix.lower()
    if suffix == ".wav":
        target = dest_dir / src.name
        if src.resolve() == target.resolve():
            return target
        shutil.copy2(src, target)
        return target
    if suffix in (".mp3", ".m4a", ".aac", ".flac"):
        import subprocess

        target = dest_dir / f"{src.stem}.wav"
        r = subprocess.run(
            ["ffmpeg", "-y", "-i", str(src), "-ar", "22050", "-ac", "1", str(target)],
            capture_output=True,
            timeout=120,
        )
        if r.returncode != 0 or not target.exists():
            raise RuntimeError(f"ffmpeg convert failed: {r.stderr.decode()[:300]}")
        return target
    raise ValueError(f"Unsupported audio format: {src}")


def copy_wavs(being: str, sources: list[Path]) -> list[Path]:
    dest_dir = incoming_dir(being)
    dest_dir.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for src in sources:
        src = Path(src).expanduser().resolve()
        if not src.exists():
            raise FileNotFoundError(f"Audio not found: {src}")
        target = _to_wav(src, dest_dir)
        copied.append(target)
        print(f"  📥 {src.name} → {target}")
    return copied


def build_voicepack(being: str, wav_files: list[Path]) -> Path | None:
    ensure_sound_paths()
    try:
        from synthesis.voice_synthesis_orchestrator import VoiceSynthesisOrchestrator
        from timbre.voicepack import VoicepackMetadata
        from audio.config import Tier
    except ImportError as exc:
        print(f"  ⚠️  Voicepack build skipped — SDK import failed: {exc}")
        return None

    profile = BEINGS[being.lower()]
    tier_map = {"ultra": Tier.ULTRA, "premium": Tier.PREMIUM, "basic": Tier.BASIC}
    orch = VoiceSynthesisOrchestrator(tier=tier_map.get(profile["tier"], Tier.ULTRA))
    metadata = VoicepackMetadata(
        name=profile["label"],
        tier=profile["tier"],
        emotions=profile["emotions"],
        sample_count=len(wav_files),
    )
    print(f"  🔨 Building voicepack for {profile['label']}...")
    voicepack_path = orch.train_voice(
        audio_files=wav_files,
        voice_name=being.lower(),
        metadata=metadata,
        custom_emotions=profile["emotions"],
    )
    VOICEPACK_DIR.mkdir(parents=True, exist_ok=True)
    dest = VOICEPACK_DIR / f"{being.lower()}.voicepack"
    if Path(voicepack_path) != dest:
        shutil.copy2(voicepack_path, dest)
    pack_copy = packs_dir(being) / f"{being.lower()}.voicepack"
    shutil.copy2(dest, pack_copy)
    print(f"  ✅ Voicepack: {dest}")
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest WAV reference files for a being")
    parser.add_argument("--being", help="Being id (e.g. kimi, alphavox, brockston)")
    parser.add_argument("--wav", nargs="+", type=Path, help="One or more .wav files")
    parser.add_argument("--build-pack", action="store_true", help="Build .voicepack via Christman Voice SDK")
    parser.add_argument("--list", action="store_true", help="List beings and WAV status")
    args = parser.parse_args()

    ensure_voice_folders()

    if args.list:
        print("\nChristman beings — drop WAVs in incoming/{being}/\n")
        for key, meta in BEINGS.items():
            inc = incoming_dir(key)
            n = len(list(inc.glob("*.wav"))) if inc.is_dir() else 0
            print(f"  {meta['label']:<12} ({key})  {n} wav(s)  → {inc}")
        return 0

    if not args.being or not args.wav:
        parser.print_help()
        return 1

    being = args.being.lower()
    if being not in BEINGS:
        print(f"Unknown being: {being}. Known: {', '.join(BEINGS)}")
        return 1

    print(f"\nIngesting voice for {BEINGS[being]['label']} ({being})")
    copied = copy_wavs(being, args.wav)
    voicepack = build_voicepack(being, copied) if args.build_pack else None
    manifest = register_manifest(being, voicepack)
    print(f"  📋 Manifest: {manifest}")
    print("Done.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())