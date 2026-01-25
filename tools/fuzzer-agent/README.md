# Fuzzer Agent

Autonomous agent that finds and fixes fuzzer bugs. Supports Strands SDK or Claude Agent SDK.

```
usage: fuzzer-agent [-h] [--model MODEL] [--prices]

Autonomous fuzzer bug fixing agent

options:
  -h, --help     show this help message and exit
  --model MODEL  Model to use (default: sonnet-4.5)
  --prices       Fetch live pricing from AWS and exit

exit codes: 0 (fixed + PR), 1 (no bugs), 2 (failed)
```