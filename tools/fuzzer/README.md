# Fuzzer

Differential fuzzers comparing Parable vs bash-oracle.

```bash
# Character mutation fuzzer
uv run fuzzer --character -n 5000
uv run fuzzer --character --stop-after 10
uv run fuzzer --character --both-succeed --stop-after 5

# Structural fuzzer (wraps inputs in $(), <(), etc.)
uv run fuzzer --structural --list-transforms
uv run fuzzer --structural --stop-after 10
uv run fuzzer --structural --transforms subshell,cmdsub

# Generator fuzzer (generates from scratch)
uv run fuzzer --generator -n 1000
uv run fuzzer --generator --stop-after 5 -v
```

Requires bash-oracle at `~/source/bash-oracle/bash-oracle`.
