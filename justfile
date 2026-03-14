set shell := ["bash", "-o", "pipefail", "-cu"]

# --- Configuration ---
project := "parable"
run_id := `head -c 16 /dev/urandom | xxd -p`
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

# Verify lock file is up to date
[group: 'source']
src-verify-lock: (_banner "src-verify-lock")
    uv lock --check

# Verify Tongues is installed at required version
[group: 'source']
check-tongues: (_banner "check-tongues")
    #!/usr/bin/env bash
    set -euo pipefail
    required="0.2.1"
    if ! command -v tongues &>/dev/null; then
        echo "FAIL: tongues not found. Install with: brew install ldayton/tap/tongues"
        exit 1
    fi
    version=$(tongues --version)
    if [[ "$(printf '%s\n' "$required" "$version" | sort -V | head -1)" != "$required" ]]; then
        echo "FAIL: tongues $version < $required. Run: brew upgrade tongues"
        exit 1
    fi
    echo "OK (tongues $version)"

# Run Tongues pycheck on source
[group: 'source']
pycheck: check-tongues (_banner "pycheck")
    tongues --stop-at pycheck src/parable.py > /dev/null

# --- CI/Check ---

# Internal: run all parallel checks
[private]
[parallel]
_check-parallel: src-test src-lint src-fmt src-verify-lock check-dump-ast pycheck

# Run all checks (parallel)
[group: 'ci']
check: _check-parallel

# Quick check
[group: 'ci']
check-quick: src-test

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

# Benchmark source test suite
[group: 'profiling']
src-benchmark: (_banner "src-benchmark")
    hyperfine --warmup 2 --runs ${RUNS:-5} 'uv run parable-test tests 2>&1'
