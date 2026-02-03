#!/bin/bash
set -e

cmd="${1:-build}"
tests_dir="$2"

case "$cmd" in
    build)
        dart pub get --offline 2>/dev/null || dart pub get
        dart analyze lib/parable.dart
        ;;
    check)
        if [[ -z "$tests_dir" ]]; then
            echo "Usage: docker run <image> check <tests_dir>" >&2
            exit 1
        fi
        dart pub get --offline 2>/dev/null || dart pub get
        dart run bin/run_tests.dart "$tests_dir"
        ;;
    *)
        echo "Unknown command: $cmd" >&2
        echo "Usage: docker run <image> [build|check <tests_dir>]" >&2
        exit 1
        ;;
esac
