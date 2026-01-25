set shell := ["bash", "-o", "pipefail", "-cu"]
project := "parable"
run_id := `head -c 16 /dev/urandom | xxd -p`

_test version *ARGS:
    UV_PROJECT_ENVIRONMENT=.venv-{{version}} uv run --python {{version}} tests/bin/run-tests.py {{ARGS}} 2>&1 | sed -u "s/^/[{{version}}] /" | tee /tmp/{{project}}-{{run_id}}-test-{{version}}.log

# Run tests on CPython 3.8
test-cpy38 *ARGS: (_test "3.8" ARGS)
# Run tests on CPython 3.9
test-cpy39 *ARGS: (_test "3.9" ARGS)
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
test *ARGS: check-style (_test "3.14" ARGS)

# Verify test expectations match bash-oracle (skips if no binary available)
verify-tests:
    #!/usr/bin/env bash
    set -e
    check_binary() {
        local path="$1"
        if ! "$path" -e 'echo' >/dev/null 2>&1; then
            echo "Skipping verify-tests: binary not compatible ($(file -b "$path"))"
            exit 0
        fi
    }
    # Check env var first
    if [[ -n "${BASH_ORACLE:-}" && -x "$BASH_ORACLE" ]]; then
        check_binary "$BASH_ORACLE"
        exec tools/bash-oracle/src/oracle/verify_tests.py
    fi
    # Check dev location
    if [[ -x "$HOME/source/bash-oracle/bash-oracle" ]]; then
        check_binary "$HOME/source/bash-oracle/bash-oracle"
        BASH_ORACLE="$HOME/source/bash-oracle/bash-oracle" exec tools/bash-oracle/src/oracle/verify_tests.py
    fi
    # Try to download
    ORACLE_PATH="/tmp/bash-oracle"
    case "$(uname -s)-$(uname -m)" in
        Linux-x86_64)   URL="http://ldayton-parable.s3-website-us-east-1.amazonaws.com/bash-oracle/linux/bash-oracle" ;;
        Darwin-*)       URL="http://ldayton-parable.s3-website-us-east-1.amazonaws.com/bash-oracle/macos/bash-oracle" ;;
        *) echo "Skipping verify-tests: no binary for $(uname -s)-$(uname -m)"; exit 0 ;;
    esac
    echo "Downloading bash-oracle from $URL"
    if ! curl -sSf --retry 3 --retry-delay 2 --max-time 30 -o "$ORACLE_PATH" "$URL"; then
        echo "Skipping verify-tests: download failed"
        exit 0
    fi
    chmod +x "$ORACLE_PATH"
    check_binary "$ORACLE_PATH"
    BASH_ORACLE="$ORACLE_PATH" exec tools/bash-oracle/src/oracle/verify_tests.py

# Run tests on all supported CPython versions (parallel)
[parallel]
test-cpy: test-cpy38 test-cpy39 test-cpy310 test-cpy311 test-cpy312 test-cpy313 test-cpy314

# Run tests on PyPy
test-pypy: test-pypy311

# Run tests on all supported Python versions (parallel)
[parallel]
test-all: test-cpy test-pypy

# Run the fuzzer (e.g., just fuzz char --stop-after 10)
fuzz *ARGS:
    FUZZER_ORIG_CWD="{{invocation_directory()}}" uv run --directory tools/fuzzer fuzzer {{ARGS}}

# Run the fuzzer agent
fuzzer-agent *ARGS:
    uv run --directory tools/fuzzer-agent fuzzer-agent {{ARGS}}

# Run Parable against the bigtable-bash corpus
run-corpus *ARGS:
    tools/bash-oracle/src/oracle/run_corpus.py {{ARGS}}

# Verify lock file is up to date
lock-check:
    uv lock --check 2>&1 | sed -u "s/^/[lock] /" | tee /tmp/{{project}}-{{run_id}}-lock.log

# Ensure biome is installed (prevents race condition in parallel JS checks)
_ensure-biome:
    @npx -y @biomejs/biome --version >/dev/null 2>&1

# Internal: run all parallel checks
[parallel]
_check-parallel: test-all lint fmt lock-check check-dump-ast check-style check-transpile test-js fmt-js fmt-dts check-dts

# Run all checks (tests, lint, format, lock, style) in parallel
check: _ensure-biome _check-parallel

# Quick check: test, transpile-js, test-js
quick-check: test transpile-js test-js

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
transpile-js output="src/parable.js":
    #!/usr/bin/env bash
    set -euo pipefail
    js_out="{{output}}"
    [[ "$js_out" = /* ]] || js_out="$(pwd)/$js_out"
    uv run --directory tools/transpiler transpiler --transpile-js "$(pwd)/src/parable.py" > "$js_out"
    npx -y @biomejs/biome format --write "$js_out" >/dev/null 2>&1
    npx -y @biomejs/biome format --write "$js_out" >/dev/null 2>&1

# Generate TypeScript definitions from JavaScript
transpile-dts input="src/parable.js" output="src/parable.d.ts" py_src="src/parable.py":
    #!/usr/bin/env bash
    set -euo pipefail
    js_in="{{input}}"
    dts_out="{{output}}"
    py_in="{{py_src}}"
    [[ "$js_in" = /* ]] || js_in="$(pwd)/$js_in"
    [[ "$dts_out" = /* ]] || dts_out="$(pwd)/$dts_out"
    [[ "$py_in" = /* ]] || py_in="$(pwd)/$py_in"
    uv run --directory tools/transpiler transpiler --transpile-dts "$js_in" "$py_in" > "$dts_out"
    npx -y @biomejs/biome format --write "$dts_out" >/dev/null 2>&1

# Transpile Python to Go
transpile-go output="src/parable.go":
    #!/usr/bin/env bash
    set -euo pipefail
    go_out="{{output}}"
    [[ "$go_out" = /* ]] || go_out="$(pwd)/$go_out"
    uv run --directory tools/transpiler transpiler --transpile-go "$(pwd)/src/parable.py" > "$go_out"
    gofmt -w "$go_out"
    go build -C src -o /dev/null .

# Check that parable.js and parable.d.ts are up-to-date with transpiler output
check-transpile:
    @just transpile-js /tmp/{{project}}-{{run_id}}-transpile.js && \
    just transpile-dts /tmp/{{project}}-{{run_id}}-transpile.js /tmp/{{project}}-{{run_id}}-transpile.d.ts && \
    if diff -q src/parable.js /tmp/{{project}}-{{run_id}}-transpile.js >/dev/null 2>&1; then \
        echo "[check-transpile-js] OK"; \
    else \
        echo "[check-transpile-js] FAIL: parable.js is out of date, run 'just transpile'" >&2; \
        exit 1; \
    fi && \
    if diff -q src/parable.d.ts /tmp/{{project}}-{{run_id}}-transpile.d.ts >/dev/null 2>&1; then \
        echo "[check-transpile-dts] OK"; \
    else \
        echo "[check-transpile-dts] FAIL: parable.d.ts is out of date, run 'just transpile'" >&2; \
        exit 1; \
    fi

# Check that parable.go is up-to-date with transpiler output
check-transpile-go:
    @just transpile-go /tmp/{{project}}-{{run_id}}-transpile.go && \
    if diff -q src/parable.go /tmp/{{project}}-{{run_id}}-transpile.go >/dev/null 2>&1; then \
        echo "[check-transpile-go] OK"; \
    else \
        echo "[check-transpile-go] FAIL: parable.go is out of date, run 'just transpile-go'" >&2; \
        exit 1; \
    fi

# Build Go (verifies parable.go compiles)
build-go:
    go build -C src -o /dev/null .

# Run Go tests
test-go *ARGS:
    go run -C src ./cmd/run-tests {{ARGS}}

# Format Go (--fix to apply changes)
fmt-go *ARGS:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ "{{ARGS}}" = "--fix" ]; then
        gofmt -w src/parable.go
        echo "[fmt-go] OK"
    else
        diff_output=$(gofmt -d src/parable.go)
        if [ -z "$diff_output" ]; then
            echo "[fmt-go] OK"
        else
            echo "[fmt-go] FAIL: src/parable.go needs formatting, run 'just fmt-go --fix'" >&2
            echo "$diff_output" >&2
            exit 1
        fi
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

# Format TypeScript definitions (--fix to apply changes)
fmt-dts *ARGS:
    npx -y @biomejs/biome format {{ if ARGS == "--fix" { "--write" } else { "" } }} src/parable.d.ts 2>&1 | sed -u "s/^/[fmt-dts] /" | tee /tmp/{{project}}-{{run_id}}-fmt-dts.log

# Type-check TypeScript definitions
check-dts:
    npx -y -p typescript tsc --noEmit 2>&1 | sed -u "s/^/[check-dts] /" | tee /tmp/{{project}}-{{run_id}}-check-dts.log
