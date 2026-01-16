"""Shell tool for the fuzzer agent."""

import os
import subprocess
from pathlib import Path

import structlog
from strands import tool

log = structlog.get_logger()
REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent

# Clean environment for subprocesses (avoid uv venv mismatch warnings)
_CLEAN_ENV = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}


@tool
def shell(command: str) -> str:
    """Execute a shell command in the Parable repo root.

    Args:
        command: The shell command to execute.

    Returns:
        Combined stdout and stderr from the command, or error message on failure.
    """
    cwd = str(REPO_ROOT)
    log.info("shell", command=command)
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,
            env=_CLEAN_ENV,
        )
        output = result.stdout + result.stderr
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
        output = output or "[no output]"
        # Log truncated output
        preview = output[:500] + "..." if len(output) > 500 else output
        log.info("shell_result", exit_code=result.returncode, output=preview)
        return output
    except subprocess.TimeoutExpired:
        log.error("shell_timeout", command=command)
        return "[command timed out after 300 seconds]"
    except Exception as e:
        log.error("shell_error", command=command, error=str(e))
        return f"[error: {e}]"
