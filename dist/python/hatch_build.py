"""Hatch build hook to transpile parable.py to Python."""

import os
import subprocess
import sys
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class TranspileHook(BuildHookInterface):
    PLUGIN_NAME = "transpile"

    def initialize(self, version, build_data):
        source_file = os.environ.get("PARABLE_SOURCE_FILE")
        transpiler_dir = os.environ.get("PARABLE_TRANSPILER_DIR")

        if not source_file:
            raise RuntimeError(
                "PARABLE_SOURCE_FILE environment variable is required"
            )
        if not transpiler_dir:
            raise RuntimeError(
                "PARABLE_TRANSPILER_DIR environment variable is required"
            )

        source_path = Path(source_file)
        if not source_path.exists():
            raise RuntimeError(f"Source file not found: {source_file}")

        output_path = Path(self.root) / "src" / "parable" / "parable.py"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(source_path) as f:
            source_content = f.read()

        result = subprocess.run(
            ["uv", "run", "--directory", transpiler_dir, "python", "-m", "src.tongues", "--target", "python"],
            input=source_content,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Transpiler failed: {result.stderr}")

        output_path.write_text(result.stdout)
