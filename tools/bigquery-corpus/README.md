# BigQuery Corpus

Fetch bash files from Google's BigQuery GitHub public dataset (`bigquery-public-data.github_repos`).

## Setup

```bash
pip install google-cloud-bigquery
gcloud auth application-default login
```

## Usage

```bash
# Fetch 1000 bash files (by extension and shebang)
./fetch-bash.py -o ./corpus -n 1000

# Only files with .sh/.bash extension
./fetch-bash.py -o ./corpus --mode extension

# Only files with #!/bin/bash or #!/usr/bin/env bash shebang
./fetch-bash.py -o ./corpus --mode shebang

# Filter by size
./fetch-bash.py -o ./corpus --min-size 500 --max-size 10000
```

## BigQuery Costs

The `github_repos` dataset is public but queries consume your BigQuery quota. The `contents` table is ~3TB, so full scans can be expensive. The queries use `LIMIT` to cap results.
