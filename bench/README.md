# Benchmarks

Parser benchmarks against the GNU Bash test corpus.

## Setup

```bash
npm install  # from this directory
```

## Usage

```bash
just bench           # Python benchmarks
just bench-js        # JavaScript benchmarks
just bench HEAD      # Compare Python: HEAD vs working tree
just bench-js HEAD   # Compare JavaScript: HEAD vs working tree
just bench a1b2c3 d4e5f6 --fast  # Compare two refs, quick mode
```

## Tools

- **Python**: Uses [pyperf](https://pyperf.readthedocs.io/) for statistical rigor
- **JavaScript**: Uses [tinybench](https://github.com/tinylibs/tinybench) for parity
