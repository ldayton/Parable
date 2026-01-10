set shell := ["bash", "-o", "pipefail", "-cu"]
project := "parable"

_test version *ARGS:
    UV_PROJECT_ENVIRONMENT=.venv-{{version}} uv run --python {{version}} bin/run-tests.py {{ARGS}} 2>&1 | sed -u "s/^/[{{version}}] /" | tee /tmp/{{project}}-test-{{version}}.log

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
    uv lock --check 2>&1 | sed -u "s/^/[lock] /" | tee /tmp/{{project}}-lock.log

# Run all checks (tests, lint, format, lock, style) in parallel
[parallel]
check: test-all lint fmt lock-check check-dump-ast check-style test-js fmt-js lint-js

# Run benchmarks (--fast for quick run)
bench *ARGS:
    PYTHONPATH=src uvx --with pyperf python bench/bench_parse.py {{ARGS}}

# Lint (--fix to apply changes)
lint *ARGS:
    uvx ruff check {{ if ARGS == "--fix" { "--fix" } else { "" } }} 2>&1 | sed -u "s/^/[lint] /" | tee /tmp/{{project}}-lint.log

# Format (--fix to apply changes)
fmt *ARGS:
    uvx ruff format {{ if ARGS == "--fix" { "" } else { "--check" } }} 2>&1 | sed -u "s/^/[fmt] /" | tee /tmp/{{project}}-fmt.log

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
    python3 bin/check-style.py 2>&1 | sed -u "s/^/[style] /" | tee /tmp/{{project}}-style.log

# Transpile Python to JavaScript
transpile:
    python3 bin/transpile.py src/parable.py > src/parable.js
    npx -y @biomejs/biome format --write src/parable.js
    npx -y @biomejs/biome lint --only=correctness --skip=noUndeclaredVariables --skip=noUnusedVariables --skip=noInnerDeclarations src/parable.js

# Run JavaScript tests
test-js *ARGS:
    node bin/run-js-tests.js {{ARGS}}

# Format JavaScript (--fix to apply changes)
fmt-js *ARGS:
    npx -y @biomejs/biome format {{ if ARGS == "--fix" { "--write" } else { "" } }} src/parable.js 2>&1 | sed -u "s/^/[fmt-js] /" | tee /tmp/{{project}}-fmt-js.log

# Lint JavaScript (--fix to apply changes)
lint-js *ARGS:
    npx -y @biomejs/biome lint --only=correctness --skip=noUndeclaredVariables --skip=noUnusedVariables --skip=noInnerDeclarations {{ if ARGS == "--fix" { "--write" } else { "" } }} src/parable.js 2>&1 | sed -u "s/^/[lint-js] /" | tee /tmp/{{project}}-lint-js.log
