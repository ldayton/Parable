#!/usr/bin/env python3
# /// script
# dependencies = ["google-cloud-bigquery"]
# ///
"""Fetch bash files from Google BigQuery's GitHub public dataset."""

import argparse
import sys
from pathlib import Path

from google.cloud import bigquery


def fetch_bash_files(
    client: bigquery.Client,
    limit: int,
    min_size: int,
    max_size: int,
    output_dir: Path,
) -> int:
    """Query BigQuery for bash files by extension and save them locally."""
    query = f"""
    SELECT
        f.repo_name,
        f.path,
        c.content
    FROM `bigquery-public-data.github_repos.files` f
    JOIN `bigquery-public-data.github_repos.contents` c
        ON f.id = c.id
    WHERE
        (f.path LIKE '%.sh' OR f.path LIKE '%.bash')
        AND c.binary = false
        AND c.size >= {min_size}
        AND c.size <= {max_size}
    LIMIT {limit}
    """
    print(f"Querying BigQuery for up to {limit} bash files...", file=sys.stderr)
    results = client.query(query).result()
    count = 0
    for row in results:
        repo_name = row.repo_name.replace("/", "__")
        filename = Path(row.path).name
        output_path = output_dir / f"{repo_name}__{filename}"
        output_path.write_text(row.content)
        count += 1
        if count % 100 == 0:
            print(f"  Saved {count} files...", file=sys.stderr)
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch bash files from GitHub via BigQuery")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Output directory")
    parser.add_argument("-n", "--limit", type=int, default=100, help="Max files to fetch")
    parser.add_argument("--min-size", type=int, default=3000, help="Minimum file size in bytes")
    parser.add_argument("--max-size", type=int, default=100000, help="Maximum file size in bytes")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    client = bigquery.Client()
    count = fetch_bash_files(client, args.limit, args.min_size, args.max_size, args.output)
    print(f"Saved {count} bash files to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
