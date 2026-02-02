# Parable Python

```bash
# Transpile (writes to src/parable/parable.py)
uv run --directory /path/to/transpiler python -m src.tongues --target python < /path/to/parable.py > src/parable/parable.py

# Run tests
uv run parable-test /path/to/tests
```
