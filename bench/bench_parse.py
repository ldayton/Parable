#!/usr/bin/env python3
"""Microbenchmarks for Parable parser."""

import pyperf

from parable import parse

# Simple commands
SIMPLE = "ls -la"
SIMPLE_ARGS = "git log --oneline -n 10 --format='%h %s'"

# Pipelines
PIPELINE_SHORT = "ps aux | grep python"
PIPELINE_LONG = "ps aux | grep python | awk '{print $2}' | head -10 | xargs kill"

# Command lists
LIST_AND = "cd /tmp && mkdir test && cd test"
LIST_MIXED = "make build && make test || echo 'failed'"

# Redirects
REDIRECT_SIMPLE = "ls > out.txt"
REDIRECT_COMPLEX = "cmd 2>&1 | tee log.txt"

# Substitutions
CMDSUB_SIMPLE = "echo $(pwd)"
CMDSUB_NESTED = "echo $(cat $(find . -name '*.py' | head -1))"

# Here documents
HEREDOC = """cat <<EOF
line 1
line 2
line 3
EOF"""

# Quoting
QUOTES_MIXED = """echo "hello $USER" 'literal $USER' $'tab\there'"""

# Complex real-world
COMPLEX_AWS = "aws ec2 describe-instances --filters 'Name=tag:Environment,Values=prod' --query 'Reservations[].Instances[].InstanceId' --output text"
COMPLEX_DOCKER = "docker run -it --rm -v $(pwd):/app -e NODE_ENV=production node:18 npm run build"
COMPLEX_FIND = "find . -type f -name '*.py' -exec grep -l 'TODO' {} \\;"


def main():
    runner = pyperf.Runner()

    # Simple
    runner.bench_func("simple", parse, SIMPLE)
    runner.bench_func("simple_args", parse, SIMPLE_ARGS)

    # Pipelines
    runner.bench_func("pipeline_short", parse, PIPELINE_SHORT)
    runner.bench_func("pipeline_long", parse, PIPELINE_LONG)

    # Command lists
    runner.bench_func("list_and", parse, LIST_AND)
    runner.bench_func("list_mixed", parse, LIST_MIXED)

    # Redirects
    runner.bench_func("redirect_simple", parse, REDIRECT_SIMPLE)
    runner.bench_func("redirect_complex", parse, REDIRECT_COMPLEX)

    # Substitutions
    runner.bench_func("cmdsub_simple", parse, CMDSUB_SIMPLE)
    runner.bench_func("cmdsub_nested", parse, CMDSUB_NESTED)

    # Here documents
    runner.bench_func("heredoc", parse, HEREDOC)

    # Quoting
    runner.bench_func("quotes_mixed", parse, QUOTES_MIXED)

    # Complex real-world
    runner.bench_func("complex_aws", parse, COMPLEX_AWS)
    runner.bench_func("complex_docker", parse, COMPLEX_DOCKER)
    runner.bench_func("complex_find", parse, COMPLEX_FIND)


if __name__ == "__main__":
    main()
