#!/usr/bin/env python3
"""
remove_merge_markers.py
The Christman AI Project / Luma Cognify AI

Removes git merge conflict markers from any project directory.
Always keeps YOUR version (HEAD / ours).

Usage:
  python remove_merge_markers.py                  ← Scan current directory
  python remove_merge_markers.py --dir /path      ← Scan specific directory
  python remove_merge_markers.py --theirs         ← Keep THEIR version instead
  python remove_merge_markers.py --dry-run        ← Preview only, no changes
  python remove_merge_markers.py --ext py,ts,tsx  ← Specific file types only

© 2026 Everett Nathaniel Christman & The Christman AI Project
Luma Cognify AI — "How can we help you love yourself more?"
"""

import argparse
import os
import re
import sys
from pathlib import Path


# ── ANSI Colors ───────────────────────────────────────────────────────────────

class C:
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    WHITE  = "\033[97m"
    DIM    = "\033[2m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"

    @classmethod
    def disable(cls):
        for attr in ["RED","GREEN","YELLOW","CYAN","WHITE","DIM","BOLD","RESET"]:
            setattr(cls, attr, "")

def c(text, *codes):
    return "".join(codes) + str(text) + C.RESET


# ── Default file extensions to scan ──────────────────────────────────────────

DEFAULT_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx",
    ".css", ".html", ".json", ".md", ".txt",
    ".yaml", ".yml", ".sh", ".env",
}

# ── Always skip these directories ────────────────────────────────────────────

SKIP_DIRS = {
    "venv", "__pycache__", "node_modules", ".git",
    "dist", "build", ".next", "coverage",
    ".turbo", "out", ".cache",
}


# ── Core conflict stripper ────────────────────────────────────────────────────

CONFLICT_PATTERN = re.compile(
    r'<<<<<<< .*?\n'   # conflict start marker
    r'(.*?)'           # HEAD / ours section
    r'=======\n'       # divider
    r'(.*?)'           # THEIRS section
    r'>>>>>>> [^\n]*\n?',  # conflict end marker
    re.DOTALL
)


def remove_markers(content: str, keep_ours: bool = True) -> tuple[str, int]:
    """
    Remove all merge conflict markers from content.
    Returns (cleaned_content, conflict_count).
    keep_ours=True  → keep HEAD section
    keep_ours=False → keep THEIRS section
    """
    count = len(CONFLICT_PATTERN.findall(content))
    if count == 0:
        return content, 0

    def replacer(m):
        ours   = m.group(1)
        theirs = m.group(2)
        return ours if keep_ours else theirs

    cleaned = CONFLICT_PATTERN.sub(replacer, content)
    return cleaned, count


def has_markers(content: str) -> bool:
    return "<<<<<<< " in content


# ── File scanner ──────────────────────────────────────────────────────────────

def scan_and_fix(
    root_dir: str,
    extensions: set,
    keep_ours: bool = True,
    dry_run: bool = False,
) -> tuple[list, list, list]:
    """
    Walk root_dir and fix all files with conflict markers.
    Returns (fixed_files, skipped_files, error_files).
    """
    fixed   = []
    skipped = []
    errors  = []

    root = Path(root_dir)

    for dirpath, dirs, files in os.walk(root):
        # Prune skip dirs in-place
        dirs[:] = [d for d in sorted(dirs)
                   if d not in SKIP_DIRS and not d.startswith(".")]

        for filename in sorted(files):
            filepath = Path(dirpath) / filename
            ext      = filepath.suffix.lower()

            if ext not in extensions:
                continue

            try:
                content = filepath.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                errors.append((str(filepath), str(e)))
                continue

            if not has_markers(content):
                skipped.append(str(filepath))
                continue

            cleaned, count = remove_markers(content, keep_ours=keep_ours)

            rel = filepath.relative_to(root)
            if dry_run:
                fixed.append((str(rel), count, "DRY RUN"))
            else:
                try:
                    filepath.write_text(cleaned, encoding="utf-8")
                    fixed.append((str(rel), count, "FIXED"))
                except Exception as e:
                    errors.append((str(filepath), str(e)))

    return fixed, skipped, errors


# ── Report ────────────────────────────────────────────────────────────────────

def print_report(
    fixed: list,
    skipped: list,
    errors: list,
    keep_ours: bool,
    dry_run: bool,
    root_dir: str,
):
    print()
    print(c("  ╔══════════════════════════════════════════════════════════════════════╗", C.DIM))
    print(c("  ║  MERGE MARKER REMOVER — The Christman AI Project                     ║", C.WHITE, C.BOLD))
    print(c("  ╠══════════════════════════════════════════════════════════════════════╣", C.DIM))

    kept = "HEAD (yours)" if keep_ours else "THEIRS (incoming)"
    mode = "DRY RUN — no files changed" if dry_run else "LIVE — files rewritten"

    print(c(f"  ║  DIR    : {root_dir[:58]}", C.DIM))
    print(c(f"  ║  KEPT   : {kept}", C.CYAN))
    print(c(f"  ║  MODE   : {mode}", C.YELLOW if dry_run else C.GREEN))
    print(c("  ╠══════════════════════════════════════════════════════════════════════╣", C.DIM))

    if fixed:
        print()
        label = "WOULD FIX" if dry_run else "FIXED"
        print(c(f"  {label} ({len(fixed)} files):", C.GREEN, C.BOLD))
        print()
        for rel, count, status in fixed:
            marker = c("⚡", C.YELLOW) if dry_run else c("✅", C.GREEN)
            print(f"  {marker}  {c(rel, C.WHITE)}  {c(f'({count} conflict block(s))', C.DIM)}")
    else:
        print()
        print(c("  ✅ No conflict markers found — repo is clean.", C.GREEN, C.BOLD))

    if errors:
        print()
        print(c(f"  ERRORS ({len(errors)} files):", C.RED, C.BOLD))
        for filepath, err in errors:
            print(f"  {c('❌', C.RED)}  {c(filepath, C.WHITE)}  {c(err, C.DIM)}")

    print()
    print(c("  ╠══════════════════════════════════════════════════════════════════════╣", C.DIM))
    print(c(f"  ║  FILES WITH CONFLICTS : {len(fixed):<45}║", C.WHITE))
    print(c(f"  ║  FILES CLEAN          : {len(skipped):<45}║", C.DIM))
    print(c(f"  ║  ERRORS               : {len(errors):<45}║", C.RED if errors else C.DIM))
    print(c("  ╚══════════════════════════════════════════════════════════════════════╝", C.DIM))

    if fixed and not dry_run:
        print()
        print(c("  Next steps:", C.WHITE, C.BOLD))
        print(c("  git add .", C.GREEN))
        print(c('  git commit -m "remove merge markers — keep local HEAD"', C.GREEN))
        print(c("  git push origin master", C.GREEN))

    print()
    print(c('  "How can we help you love yourself more?"', C.GREEN))
    print(c("  © 2026 Everett Nathaniel Christman & The Christman AI Project", C.DIM))
    print()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Remove git merge conflict markers. Always keeps YOUR version by default.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python remove_merge_markers.py
  python remove_merge_markers.py --dir /Users/EverettN/AlphaVox
  python remove_merge_markers.py --dry-run
  python remove_merge_markers.py --theirs
  python remove_merge_markers.py --ext py,ts,tsx,css
        """
    )
    parser.add_argument("--dir",     default=".",  help="Directory to scan (default: current)")
    parser.add_argument("--theirs",  action="store_true", help="Keep THEIR version instead of yours")
    parser.add_argument("--dry-run", action="store_true", help="Preview only — make no changes")
    parser.add_argument("--ext",     default="",   help="Comma-separated extensions to scan (e.g. py,ts,tsx)")
    parser.add_argument("--no-color",action="store_true", help="Disable color output")
    args = parser.parse_args()

    if args.no_color or not sys.stdout.isatty():
        C.disable()

    root_dir = os.path.abspath(args.dir)
    if not os.path.isdir(root_dir):
        print(f"ERROR: {root_dir} is not a directory.")
        sys.exit(1)

    # Build extension set
    if args.ext:
        extensions = {"." + e.strip().lstrip(".").lower() for e in args.ext.split(",")}
    else:
        extensions = DEFAULT_EXTENSIONS

    keep_ours = not args.theirs

    print()
    print(c("  Scanning for merge conflict markers...", C.DIM))

    fixed, skipped, errors = scan_and_fix(
        root_dir=root_dir,
        extensions=extensions,
        keep_ours=keep_ours,
        dry_run=args.dry_run,
    )

    print_report(fixed, skipped, errors, keep_ours, args.dry_run, root_dir)

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

# ==============================================================================
# © 2026 Everett Nathaniel Christman & The Christman AI Project
# Luma Cognify AI — "How can we help you love yourself more?"
# Drop this script into ANY project and run it.
# No dependencies. Pure Python 3. Works everywhere.
# ==============================================================================

