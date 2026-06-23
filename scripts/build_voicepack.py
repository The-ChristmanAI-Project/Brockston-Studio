#!/usr/bin/env python3
"""
build_voicepack.py — Build a .voicepack from WAV reference files.

Usage:
    python scripts/build_voicepack.py --being brockston --wav ref1.wav ref2.wav
    python scripts/build_voicepack.py --being giuseppe --wav data/raw/giuseppe_ref.wav
    python scripts/build_voicepack.py --list-beings

The voicepack is saved to:
    data/voicepacks/{being}.voicepack

Once built, christman_sound.speak(text, being='{being}') automatically
routes through VoiceSynthesisOrchestrator instead of falling back to XTTS.
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.christman_sound_config import (  # noqa: E402
    BEINGS,
    VOICEPACK_DIR,
    ensure_sound_paths,
)

ensure_sound_paths()


def build(being: str, wav_files: list[Path]) -> Path:
    from synthesis.voice_synthesis_orchestrator import VoiceSynthesisOrchestrator
    from timbre.voicepack import VoicepackMetadata
    from audio.config import Tier

    profile = BEINGS.get(being.lower())
    if not profile:
        raise ValueError(f"Unknown being: {being}. Known: {list(BEINGS)}")

    existing = [p for p in wav_files if p.exists()]
    if not existing:
        raise FileNotFoundError(f"No WAV files found: {wav_files}")

    tier_map = {"ultra": Tier.ULTRA, "premium": Tier.PREMIUM, "basic": Tier.BASIC}
    tier = tier_map.get(profile["tier"], Tier.ULTRA)

    orch = VoiceSynthesisOrchestrator(tier=tier)

    metadata = VoicepackMetadata(
        name=profile.get("label", being.title()),
        tier=profile["tier"],
        emotions=profile["emotions"],
        sample_count=len(existing),
    )

    print(f"  Building voicepack for: {being}")
    print(f"  WAV files: {[p.name for p in existing]}")
    print(f"  Tier: {profile['tier']} | Emotions: {len(profile['emotions'])}")

    voicepack_path = orch.train_voice(
        audio_files=existing,
        voice_name=being.lower(),
        metadata=metadata,
        custom_emotions=profile["emotions"],
    )

    # Move to project voicepacks dir if not already there
    VOICEPACK_DIR.mkdir(parents=True, exist_ok=True)
    dest = VOICEPACK_DIR / f"{being.lower()}.voicepack"
    if voicepack_path != dest:
        import shutil
        shutil.copy(voicepack_path, dest)

    print(f"  ✅ Voicepack written: {dest}")
    return dest


def main():
    parser = argparse.ArgumentParser(
        description="Build a .voicepack from WAV reference files for a Christman AI being."
    )
    parser.add_argument("--being", type=str, help="Being name (e.g. brockston, giuseppe)")
    parser.add_argument("--wav", nargs="+", type=Path, help="One or more reference WAV files")
    parser.add_argument("--list-beings", action="store_true", help="List all known beings")
    args = parser.parse_args()

    if args.list_beings:
        print("\nKnown beings:")
        for name, cfg in BEINGS.items():
            existing = (VOICEPACK_DIR / f"{name}.voicepack").exists()
            status = "✅ voicepack exists" if existing else "○  no voicepack yet"
            print(f"  {name:<12} {status}")
        return

    if not args.being or not args.wav:
        parser.print_help()
        sys.exit(1)

    build(args.being, args.wav)


if __name__ == "__main__":
    main()
