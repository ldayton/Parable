set shell := ["bash", "-o", "pipefail", "-cu"]
project := "parable"
run_id := `head -c 16 /dev/urandom | xxd -p`

_test version *ARGS:
    UV_PROJECT_ENVIRONMENT=.venv-{{version}} uv run --python {{version}} tests/bin/run-tests.py {{ARGS}} 2>&1 | sed -u "s/^/[{{version}}] /" | tee /tmp/{{project}}-{{run_id}}-test-{{version}}.log

# Run tests on CPython 3.10
test-cpy310 *ARGS: (_test "3.10" ARGS)
# Run tests on CPython 3.11
test-cpy311 *ARGS: (_test "3.11" ARGS)
# Run tests on CPython 3.12
test-cpy312 *ARGS: (_test "3.12" ARGS)
# Run tests on CPython 3.13
test-cpy313 *ARGS: (_test "3.13" ARGS)
# Run tests on CPython 3.14
test-cpy314 *ARGS: (_test "3.14" ARGS)
# Run tests on PyPy 3.11
test-pypy311 *ARGS: (_test "pypy3.11" ARGS)

# Run tests (default: CPython 3.14)
test *ARGS: (_test "3.14" ARGS)

# Run tests on all supported CPython versions (parallel)
[parallel]
test-cpy: test-cpy310 test-cpy311 test-cpy312 test-cpy313 test-cpy314

# Run tests on PyPy
test-pypy: test-pypy311

# Run tests on all supported Python versions (parallel)
[parallel]
test-all: test-cpy test-pypy

# Verify lock file is up to date
lock-check:
    uv lock --check 2>&1 | sed -u "s/^/[lock] /" | tee /tmp/{{project}}-{{run_id}}-lock.log

# Ensure biome is installed (prevents race condition in parallel JS checks)
_ensure-biome:
    @npx -y @biomejs/biome --version >/dev/null 2>&1

# Internal: run all parallel checks
[parallel]
_check-parallel: test-all lint fmt lock-check check-dump-ast check-style check-transpile test-js fmt-js

# Run all checks (tests, lint, format, lock, style) in parallel
check: _ensure-biome _check-parallel

# Run benchmarks, optionally comparing refs: bench [ref1] [ref2] [--fast]
bench *ARGS:
    #!/usr/bin/env bash
    refs=()
    flags=()
    for arg in {{ARGS}}; do
        if [[ "$arg" == --* ]]; then
            flags+=("$arg")
        else
            refs+=("$arg")
        fi
    done
    if [[ ${#refs[@]} -eq 0 ]]; then
        PYTHONPATH=src uvx --with pyperf python bench/bench_parse.py "${flags[@]}"
    else
        uvx --with pyperf python bench/bench-compare.py "${refs[@]}" "${flags[@]}"
    fi

# Lint (--fix to apply changes)
lint *ARGS:
    uvx ruff check {{ if ARGS == "--fix" { "--fix" } else { "" } }} 2>&1 | sed -u "s/^/[lint] /" | tee /tmp/{{project}}-{{run_id}}-lint.log

# Format (--fix to apply changes)
fmt *ARGS:
    uvx ruff format {{ if ARGS == "--fix" { "" } else { "--check" } }} 2>&1 | sed -u "s/^/[fmt] /" | tee /tmp/{{project}}-{{run_id}}-fmt.log

# Verify parable-dump.py works
check-dump-ast:
    @output=$(uv run bin/parable-dump.py 'echo hello') && \
    expected='(command (word "echo") (word "hello"))' && \
    if [ "$output" = "$expected" ]; then \
        echo "[dump-ast] OK"; \
    else \
        echo "[dump-ast] FAIL: expected '$expected', got '$output'" >&2; \
        exit 1; \
    fi

# Check for banned Python constructions
check-style:
    uv run --directory tools/transpiler transpiler --check-style "$(pwd)/src" 2>&1 | sed -u "s/^/[style] /" | tee /tmp/{{project}}-{{run_id}}-style.log

# Transpile Python to JavaScript
transpile output="src/parable.js":
    uv run --directory tools/transpiler transpiler --transpile "$(pwd)/src/parable.py" > {{output}} && \
    npx -y @biomejs/biome format --write {{output}} >/dev/null 2>&1 && \
    npx -y @biomejs/biome format --write {{output}} >/dev/null 2>&1

# Check that parable.js is up-to-date with transpiler output
check-transpile:
    @just transpile /tmp/{{project}}-{{run_id}}-transpile.js && \
    if diff -q src/parable.js /tmp/{{project}}-{{run_id}}-transpile.js >/dev/null 2>&1; then \
        echo "[transpile] OK"; \
    else \
        echo "[transpile] FAIL: parable.js is out of date, run 'just transpile'" >&2; \
        exit 1; \
    fi

# Run JavaScript tests
test-js *ARGS: check-transpile
    node tests/bin/run-js-tests.js {{ARGS}}

# Run JS benchmarks, optionally comparing refs: bench-js [ref1] [ref2] [--fast]
bench-js *ARGS:
    #!/usr/bin/env bash
    [[ -d bench/node_modules ]] || npm --prefix bench install
    refs=()
    flags=()
    for arg in {{ARGS}}; do
        if [[ "$arg" == --* ]]; then
            flags+=("$arg")
        else
            refs+=("$arg")
        fi
    done
    if [[ ${#refs[@]} -eq 0 ]]; then
        node bench/bench_parse.js "${flags[@]}"
    else
        node bench/bench-compare.js "${refs[@]}" "${flags[@]}"
    fi

# Format JavaScript (--fix to apply changes)
# Note: biome format is run twice due to https://github.com/biomejs/biome/issues/4383
fmt-js *ARGS:
    npx -y @biomejs/biome format {{ if ARGS == "--fix" { "--write" } else { "" } }} src/parable.js 2>&1 | sed -u "s/^/[fmt-js] /" | tee /tmp/{{project}}-{{run_id}}-fmt-js.log
    {{ if ARGS == "--fix" { "npx -y @biomejs/biome format --write src/parable.js >/dev/null 2>&1 || true" } else { "" } }}
