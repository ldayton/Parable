# Fuzzer Agent

Strands SDK agent that autonomously finds and fixes fuzzer bugs.

```bash
uv run fuzzer-agent --model haiku-35
uv run fuzzer-agent --model sonnet-45
```

Exit codes: 0 (fixed + PR created), 1 (no bugs found), 2 (agent failed).

Requires AWS credentials for Bedrock.
