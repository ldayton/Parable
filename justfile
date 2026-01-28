set shell := ["bash", "-o", "pipefail", "-cu"]

# --- Configuration ---
project := "parable"
run_id := `head -c 16 /dev/urandom | xxd -p`
backends := "go python ts"  # Testable transpiled backends

# --- Base (src/parable.py) ---

# Run parser tests against base
test *ARGS:
    uv run tests/bin/run-tests.py {{ARGS}} 2>&1 | sed -u "s/^/[test] /" | tee /tmp/{{project}}-{{run_id}}-test.log

# Lint (--fix to apply changes)
lint *ARGS:
    uvx ruff check {{ if ARGS == "--fix" { "--fix" } else { "" } }} 2>&1 | sed -u "s/^/[lint] /" | tee /tmp/{{project}}-{{run_id}}-lint.log

# Format (--fix to apply changes)
fmt *ARGS:
    uvx ruff format {{ if ARGS == "--fix" { "" } else { "--check" } }} 2>&1 | sed -u "s/^/[fmt] /" | tee /tmp/{{project}}-{{run_id}}-fmt.log

# Check for banned Python constructions
check-style:
    uv run --directory transpiler python -m src.cli --check-style "$(pwd)/src" 2>&1 | sed -u "s/^/[style] /" | tee /tmp/{{project}}-{{run_id}}-style.log

# Verify lock file is up to date
verify-lock:
    uv lock --check 2>&1 | sed -u "s/^/[verify-lock] /" | tee /tmp/{{project}}-{{run_id}}-verify-lock.log

# --- Transpiler ---

# Transpile base to dist/<backend>/
transpile backend="go":
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{backend}}" in
        go)
            out="dist/go/parable.go"
            uv run --directory transpiler python -m src.cli "$(pwd)/src/parable.py" -b go > /tmp/parable-ir.go
            gofmt /tmp/parable-ir.go > "$out"
            ;;
        python)
            mkdir -p dist/python
            uv run --directory transpiler python -m src.cli "$(pwd)/src/parable.py" -b python > dist/python/parable.py
            ;;
        ts)
            mkdir -p dist/ts
            uv run --directory transpiler python -m src.cli "$(pwd)/src/parable.py" -b ts > dist/ts/parable.ts
            ;;
        *)
            echo "Unknown backend: {{backend}}"
            exit 1
            ;;
    esac

# Verify dist/<backend>/ is up-to-date
verify backend="go":
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{backend}}" in
        go)
            just transpile go
            # transpile already writes to dist/go/parable.go, so just verify it compiles
            go build -C dist/go -o /dev/null .
            echo "[verify-go] OK"
            ;;
        *)
            echo "Verify not implemented for backend: {{backend}}"
            exit 1
            ;;
    esac

# Compile transpiled code
build backend="go":
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{backend}}" in
        go)
            go build -C dist/go -o /dev/null .
            ;;
        ts)
            tsc --outDir /tmp/transpile-ts --lib es2019 --module commonjs --esModuleInterop dist/ts/parable.ts
            ;;
        *)
            echo "Build not implemented for backend: {{backend}}"
            exit 1
            ;;
    esac

# Run tests on transpiled backend
test-backend backend:
    #!/usr/bin/env bash
    set -euo pipefail
    tests_abs="$(pwd)/tests"
    case "{{backend}}" in
        go)
            just transpile go
            go build -C dist/go -o /dev/null .
            go run -C dist/go ./cmd/run-tests "$tests_abs"
            ;;
        python)
            just transpile python
            PYTHONPATH=dist/python python3 tests/bin/run-tests.py
            ;;
        ts)
            just transpile ts
            just build ts
            node tests/bin/run-js-tests.js /tmp/transpile-ts
            ;;
        *)
            echo "No test runner for backend: {{backend}}"
            echo "Available backends: {{backends}}"
            exit 1
            ;;
    esac

# --- CI/Check ---

# Internal: run all parallel checks
[parallel]
_check-parallel: test lint fmt verify-lock check-dump-ast check-style (verify "go") (test-backend "go")

# Ensure biome is installed (prevents race condition in parallel JS checks)
_ensure-biome:
    @npx -y @biomejs/biome --version >/dev/null 2>&1

# Run all checks (parallel)
check: _ensure-biome _check-parallel

# Quick check: test base, transpile and test Go
quick-check: check-style test (test-backend "go")

# --- Tools ---

# Run the fuzzer (e.g., just fuzz char --stop-after 10)
fuzz *ARGS:
    FUZZER_ORIG_CWD="{{invocation_directory()}}" uv run --directory tools/fuzzer fuzzer {{ARGS}}

# Run the fuzzer agent
fuzzer-agent *ARGS:
    uv run --directory tools/fuzzer-agent fuzzer-agent {{ARGS}}

# Run Parable against the bigtable-bash corpus
run-corpus *ARGS:
    tests/bin/run-corpus.py {{ARGS}}

# Verify test expectations match bash-oracle
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
        exec tests/bin/verify-tests.py
    fi
    # Check dev location
    if [[ -x "$HOME/source/bash-oracle/bash-oracle" ]]; then
        check_binary "$HOME/source/bash-oracle/bash-oracle"
        BASH_ORACLE="$HOME/source/bash-oracle/bash-oracle" exec tests/bin/verify-tests.py
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
    BASH_ORACLE="$ORACLE_PATH" exec tests/bin/verify-tests.py

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

# --- Profiling ---

# Run coverage analysis on base test suite
coverage:
    #!/usr/bin/env bash
    set -euo pipefail
    uv run --with coverage coverage run tests/bin/run-tests.py
    uv run --with coverage coverage html -d /tmp/parable-coverage
    uv run --with coverage coverage json -o /tmp/parable-coverage.json
    echo ""
    echo "Output:"
    echo "  HTML: /tmp/parable-coverage/index.html"
    echo "  JSON: /tmp/parable-coverage.json"
    open /tmp/parable-coverage/index.html 2>/dev/null || true

# Run coverage analysis on backend test suite
coverage-backend backend:
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{backend}}" in
        go)
            rm -rf /tmp/parable-coverage-go-raw
            mkdir -p /tmp/parable-coverage-go-raw
            just transpile go
            GOCOVERDIR=/tmp/parable-coverage-go-raw go run -C dist/go -cover ./cmd/run-tests "$(pwd)/tests"
            go tool covdata textfmt -i=/tmp/parable-coverage-go-raw -o=/tmp/parable-coverage-go.txt
            cd dist/go && go tool cover -html=/tmp/parable-coverage-go.txt -o=/tmp/parable-coverage-go.html
            echo ""
            echo "Output:"
            echo "  HTML: /tmp/parable-coverage-go.html"
            echo "  Text: /tmp/parable-coverage-go.txt"
            open /tmp/parable-coverage-go.html 2>/dev/null || true
            ;;
        *)
            echo "Coverage not implemented for backend: {{backend}}"
            exit 1
            ;;
    esac

# Benchmark test suite
benchmark:
    hyperfine --warmup 2 --runs ${RUNS:-5} 'uv run tests/bin/run-tests.py 2>&1'
