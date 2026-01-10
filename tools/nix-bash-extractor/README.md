# nix-bash-extractor

Extract bash code from Nix files for parser validation.

## Usage

```bash
# Stats only
python extract.py --stats /path/to/nixpkgs/pkgs

# Print all bash to stdout
python extract.py /path/to/nixpkgs/pkgs

# Write to separate files
python extract.py -o ./extracted /path/to/nixpkgs/pkgs
```

## What it extracts

Bash from these Nix attributes:
- `buildPhase`, `installPhase`, `checkPhase`, `configurePhase`
- `unpackPhase`, `patchPhase`, `fixupPhase`
- `preBuild`, `postBuild`, `preInstall`, `postInstall`
- `preCheck`, `postCheck`, `preConfigure`, `postConfigure`
- `preFixup`, `postFixup`, `shellHook`

## Nix string escaping

Handles Nix's `''` string escapes:
- `'''` → `''`
- `''$` → `$`
- `''\` → `\`
