#!/bin/bash
set -e

cmd="${1:-build}"
tests_dir="$2"

case "$cmd" in
    build)
        luac -p parable.lua
        ;;
    check)
        if [[ -z "$tests_dir" ]]; then
            echo "Usage: docker run <image> check <tests_dir>" >&2
            exit 1
        fi
        luac -p parable.lua
        lua -l parable "$tests_dir/bin/run-tests.lua" "$tests_dir"
        ;;
    *)
        echo "Unknown command: $cmd" >&2
        echo "Usage: docker run <image> [build|check <tests_dir>]" >&2
        exit 1
        ;;
esac
