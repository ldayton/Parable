#!/bin/bash
set -e

cmd="${1:-build}"
tests_dir="$2"

case "$cmd" in
    build)
        npm install --silent 2>/dev/null || npm install
        npx tsc
        ;;
    check)
        if [[ -z "$tests_dir" ]]; then
            echo "Usage: docker run <image> check <tests_dir>" >&2
            exit 1
        fi
        npm install --silent 2>/dev/null || npm install
        npx tsc
        PARABLE_PATH="$(pwd)/dist" node "$tests_dir/bin/run-js-tests.js" "$(pwd)"
        ;;
    *)
        echo "Unknown command: $cmd" >&2
        echo "Usage: docker run <image> [build|check <tests_dir>]" >&2
        exit 1
        ;;
esac
