set shell := ["bash", "-cu"]

_test-py version *ARGS:
    uv run --python {{version}} pytest {{ARGS}}

# Run tests on Python 3.10
test-py310 *ARGS: (_test-py "3.10" ARGS)
# Run tests on Python 3.11
test-py311 *ARGS: (_test-py "3.11" ARGS)
# Run tests on Python 3.12
test-py312 *ARGS: (_test-py "3.12" ARGS)
# Run tests on Python 3.13
test-py313 *ARGS: (_test-py "3.13" ARGS)
# Run tests on Python 3.14
test-py314 *ARGS: (_test-py "3.14" ARGS)

# Run tests (default: 3.14)
test *ARGS: (_test-py "3.14" ARGS)

# Run tests on all supported Python versions
test-all: test-py310 test-py311 test-py312 test-py313 test-py314

# Run benchmarks
bench:
    uv run --group bench python bench/bench_parse.py

# Format and lint
fmt:
    uv run ruff check --fix && uv run ruff format
