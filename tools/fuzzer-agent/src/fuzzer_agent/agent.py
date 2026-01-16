"""Fuzzer bug fixing agent using Strands."""

import io
import time
from contextlib import redirect_stderr
from pathlib import Path

import structlog
from strands import Agent
from strands.models import BedrockModel

from .tools import shell

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
        return f"{base}\n\n{local}"

    def run(self) -> int:
        """Run the fuzzer fixing agent.

        Returns:
            0: Fixed a bug and created PR
            1: No bugs found (fuzzer found no discrepancies)
            2: Agent failed
        """
        model = BedrockModel(model_id=self.model_id, region_name="us-east-2")
        agent = Agent(
            model=model,
            system_prompt=self.system_prompt,
            tools=self.tools,
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
            output = str(response).lower()
            self.log.info("agent_complete", duration=round(duration, 2))
            # Determine exit code based on agent output
            if "no discrepancies" in output or "no bugs found" in output:
                return 1
            if "gh pr create" in str(response) or "created" in output:
                return 0
            return 2
        except Exception as e:
            self.log.error("agent_failed", error=str(e))
            return 2
