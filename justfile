set shell := ["bash", "-o", "pipefail", "-cu"]

# --- Configuration ---
project := "parable"
run_id := `head -c 16 /dev/urandom | xxd -p`
backends := "c csharp go java javascript lua perl php python ruby typescript"  # All backends

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

# Transpile base to dist/<backend>/
[group: 'backends']
backend-transpile backend:
    #!/usr/bin/env bash
    set -euo pipefail
    printf '{{BOLD}}{{CYAN}}==> backend-transpile %s{{NORMAL}}\n' '{{backend}}'
    case "{{backend}}" in
        c)
            mkdir -p dist/c
            uv run --directory transpiler python -m src.tongues --target c < "$(pwd)/src/parable.py" > dist/c/parable.c
            ;;
        csharp)
            just -f dist/csharp/justfile transpile "$(pwd)/src/parable.py" "$(pwd)/transpiler"
            ;;
        go)
            just -f dist/go/justfile transpile "$(pwd)/src/parable.py" "$(pwd)/transpiler"
            ;;
        java)
            dist/java/gradlew -p dist/java transpile --quiet -PsourceFile="$(pwd)/src/parable.py" -PtranspilerDir="$(pwd)/transpiler"
            ;;
        javascript)
            SOURCE_FILE="$(pwd)/src/parable.py" TRANSPILER_DIR="$(pwd)/transpiler" npm --prefix dist/javascript run transpile
            ;;
        lua)
            SOURCE_FILE="$(pwd)/src/parable.py" TRANSPILER_DIR="$(pwd)/transpiler" make -C dist/lua transpile
            ;;
        perl)
            SOURCE_FILE="$(pwd)/src/parable.py" TRANSPILER_DIR="$(pwd)/transpiler" make -C dist/perl transpile
            ;;
        php)
            SOURCE_FILE="$(pwd)/src/parable.py" TRANSPILER_DIR="$(pwd)/transpiler" composer --working-dir=dist/php run transpile
            ;;
        python)
            SOURCE_FILE="$(pwd)/src/parable.py" TRANSPILER_DIR="$(pwd)/transpiler" make -C dist/python transpile
            ;;
        ruby)
            SOURCE_FILE="$(pwd)/src/parable.py" TRANSPILER_DIR="$(pwd)/transpiler" rake -C dist/ruby transpile
            ;;
        typescript)
            SOURCE_FILE="$(pwd)/src/parable.py" TRANSPILER_DIR="$(pwd)/transpiler" npm --prefix dist/typescript run transpile
            ;;
        *)
            echo "Unknown backend: {{backend}}"
            exit 1
            ;;
    esac

# Run tests on transpiled backend
[group: 'backends']
backend-test backend:
    #!/usr/bin/env bash
    set -euo pipefail
    printf '{{BOLD}}{{CYAN}}==> backend-test %s{{NORMAL}}\n' '{{backend}}'
    tests_abs="$(pwd)/tests"
    case "{{backend}}" in
        c)
            just backend-transpile c
            just -f dist/c/justfile check "$tests_abs"
            ;;
        csharp)
            just -f dist/csharp/justfile check "$(pwd)/src/parable.py" "$(pwd)/transpiler" "$tests_abs"
            ;;
        go)
            just -f dist/go/justfile check "$(pwd)/src/parable.py" "$(pwd)/transpiler" "$tests_abs"
            ;;
        java)
            dist/java/gradlew -p dist/java run --quiet -PsourceFile="$(pwd)/src/parable.py" -PtranspilerDir="$(pwd)/transpiler" --args="$tests_abs"
            ;;
        javascript)
            SOURCE_FILE="$(pwd)/src/parable.py" TRANSPILER_DIR="$(pwd)/transpiler" npm --prefix dist/javascript run transpile
            TESTS_DIR="$tests_abs" npm --prefix dist/javascript run check
            ;;
        lua)
            SOURCE_FILE="$(pwd)/src/parable.py" TRANSPILER_DIR="$(pwd)/transpiler" make -C dist/lua transpile
            TESTS_DIR="$tests_abs" make -C dist/lua check
            ;;
        perl)
            SOURCE_FILE="$(pwd)/src/parable.py" TRANSPILER_DIR="$(pwd)/transpiler" make -C dist/perl transpile
            TESTS_DIR="$tests_abs" make -C dist/perl check
            ;;
        php)
            SOURCE_FILE="$(pwd)/src/parable.py" TRANSPILER_DIR="$(pwd)/transpiler" composer --working-dir=dist/php run transpile
            TESTS_DIR="$tests_abs" composer --working-dir=dist/php run check
            ;;
        python)
            SOURCE_FILE="$(pwd)/src/parable.py" TRANSPILER_DIR="$(pwd)/transpiler" make -C dist/python transpile
            TESTS_DIR="$tests_abs" make -C dist/python check
            ;;
        ruby)
            SOURCE_FILE="$(pwd)/src/parable.py" TRANSPILER_DIR="$(pwd)/transpiler" rake -C dist/ruby transpile
            TESTS_DIR="$tests_abs" rake -C dist/ruby check
            ;;
        typescript)
            SOURCE_FILE="$(pwd)/src/parable.py" TRANSPILER_DIR="$(pwd)/transpiler" npm --prefix dist/typescript run transpile
            npm --prefix dist/typescript run build
            TESTS_DIR="$tests_abs" npm --prefix dist/typescript run check
            ;;
        *)
            echo "No test runner for backend: {{backend}}"
            echo "Available backends: {{backends}}"
            exit 1
            ;;
    esac

# --- CI/Check ---

# Check that C backend compiles (without running tests)
[group: 'ci']
c-compile:
    just backend-transpile c
    just -f dist/c/justfile build

# Internal: run all parallel checks
[private]
[parallel]
_check-parallel: src-test src-lint src-fmt src-verify-lock src-subset transpiler-subset transpiler-test check-dump-ast (backend-test "csharp") (backend-test "go") (backend-test "java") (backend-test "javascript") (backend-test "lua") (backend-test "perl") (backend-test "php") (backend-test "python") (backend-test "ruby") (backend-test "typescript")

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
