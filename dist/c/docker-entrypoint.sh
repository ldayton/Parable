#!/bin/bash
set -e

cmd="${1:-build}"
tests_dir="$2"

case "$cmd" in
    build)
        gcc -Wall -Wextra -fsyntax-only -std=c11 parable.c
        ;;
    check)
        if [[ -z "$tests_dir" ]]; then
            echo "Usage: docker run <image> check <tests_dir>" >&2
            exit 1
        fi
        gcc -Wall -Wextra -O2 -std=c11 -o run_tests run_tests.c
        ./run_tests "$tests_dir"
        ;;
    *)
        echo "Unknown command: $cmd" >&2
        echo "Usage: docker run <image> [build|check <tests_dir>]" >&2
        exit 1
        ;;
esac
