# New IR-based Transpiler

Converting the existing Go transpiler at `../tools/transpiler/` from a Go-specific transpiler to a generic one with an IR layer. The old transpiler works and is used by `just transpile-go` in the main project.

Transpiles `../src/parable.py` → Go via an intermediate representation.

## Architecture

```
../src/parable.py  →  frontend.py  →  IR  →  middleend.py  →  backend/go.py  →  dist/parable.go
```

- `./src/ir.py` - IR node definitions (types, expressions, statements). Does NOT define middleend annotations.
- `./src/frontend.py` - Python AST → IR
- `./src/middleend.py` - IR analysis (scope/flow tracking, dynamic annotations)
- `./src/backend/go.py` - IR → Go code
- `./src/cli.py` - CLI entry point

## Paths

| Path                   | Description                                    |
| ---------------------- | ---------------------------------------------- |
| `../tools/transpiler/` | Old working Go-specific transpiler             |
| `../src/parable.py`    | Python source to transpile                     |
| `../src/parable.go`    | Go output (old transpiler, used in production) |
| `dist/parable.go`      | Go output (new transpiler, under development)  |

## Just Targets

```
just emit          # transpile to stdout
just go            # transpile and write to dist/parable.go
just check         # transpile and verify Go compiles
just test          # transpile, write, run Go tests
just test-all      # run all backend compilation tests
just errors        # show Go compilation errors
```

## Phase Responsibilities

**Frontend** - Source language translation
- Parse Python AST and emit IR
- Handle ALL Python-specific semantics:
  - String methods (`join`, `split`, `isalnum`, etc.) → generic IR calls
  - Operators (`in`, `not in`) → appropriate IR expressions
  - Tuple indexing → `FieldAccess`, not `Index`
  - Pointer/deref decisions → emit `Deref` nodes when needed
- The IR should be complete - backends should never compensate for frontend gaps

**Middleend** - IR analysis (read-only)
- Compute properties that require scope/flow tracking:
  - `is_declaration` - first assignment to a variable (needs scope tracking)
  - `is_reassigned` - variable assigned after declaration
  - `is_modified` - parameter mutated in function body
- Annotations are dynamic attributes, NOT defined in ir.py
- No transformations - only adds information, never rewrites IR
- No source language knowledge, no target language knowledge

**Backend** - Target language emission
- Syntax emission from IR nodes using IR's type information
- Legitimate: type-based syntax choices (e.g., `Slice` → `[]T`, `var x T` vs `x :=`)
- NOT legitimate: compensating for missing frontend translations
- No Python-specific code (no `join`, `isalnum` - frontend's job)
- No Parable-specific code (no `Node`, `quoteStackEntry`, `"stack"` heuristics)
- Generic: could emit any target language from the same IR
