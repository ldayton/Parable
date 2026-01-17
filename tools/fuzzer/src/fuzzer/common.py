"""Shared utilities for Parable fuzzers."""

import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from parable import ParseError, parse  # noqa: E402

_default_oracle = Path.home() / "source" / "bash-oracle" / "bash-oracle"
ORACLE_PATH = Path(os.environ.get("BASH_ORACLE") or _default_oracle)
if not ORACLE_PATH.exists():
    sys.exit(f"bash-oracle not found at {ORACLE_PATH}")


@dataclass
class Discrepancy:
    """A discrepancy between Parable and oracle results."""

    original: str
    mutated: str
    mutation_desc: str
    parable_result: str
    oracle_result: str

    def signature(self) -> str:
        """Return a signature for deduplication."""
        p = "err" if self.parable_result == "<error>" else "ok"
        o = "err" if self.oracle_result == "<error>" else "ok"
        return f"{p}:{o}:{self.mutated[:50]}"


def find_test_files(directory: Path) -> list[Path]:
    """Find all .tests files recursively."""
    return sorted(directory.rglob("*.tests"))


def parse_test_file(filepath: Path) -> list[str]:
    """Extract just the inputs from a .tests file."""
    inputs = []
    lines = filepath.read_text().split("\n")
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.startswith("=== "):
            i += 1
            input_lines = []
            while i < n and lines[i] != "---":
                input_lines.append(lines[i])
                i += 1
            if i < n and lines[i] == "---":
                i += 1
            while i < n and lines[i] != "---" and not lines[i].startswith("=== "):
                i += 1
            if i < n and lines[i] == "---":
                i += 1
            inputs.append("\n".join(input_lines))
        else:
            i += 1
    return inputs


def run_oracle(input_text: str) -> str | None:
    """Run bash-oracle on input. Returns s-expr or None on error/timeout."""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(input_text)
            tmp_path = Path(f.name)
        result = subprocess.run(
            [str(ORACLE_PATH), str(tmp_path)],
            capture_output=True,
            timeout=5,
        )
        if result.returncode != 0:
            return None
        return result.stdout.decode("utf-8", errors="replace").strip()
    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        return None
    finally:
        if tmp_path:
            tmp_path.unlink(missing_ok=True)


def run_parable(input_text: str) -> str | None:
    """Run Parable on input. Returns s-expr, None on parse error, or <crash:...>."""
    try:
        nodes = parse(input_text)
        return " ".join(node.to_sexp() for node in nodes)
    except ParseError:
        return None
    except Exception as e:
        return f"<crash: {type(e).__name__}: {e}>"


def normalize(s: str) -> str:
    """Normalize for comparison, ignoring cosmetic differences."""
    s = " ".join(s.split())
    s = re.sub(r"\b1>", ">", s)
    s = re.sub(r"\b1>&", ">&", s)
    s = re.sub(r"\\n\s+", r"\\n", s)
    return s


def post_process_discrepancies(
    discrepancies: list[Discrepancy],
    minimize: bool = False,
    filter_layer: int | None = None,
) -> list[Discrepancy]:
    """Minimize and/or filter discrepancies by layer."""
    from .generator import LAYERS, detect_layer
    from .minimize import minimize as minimize_fn

    # --filter-layer implies --minimize
    if filter_layer is not None:
        minimize = True

    if minimize and discrepancies:
        print("Minimizing discrepancies...")
        minimized = []
        for i, d in enumerate(discrepancies):
            result = minimize_fn(d.mutated)
            if result:
                d.mutated = result
                minimized.append(d)
            print(f"\r  {i + 1}/{len(discrepancies)}", end="", flush=True)
        print()
        discrepancies = minimized
        print(f"Minimized to {len(discrepancies)} discrepancies")

    if filter_layer is not None and discrepancies:
        print(f"Filtering to layer {filter_layer} ({LAYERS.get(filter_layer, '?')}) and below...")
        filtered = []
        for d in discrepancies:
            detected = detect_layer(d.mutated)
            if detected <= filter_layer:
                filtered.append(d)
        discrepancies = filtered
        print(f"Filtered to {len(discrepancies)} discrepancies")

    return discrepancies


def parse_layer_spec(spec: str) -> int:
    """Parse a layer spec like '5', 'words', 'commands' to an int."""
    from .generator import LAYER_PRESETS

    if spec in LAYER_PRESETS:
        return LAYER_PRESETS[spec]
    return int(spec)
