set shell := ["bash", "-o", "pipefail", "-cu"]

# --- Configuration ---
project := "parable"
run_id := `head -c 16 /dev/urandom | xxd -p`
backends := "csharp dart go java javascript lua perl php python ruby typescript"

# --- Helpers ---

[private]
_banner label:
    @printf '{{BOLD}}{{CYAN}}==> %s{{NORMAL}}\n' '{{label}}'

# --- Source (src/parable.py) ---

# Run parser tests against source
[group: 'source']
src-test *ARGS: (_banner "src-test")
    uv run parable-test {{ARGS}} tests

# Lint (--fix to apply changes)
[group: 'source']
src-lint *ARGS: (_banner "src-lint")
    uvx ruff check {{ if ARGS == "--fix" { "--fix" } else { "" } }} src/

# Format (--fix to apply changes)
[group: 'source']
src-fmt *ARGS: (_banner "src-fmt")
    uvx ruff format {{ if ARGS == "--fix" { "" } else { "--check" } }} src/

# Verify source is subset-compliant
[group: 'source']
src-subset: (_banner "src-subset")
    uv run --directory transpiler python -m src.tongues --verify < src/parable.py

# Verify transpiler is subset-compliant (self-hosting)
[group: 'transpiler']
transpiler-subset: (_banner "transpiler-subset")
    just -f transpiler/justfile style

# Run transpiler tests
[group: 'transpiler']
transpiler-test: (_banner "transpiler-test")
    just -f transpiler/justfile test-transpiler

# Verify lock file is up to date
[group: 'source']
src-verify-lock: (_banner "src-verify-lock")
    uv lock --check

# --- Backends (transpiled output in dist/) ---

# Transpile via Docker
[group: 'backends']
backend-transpile backend: (_banner "backend-transpile " + backend)
    just -f dist/{{backend}}/justfile transpile "$(pwd)/src/parable.py" "$(pwd)/transpiler"

# Run tests via Docker
[group: 'backends']
backend-test backend: (_banner "backend-test " + backend)
    just -f dist/{{backend}}/justfile check "$(pwd)/src/parable.py" "$(pwd)/transpiler" "$(pwd)/tests"

# --- CI/Check ---

# Check that C backend compiles (without running tests)
[group: 'ci']
c-compile:
    just backend-transpile c
    just -f dist/c/justfile build

# Internal: run all parallel checks
[private]
[parallel]
_check-parallel: src-test src-lint src-fmt src-verify-lock src-subset transpiler-subset transpiler-test check-dump-ast _backend-test-all

# Internal: run backend tests in parallel
[private]
_backend-test-all:
    #!/usr/bin/env bash
    set -e
    pids=()
    for backend in {{backends}}; do
        just backend-test "$backend" &
        pids+=($!)
    done
    failed=0
    for pid in "${pids[@]}"; do
        wait "$pid" || failed=1
    done
    exit $failed

# Ensure biome is installed (prevents race condition in parallel JS checks)
[private]
_ensure-biome:
    @npx -y @biomejs/biome --version >/dev/null 2>&1

# Run all checks (parallel)
[group: 'ci']
check: _ensure-biome _check-parallel

# Quick check: test source, transpile and test Go
[group: 'ci']
check-quick: src-subset transpiler-subset src-test (backend-test "go")

# --- Tools ---

# Run the fuzzer (e.g., just fuzz char --stop-after 10)
[group: 'tools']
fuzz *ARGS:
    FUZZER_ORIG_CWD="{{invocation_directory()}}" uv run --directory tools/fuzzer fuzzer {{ARGS}}

# Run the fuzzer agent
[group: 'tools']
fuzzer-agent *ARGS:
    uv run --directory tools/fuzzer-agent fuzzer-agent {{ARGS}}

# Run source against the bigtable-bash corpus
[group: 'tools']
src-run-corpus *ARGS:
    uv run tests/bin/run-corpus.py {{ARGS}}

# Verify test expectations match bash-oracle
[group: 'ci']
check-tests: (_banner "check-tests")
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
[group: 'ci']
check-dump-ast: (_banner "check-dump-ast")
    @output=$(uv run bin/parable-dump.py 'echo hello') && \
    expected='(command (word "echo") (word "hello"))' && \
    if [ "$output" = "$expected" ]; then \
        echo "OK"; \
    else \
        echo "FAIL: expected '$expected', got '$output'" >&2; \
        exit 1; \
    fi

# --- Profiling ---

# Run coverage analysis on source test suite
[group: 'profiling']
src-coverage: (_banner "src-coverage")
    #!/usr/bin/env bash
    set -euo pipefail
    uv run --with coverage coverage run -m run_tests tests
    uv run --with coverage coverage html -d /tmp/parable-coverage
    uv run --with coverage coverage json -o /tmp/parable-coverage.json
    echo ""
    echo "Output:"
    echo "  HTML: /tmp/parable-coverage/index.html"
    echo "  JSON: /tmp/parable-coverage.json"
    open /tmp/parable-coverage/index.html 2>/dev/null || true

# Run coverage analysis on backend test suite
[group: 'profiling']
backend-coverage backend:
    #!/usr/bin/env bash
    set -euo pipefail
    printf '{{BOLD}}{{CYAN}}==> backend-coverage %s{{NORMAL}}\n' '{{backend}}'
    case "{{backend}}" in
        go)
            rm -rf /tmp/parable-coverage-go-raw
            mkdir -p /tmp/parable-coverage-go-raw
            just -f dist/go/justfile transpile "$(pwd)/src/parable.py" "$(pwd)/transpiler"
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

# Benchmark source test suite
[group: 'profiling']
src-benchmark: (_banner "src-benchmark")
    hyperfine --warmup 2 --runs ${RUNS:-5} 'uv run parable-test tests 2>&1'
