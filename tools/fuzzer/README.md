# Fuzzer

Differential fuzzers comparing Parable vs bash-oracle.

```bash
uv run fuzzer --help              # show all modes
uv run fuzzer gen --help          # mode-specific help
```

## Modes

### Character Mutation
Mutates test corpus inputs with random character changes.

```bash
uv run fuzzer char -n 5000
uv run fuzzer char --stop-after 10 -v
uv run fuzzer char --both-succeed --stop-after 5
```

### Structural Transformation
Wraps inputs in structural constructs like `$()`, `<()`, `{ }`.

```bash
uv run fuzzer struct --list-transforms
uv run fuzzer struct --stop-after 10
uv run fuzzer struct --transforms subshell,cmdsub
```

### Generator
Generates bash scripts from scratch using grammar rules.

```bash
uv run fuzzer gen -n 1000
uv run fuzzer gen --stop-after 5 -v

# Layer control
uv run fuzzer gen --list-layers              # show available layers
uv run fuzzer gen --layer 0 --dry-run 5      # literals only
uv run fuzzer gen --layer 5 -n 1000          # up to simple commands
uv run fuzzer gen --layer words              # preset: layers 0-2
uv run fuzzer gen --layer control            # preset: layers 0-10
uv run fuzzer gen --layer 3-7                # range: cmd_sub to pipelines

# Output
uv run fuzzer gen -n 1000 -o discrepancies.txt
uv run fuzzer gen -n 1000 --minimize -o discrepancies.txt
```

### Minimize
Reduces a discrepancy to its minimal reproducing example via delta debugging.

```bash
uv run fuzzer min 'echo $(cat <<EOF
test
EOF
)'
uv run fuzzer min @failing.sh             # from file
echo 'input' | uv run fuzzer min          # from stdin
uv run fuzzer min -v -t 30 @input.sh      # verbose, 30s timeout
```

## Requirements

Requires bash-oracle at `~/source/bash-oracle/bash-oracle`.
