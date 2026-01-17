# bash-oracle

Patched bash that dumps its internal AST as s-expressions. Used as an oracle to validate Parable's parser output.

## Source

https://github.com/ldayton/bash-oracle

## Build

```bash
cd ~/source/bash-oracle
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

## Helper Scripts

```bash
cd tools/bash-oracle

# Verify test expectations against bash-oracle
uv run oracle --verify-tests

# Run Parable against bigtable-bash corpus
uv run oracle --run-corpus

# Convert test corpora
uv run oracle --convert-gnu-bash
uv run oracle --convert-oils
uv run oracle --convert-tree-sitter
```

## Files

- `src/oracle/` - Helper scripts for test corpus conversion
