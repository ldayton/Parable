#!/bin/bash
set -e

cmd="${1:-build}"
tests_dir="$2"

# Format parable.go if it exists (transpiler outputs unformatted)
if [[ -f parable.go ]]; then
    gofmt -w parable.go
fi

case "$cmd" in
    build)
        go build -o /dev/null .
        ;;
    check)
        if [[ -z "$tests_dir" ]]; then
            echo "Usage: docker run <image> check <tests_dir>" >&2
            exit 1
        fi
        go run ./cmd/run-tests "$tests_dir"
        ;;
    *)
        echo "Unknown command: $cmd" >&2
        echo "Usage: docker run <image> [build|check <tests_dir>]" >&2
        exit 1
        ;;
esac
