"""Shell tool for the fuzzer agent."""

import subprocess
from pathlib import Path

import structlog
from strands import tool

log = structlog.get_logger()
REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent


@tool
def shell(command: str, cwd: str | None = None) -> str:
    """Execute any shell command.

    Args:
        command: The shell command to execute.
        cwd: Working directory for the command. Defaults to Parable repo root.

    Returns:
        Combined stdout and stderr from the command, or error message on failure.
    """
    if cwd is None:
        cwd = str(REPO_ROOT)
    log.info("shell", command=command, cwd=cwd)
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,
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
