# New IR-based Transpiler

Converting the existing Go transpiler at `../tools/transpiler/` from a Go-specific transpiler to a generic one with an IR layer. The old transpiler works and is used by `just transpile-go` in the main project.

Transpiles `../src/parable.py` → Go via an intermediate representation.

## Architecture

```
../src/parable.py  →  frontend.py  →  IR  →  backend/go.py  →  ../src/parable.go
```

- `./src/ir.py` - IR node definitions (types, expressions, statements)
- `./src/frontend.py` - Python AST → IR (not yet created)
- `./src/backend/go.py` - IR → Go code (not yet created)
- `./src/cli.py` - CLI entry point

## Paths

| Path                   | Description                        |
| ---------------------- | ---------------------------------- |
| `../tools/transpiler/` | Old working Go-specific transpiler |
| `../src/parable.py`    | Python source to transpile         |
| `../src/parable.go`    | Go output                          |

## Just Targets

```
just emit    # transpile to stdout
just go      # transpile and write to ../src/parable.go
just check   # transpile and verify Go compiles
just test    # transpile, write, run Go tests
just errors  # show Go compilation errors
```

## Design Goals

- Generic backend: no source-language assumptions in IR → Go emission
- Frontend handles all Python-specific translations
- IR is the contract between frontend and backend

## Backend Rules

`./src/backend/go.py` must be completely generic:
- No Python-specific code (no `join`, `append`, `isalnum` translations)
- No Parable-specific code (no `Node`, `Stack`, field name assumptions)
- Only emits Go from IR nodes - nothing else
- All source language quirks handled in frontend before IR generation
