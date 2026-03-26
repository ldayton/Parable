set shell := ["bash", "-o", "pipefail", "-cu"]

export VIRTUAL_ENV := ""

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
    required="0.2.5"
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
_check-parallel: src-test src-lint src-fmt src-verify-lock check-dump-ast pycheck (lang "javascript") (lang "python")

# Run all checks (parallel)
[group: 'ci']
check: _check-parallel

# Quick check
[group: 'ci']
check-quick: src-test

# --- Transpiled backends ---

# SHA256 of source file (truncated to 16 chars)
[private]
_src-checksum:
    @cat src/parable.py | { sha256sum 2>/dev/null || shasum -a 256; } | cut -c1-16

# Transpile source to target language (skips if unchanged)
[private]
_transpile target:
    #!/usr/bin/env bash
    set -euo pipefail
    declare -A ext=([python]=py [ruby]=rb [perl]=pl [javascript]=js [java]=java)
    e=${ext[{{target}}]}
    out=".out/parable.$e"
    sum_file=".out/.sum-{{target}}"
    current=$(just -f {{justfile()}} _src-checksum)
    cached=$(cat "$sum_file" 2>/dev/null || echo "")
    if [ -f "$out" ] && [ "$current" = "$cached" ]; then
        printf '\033[33m[transpile-{{target}}] up to date\033[0m\n'
        exit 0
    fi
    rm -f "$sum_file"
    printf '\033[32m[transpile-{{target}}]\033[0m\n'
    start=$SECONDS
    mkdir -p .out
    tongues --target {{target}} -o "$out" src/parable.py
    case "{{target}}" in
        javascript) echo 'module.exports = { parse, ParseError, MatchedPairError };' >> "$out" ;;
        perl)       echo '1;' >> "$out" ;;
    esac
    printf '\033[32m[transpile-{{target}}] %ds\033[0m\n' "$((SECONDS - start))"
    echo "$current" > "$sum_file"

# Run transpiled tests for a target language
[private]
_run-lang-tests target:
    #!/usr/bin/env bash
    set -euo pipefail
    printf '\033[32m[lang-{{target}}]\033[0m\n'
    start=$SECONDS
    case "{{target}}" in
        javascript)
            PARABLE_PATH="$(pwd)/.out" node tests/transpiled/javascript/run-tests.js tests
            ;;
        python)
            PYTHONPATH=.out uv run python tests/transpiled/python/run_tests.py tests
            ;;
        java)
            mkdir -p .out/java-classes
            cp .out/parable.java .out/java-classes/Main.java
            javac -encoding UTF-8 .out/java-classes/Main.java -d .out/java-classes
            javac -encoding UTF-8 -cp .out/java-classes tests/transpiled/java/RunTests.java -d .out/java-classes
            java -cp .out/java-classes RunTests tests
            ;;
        perl)
            perl -I.out tests/transpiled/perl/run_tests.pl tests
            ;;
        ruby)
            ruby -I.out tests/transpiled/ruby/run_tests.rb tests
            ;;
        *)
            echo "Unknown target: {{target}}"
            exit 1
            ;;
    esac
    printf '\033[32m[lang-{{target}}] %ds\033[0m\n' "$((SECONDS - start))"

# Transpile and run tests in target language
# Usage: just lang javascript
[group: 'backends']
lang target: check-tongues (_transpile target) (_run-lang-tests target)

# Transpile using local Tongues dev source and run tests
# Usage: just lang-dev javascript
[group: 'backends']
lang-dev target: (_transpile-dev target) (_run-lang-tests target)

# Transpile using local Tongues source (no caching)
[private]
_transpile-dev target:
    #!/usr/bin/env bash
    set -euo pipefail
    declare -A ext=([python]=py [ruby]=rb [perl]=pl [javascript]=js [java]=java)
    e=${ext[{{target}}]}
    out=".out/parable.$e"
    mkdir -p .out
    printf '\033[32m[transpile-{{target}} (dev)]\033[0m\n'
    start=$SECONDS
    python3 ~/source/Tongues/tongues/bin/tongues --target {{target}} -o "$out" src/parable.py
    case "{{target}}" in
        javascript) echo 'module.exports = { parse, ParseError, MatchedPairError };' >> "$out" ;;
        perl)       echo '1;' >> "$out" ;;
    esac
    printf '\033[32m[transpile-{{target}} (dev)] %ds\033[0m\n' "$((SECONDS - start))"

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
