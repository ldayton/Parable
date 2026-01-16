"""Shell tool for the fuzzer agent."""

import subprocess

from strands import tool


@tool
def shell(command: str, cwd: str | None = None) -> str:
    """Execute any shell command.

    Args:
        command: The shell command to execute.
        cwd: Working directory for the command. Defaults to current directory.

    Returns:
        Combined stdout and stderr from the command, or error message on failure.
    """
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
        return output or "[no output]"
    except subprocess.TimeoutExpired:
        return "[command timed out after 300 seconds]"
    except Exception as e:
        return f"[error: {e}]"
