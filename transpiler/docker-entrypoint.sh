#!/bin/bash
set -e

target="$1"
source_file="$2"
output_file="$3"

if [[ -z "$target" || -z "$source_file" || -z "$output_file" ]]; then
    echo "Usage: docker run <image> <target> <source_file> <output_file>" >&2
    echo "  target: c, csharp, go, java, javascript, lua, perl, php, python, ruby, typescript, zig, etc." >&2
    exit 1
fi

# Java needs package declaration prepended
if [[ "$target" == "java" ]]; then
    echo "package parable;" > "$output_file"
    echo "" >> "$output_file"
    uv run python -m src.tongues --target "$target" < "$source_file" >> "$output_file"
else
    uv run python -m src.tongues --target "$target" < "$source_file" > "$output_file"
fi
