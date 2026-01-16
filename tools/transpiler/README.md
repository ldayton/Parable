# transpiler

Python to JavaScript transpiler for Parable.

```bash
# Transpile parable.py to JavaScript
uv run transpiler --transpile src/parable.py > src/parable.js

# Check for banned Python constructs that don't transpile cleanly
uv run transpiler --check-style src/
```

## Banned constructs

The style checker enforces a restricted Python subset that translates cleanly to JS/Go/Rust. See `check_style.py` for the full list, including:

- List/dict/set comprehensions (use explicit loops)
- Generator expressions (use explicit loops)
- Walrus operator (assign first, then test)
- Negative indexing (use `len(x)-n`)
- `//` floor division (use `int(a / b)`)
- `enumerate`, `zip`, `reversed` (use indexed loops)
- `with` statement (use try/finally)
