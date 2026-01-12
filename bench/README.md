# Benchmarks

Parser benchmarks against the GNU Bash test corpus (19,370 lines).

## Setup

```bash
cd bench && npm install
```

## Usage

```bash
just bench              # Run Python benchmark
just bench-js           # Run JavaScript benchmark
```

### Comparing versions

```bash
just bench HEAD         # Compare HEAD vs working tree
just bench HEAD~5       # Compare HEAD~5 vs working tree
just bench abc123 def456  # Compare two commits
```

### Options

- `--fast` — Fewer iterations for quick checks

```bash
just bench HEAD --fast
just bench-js HEAD --fast
```

## Output

Results are saved to `.pyperf/` with timestamps:

```
.pyperf/2026-01-12_162626_5c4e312_vs_current/
├── 1_5c4e312.json
└── 2_current.json
```

## Tools

|         | Python                                   | JavaScript                                         |
| ------- | ---------------------------------------- | -------------------------------------------------- |
| Library | [pyperf](https://pyperf.readthedocs.io/) | [tinybench](https://github.com/tinylibs/tinybench) |
| Warmup  | Calibrated                               | 5 runs                                             |
| Samples | 20                                       | 20                                                 |
| Stats   | Mean, stddev, outlier detection          | Mean, stddev                                       |
