# bash-oracle

Patched bash that dumps its internal AST as s-expressions. Used as an oracle to validate Parable's parser output.

## Prerequisites

Clone bash from source:

```bash
git clone https://git.savannah.gnu.org/git/bash.git ~/source/bash
```

## Build

```bash
just build
```

This applies `bash-dump-ast.patch` to bash, rebuilds it, and copies the binary to `bash-oracle`.

## Usage

```bash
echo 'echo hello world' | ./bash-oracle --dump-ast
# (command (word "echo") (word "hello") (word "world"))

echo 'for i in a b; do echo $i; done' | ./bash-oracle --dump-ast
# (for (word "i") (in (word "a") (word "b")) (command (word "echo") (word "$i")))
```

## How it works

The patch adds a `--dump-ast` flag to bash that:
1. Parses input without executing (`read_but_dont_execute = 1`)
2. Calls `dump_command()` on the parsed AST
3. Outputs s-expressions matching Parable's format

## Files

- `bash-dump-ast.patch` - Patch adding `--dump-ast` to bash
- `justfile` - Build commands
