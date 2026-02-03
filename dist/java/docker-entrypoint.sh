#!/bin/bash
set -e

cmd="${1:-build}"
tests_dir="$2"

case "$cmd" in
    build)
        mkdir -p build/classes
        javac -d build/classes src/main/java/parable/*.java
        ;;
    check)
        if [[ -z "$tests_dir" ]]; then
            echo "Usage: docker run <image> check <tests_dir>" >&2
            exit 1
        fi
        mkdir -p build/classes
        javac -d build/classes src/main/java/parable/*.java
        java -cp build/classes parable.RunTests "$tests_dir"
        ;;
    *)
        echo "Unknown command: $cmd" >&2
        echo "Usage: docker run <image> [build|check <tests_dir>]" >&2
        exit 1
        ;;
esac
