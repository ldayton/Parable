#!/usr/bin/env python3
"""Extract bash code from Nix files."""

import argparse
import re
import sys
from pathlib import Path

PHASE_ATTRS = [
    "buildPhase",
    "installPhase",
    "checkPhase",
    "configurePhase",
    "unpackPhase",
    "patchPhase",
    "fixupPhase",
    "preBuild",
    "postBuild",
    "preInstall",
    "postInstall",
    "preCheck",
    "postCheck",
    "preConfigure",
    "postConfigure",
    "preFixup",
    "postFixup",
    "shellHook",
]

ATTR_PATTERN = re.compile(
    r"(?:" + "|".join(PHASE_ATTRS) + r")\s*=\s*''(.*?)''(?=\s*;)",
    re.DOTALL,
)


def unescape_nix_string(s: str) -> str:
    """Convert Nix '' string escapes to literal characters."""
    # Order matters: ''' -> '' must come before ''$ -> $ etc.
    s = s.replace("'''", "\x00NIX_QUOTE\x00")
    s = s.replace("''$", "$")
    s = s.replace("''\\", "\\")
    s = s.replace("\x00NIX_QUOTE\x00", "''")
    return s


def extract_bash_from_nix(content: str) -> list[str]:
    """Extract all bash snippets from a Nix file's content."""
    snippets = []
    for match in ATTR_PATTERN.finditer(content):
        bash = unescape_nix_string(match.group(1))
        # Strip leading newline that's conventional in Nix
        bash = bash.lstrip("\n")
        if bash.strip():
            snippets.append(bash)
    return snippets


def extract_from_file(path: Path) -> list[str]:
    """Extract bash from a single Nix file."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        return extract_bash_from_nix(content)
    except Exception as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        return []


NIXPKGS_DEFAULT = Path.home() / "source" / "nixpkgs" / "pkgs"


def main():
    parser = argparse.ArgumentParser(description="Extract bash from Nix files")
    parser.add_argument("paths", nargs="*", type=Path, help="Nix files or directories")
    parser.add_argument("-o", "--output-dir", type=Path, help="Output directory for extracted bash")
    parser.add_argument("--separator", default="\n---\n", help="Separator between snippets")
    parser.add_argument("--stats", action="store_true", help="Print statistics only")
    args = parser.parse_args()
    if not args.paths:
        args.paths = [NIXPKGS_DEFAULT]

    all_files: list[Path] = []
    for p in args.paths:
        if p.is_file():
            all_files.append(p)
        elif p.is_dir():
            all_files.extend(p.rglob("*.nix"))

    total_snippets = 0
    total_lines = 0

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)

    for nix_file in sorted(all_files):
        snippets = extract_from_file(nix_file)
        if not snippets:
            continue

        total_snippets += len(snippets)
        for snippet in snippets:
            total_lines += snippet.count("\n") + 1

        if args.stats:
            continue

        if args.output_dir:
            # Write each snippet to a separate file
            rel = nix_file.name
            for i, snippet in enumerate(snippets):
                out_path = args.output_dir / f"{rel}.{i}.bash"
                out_path.write_text(snippet)
        else:
            for snippet in snippets:
                print(snippet)
                print(args.separator)

    if args.stats:
        print(f"Files scanned: {len(all_files)}")
        print(f"Snippets extracted: {total_snippets}")
        print(f"Lines of bash: {total_lines}")


if __name__ == "__main__":
    main()
