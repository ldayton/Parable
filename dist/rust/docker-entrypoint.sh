#!/bin/bash
set -e

cmd="${1:-build}"
tests_dir="$2"

# Format parable.rs if it exists (transpiler outputs unformatted)
if [[ -f src/parable.rs ]]; then
    rustfmt src/parable.rs 2>/dev/null || true
fi

case "$cmd" in
    build)
        cargo build --release
        ;;
    check)
        if [[ -z "$tests_dir" ]]; then
            echo "Usage: docker run <image> check <tests_dir>" >&2
            exit 1
        fi
        cargo run --release --bin run_tests -- "$tests_dir"
        ;;
    *)
        echo "Unknown command: $cmd" >&2
        echo "Usage: docker run <image> [build|check <tests_dir>]" >&2
        exit 1
        ;;
esac
