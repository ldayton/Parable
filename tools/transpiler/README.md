# transpiler

Python to JavaScript transpiler for Parable. TypeScript definitions are auto-generated from the transpiled JS.

```bash
# Transpile parable.py to JavaScript
uv run transpiler --transpile-js src/parable.py > src/parable.js

# Generate TypeScript definitions from JavaScript
uv run transpiler --transpile-dts src/parable.js > src/parable.d.ts

# Check for banned Python constructs that don't transpile cleanly
uv run transpiler --check-style src/
```

## Banned constructs

The style checker enforces a restricted Python subset that translates cleanly to JS/TS. See `check_style.py` for the full list, including:

- List/dict/set comprehensions (use explicit loops)
- Generator expressions (use explicit loops)
- Walrus operator (assign first, then test)
- Negative indexing (use `len(x)-n`)
- `//` floor division (use `int(a / b)`)
- `enumerate`, `zip`, `reversed` (use indexed loops)
- `with` statement (use try/finally)
