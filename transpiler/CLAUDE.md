# IR-based Transpiler

Transpiles `../src/parable.py` to multiple target languages via an intermediate representation.

## Status

| Backend    | Status      |
| ---------- | ----------- |
| Go         | ✓ Done      |
| Python     | ✓ Done      |
| TypeScript | ✓ Done      |
| Java       | In progress |

## Architecture

```
../src/parable.py  →  frontend.py  →  IR  →  middleend.py  →  backend/*.py  →  dist/
```

- `./src/ir.py` - IR node definitions (types, expressions, statements). Does NOT define middleend annotations.
- `./src/frontend.py` - Python AST → IR
- `./src/middleend.py` - IR analysis (scope/flow tracking, dynamic annotations)
- `./src/backend/go.py` - IR → Go
- `./src/backend/python.py` - IR → Python
- `./src/backend/typescript.py` - IR → TypeScript
- `./src/backend/java.py` - IR → Java
- `./src/cli.py` - CLI entry point

## Paths

| Path                | Description       |
| ------------------- | ----------------- |
| `../src/parable.py` | Python source     |
| `dist/go/`          | Go output         |
| `dist/python/`      | Python output     |
| `dist/ts/`          | TypeScript output |
| `dist/java/`        | Java output       |

## Just Targets

```
just backend-transpile <backend>   # transpile to dist/<backend>/
just backend-test <backend>        # transpile, compile, run tests
```

Backends: `go`, `python`, `ts`, `java`

## Debugging Test Failures

All test runners support `-f <pattern>` to filter by test name or file path:

```bash
# Go
go run -C dist/go ./cmd/run-tests /path/to/tests -f 01_words

# Python
PYTHONPATH=dist/python python3 tests/bin/run-tests.py -f 01_words

# TypeScript
node tests/bin/run-js-tests.js dist/js -f 01_words

# Java
java -cp dist/java/classes Parable --run-tests tests -f 01_words
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
