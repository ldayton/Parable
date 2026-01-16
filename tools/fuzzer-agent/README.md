# Fuzzer Agent

Strands SDK agent that autonomously finds and fixes fuzzer bugs.

```
usage: fuzzer-agent [-h] [--model MODEL] [--prices]

Autonomous fuzzer bug fixing agent

options:
  -h, --help     show this help message and exit
  --model MODEL  Model to use (default: sonnet-4.5)
  --prices       Fetch live pricing from AWS and exit

exit codes: 0 (fixed + PR), 1 (no bugs), 2 (failed)
```