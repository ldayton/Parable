"""Fuzzer bug fixing agent using Strands."""

import io
import os
import subprocess
import time
from contextlib import redirect_stderr
from pathlib import Path

import structlog
from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.models import BedrockModel

from .tools import shell

# Pricing per 1M tokens (input, output)
MODEL_PRICING = {
    "haiku-3": (0.25, 1.25),
    "haiku-35": (0.80, 4.00),
    "haiku-45": (1.00, 5.00),
    "sonnet-35": (3.00, 15.00),
    "sonnet-37": (3.00, 15.00),
    "sonnet-4": (3.00, 15.00),
    "sonnet-45": (3.00, 15.00),
    "opus-4": (15.00, 75.00),
    "opus-41": (15.00, 75.00),
    "opus-45": (15.00, 75.00),
    "llama-33-70b": (0.99, 0.99),
    "llama-32-90b": (0.99, 0.99),
    "llama-31-70b": (0.99, 0.99),
    "nova-pro": (0.80, 3.20),
    "nova-premier": (2.50, 10.00),
}

MODELS = {
    "haiku-3": "anthropic.claude-3-haiku-20240307-v1:0",
    "haiku-35": "anthropic.claude-3-5-haiku-20241022-v1:0",
    "haiku-45": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "sonnet-3": "anthropic.claude-3-sonnet-20240229-v1:0",
    "sonnet-35": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "sonnet-4": "us.anthropic.claude-sonnet-4-20250514-v1:0",
    "sonnet-45": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "opus-4": "us.anthropic.claude-opus-4-20250514-v1:0",
    "opus-45": "us.anthropic.claude-opus-4-5-20251101-v1:0",
    "llama-33-70b": "meta.llama3-3-70b-instruct-v1:0",
    "llama-32-90b": "meta.llama3-2-90b-instruct-v1:0",
    "llama-31-70b": "meta.llama3-1-70b-instruct-v1:0",
    "nova-pro": "amazon.nova-pro-v1:0",
}

# Path to repo root (fuzzer-agent/src/fuzzer_agent -> repo root)
REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
PROMPTS_DIR = REPO_ROOT / "tools" / "fuzzer" / "prompts"


class FuzzerFixer:
    """Agent that finds and fixes fuzzer bugs in Parable."""

    def __init__(self, model: str = "sonnet-45"):
        self.log = structlog.get_logger()
        self.model_name = model
        self.model_id = MODELS[model]
        self.system_prompt = self._load_system_prompt()
        self.tools = [shell]

    def _load_system_prompt(self) -> str:
        base = (PROMPTS_DIR / "fuzzer-fix-base.md").read_text()
        local = (PROMPTS_DIR / "fuzzer-fix-local.md").read_text()
        mre_instruction = "\n\n**Important:** After finding an MRE, write it to `/tmp/mre.txt` (just the bash code, no explanation).\n"
        return f"{base}\n\n{local}{mre_instruction}"

    def _write_summary(self, content: str) -> None:
        """Append to GitHub Actions job summary if running in CI."""
        summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_file:
            try:
                with open(summary_file, "a") as f:
                    f.write(content)
            except Exception as e:
                self.log.warning("summary_write_failed", error=str(e))

    def _get_git_sha(self) -> str:
        """Get current git SHA."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                timeout=5,
            )
            return result.stdout.strip()[:7] if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in dollars based on model pricing."""
        pricing = MODEL_PRICING.get(self.model_name, (0, 0))
        input_cost = (input_tokens / 1_000_000) * pricing[0]
        output_cost = (output_tokens / 1_000_000) * pricing[1]
        return input_cost + output_cost

    def run(self) -> int:
        """Run the fuzzer fixing agent.

        Returns:
            0: Fixed a bug and created PR
            1: No bugs found (fuzzer found no discrepancies)
            2: Agent failed
        """
        base_sha = self._get_git_sha()
        self._write_summary(
            f"## Fuzzer Agent\n\n| | |\n|---|---|\n| **Model** | `{self.model_name}` |\n| **Base SHA** | `{base_sha}` |\n"
        )
        self.log.info("agent_start", model=self.model_name, base_sha=base_sha)
        model = BedrockModel(
            model_id=self.model_id,
            region_name="us-east-2",
            temperature=0.2,
            max_tokens=4096,
        )
        agent = Agent(
            model=model,
            system_prompt=self.system_prompt,
            tools=self.tools,
            conversation_manager=SlidingWindowConversationManager(
                window_size=40,
                should_truncate_results=False,
                per_turn=True,
            ),
        )
        prompt = "Find and fix one parser bug using the fuzzer."
        stderr_capture = io.StringIO()
        start_time = time.time()
        try:
            with redirect_stderr(stderr_capture):
                response = agent(prompt)
            duration = time.time() - start_time
            for line in stderr_capture.getvalue().splitlines():
                if line.strip():
                    self.log.warning("agent_stderr", message=line)
            output = str(response).lower() if response else ""
            # Extract metrics safely
            input_tokens = 0
            output_tokens = 0
            try:
                if response and response.metrics and response.metrics.accumulated_usage:
                    input_tokens = response.metrics.accumulated_usage.get("inputTokens", 0)
                    output_tokens = response.metrics.accumulated_usage.get("outputTokens", 0)
            except Exception:
                pass
            cost = self._calculate_cost(input_tokens, output_tokens)
            final_sha = self._get_git_sha()
            # Read MRE if written
            mre = ""
            mre_path = Path("/tmp/mre.txt")
            try:
                if mre_path.exists():
                    mre = mre_path.read_text().strip()
            except Exception:
                pass
            # Write final summary
            summary = f"| **Final SHA** | `{final_sha}` |\n"
            summary += f"| **Tokens** | {input_tokens:,} in / {output_tokens:,} out |\n"
            summary += f"| **Cost** | ${cost:.4f} |\n"
            summary += f"| **Duration** | {duration:.1f}s |\n"
            if mre:
                summary += f"\n### MRE\n```bash\n{mre}\n```\n"
            self._write_summary(summary)
            self.log.info(
                "agent_complete",
                duration=round(duration, 2),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=round(cost, 4),
            )
            # Determine exit code based on agent output
            if "no discrepancies" in output or "no bugs found" in output:
                return 1
            if "gh pr create" in str(response) or "created" in output:
                return 0
            return 2
        except Exception as e:
            self.log.error("agent_failed", error=str(e))
            error_msg = str(e).replace("`", "'")  # Escape backticks for markdown
            self._write_summary(f"\n### Error\n```\n{error_msg}\n```\n")
            return 2
