# bash-oracle

Patched bash that dumps its internal AST as s-expressions. Used as an oracle to validate Parable's parser output.

## Source

Development happens in the bash-oracle branch: https://github.com/ldayton/bash-oracle/tree/bash-oracle

## Build

```bash
cd ~/source/bash
git checkout bash-oracle
just build
```

## Usage

Parse from stdin:
```bash
echo 'echo hello world' | ./bash-oracle --dump-ast
# (command (word "echo") (word "hello") (word "world"))
```

Generate .tests files from a directory of scripts:
```bash
./bash-oracle --write-tests /path/to/scripts /path/to/output
# Creates one .tests file per script with AST or !error
```

## How it works

The patch modifies bash to:
1. Add `--dump-ast` flag for stdin parsing
2. Add `--write-tests INDIR OUTDIR` for batch .tests generation
3. Hardcode `read_but_dont_execute = 1` (never executes commands)
4. Gut `execute_command()` as a failsafe
5. Output s-expressions matching Parable's AST format

## Files

- `bash-oracle.patch` - Patch for bash (generated via `just patchfile` in bash repo)
- `bin/` - Helper scripts for test corpus conversion

## Updating the patch

After making changes in the bash repo:
```bash
cd ~/source/bash
git checkout bash-oracle
# make changes, commit
just patchfile  # writes to ~/source/Parable/tools/bash-oracle/bash-oracle.patch
```
