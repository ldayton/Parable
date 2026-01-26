# New IR-based Transpiler

Converting the existing Go transpiler at `../tools/transpiler/` from a Go-specific transpiler to a generic one with an IR layer. The old transpiler works and is used by `just transpile-go` in the main project.

Transpiles `../src/parable.py` → Go via an intermediate representation.

## Architecture

```
../src/parable.py  →  frontend.py  →  IR  →  middleend.py  →  backend/go.py  →  ../src/parable.go
```

- `./src/ir.py` - IR node definitions (types, expressions, statements). Does NOT define middleend annotations.
- `./src/frontend.py` - Python AST → IR
- `./src/middleend.py` - IR analysis and transformations
- `./src/backend/go.py` - IR → Go code
- `./src/cli.py` - CLI entry point

## Paths

| Path                   | Description                        |
| ---------------------- | ---------------------------------- |
| `../tools/transpiler/` | Old working Go-specific transpiler |
| `../src/parable.py`    | Python source to transpile         |
| `../src/parable.go`    | Go output                          |

## Just Targets

```
just emit          # transpile to stdout
just go            # transpile and write to ../src/parable.go
just check         # transpile and verify Go compiles
just test          # transpile, write, run Go tests
just test-backends # run backend tests (pytest)
just errors        # show Go compilation errors
```

## Phase Responsibilities

**Frontend** - Source language translation
- Parse Python AST and emit IR
- Handle all Python-specific semantics (truthiness, iteration, string methods, etc.)
- Resolve source language idioms into generic IR constructs

**Middleend** - IR analysis (read-only)
- Analyze IR to gather information needed by backends
- Annotate nodes with computed properties at runtime (e.g., `stmt.is_declaration = True`)
- Annotations are dynamic attributes, NOT defined in ir.py
- No transformations - only adds information, never rewrites IR
- No source language knowledge, no target language knowledge

**Backend** - Target language emission
- Pure syntax emission from IR nodes
- No analysis, no decisions - just print what the IR says
- No Python-specific code (no `join`, `append`, `isalnum` translations)
- No Parable-specific code (no `Node`, `Stack`, field name assumptions)
- Generic: could emit any target language from the same IR
