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
from strands.models.litellm import LiteLLMModel

from .pricing import AZURE_PRICING, CLAUDE_PRICING, GCP_PRICING, OTHER_PRICING
from .tools import shell

MODEL_PRICING = {**CLAUDE_PRICING, **OTHER_PRICING, **AZURE_PRICING, **GCP_PRICING}

# Bedrock model IDs
BEDROCK_MODELS = {
    "deepseek-r1": "us.deepseek.r1-v1:0",
    "deepseek-v3.1": "us.deepseek.deepseek-v3-1-v1:0",
    "haiku-3": "anthropic.claude-3-haiku-20240307-v1:0",
    "haiku-3.5": "anthropic.claude-3-5-haiku-20241022-v1:0",
    "haiku-4.5": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "sonnet-3": "anthropic.claude-3-sonnet-20240229-v1:0",
    "sonnet-3.5": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "sonnet-4": "us.anthropic.claude-sonnet-4-20250514-v1:0",
    "sonnet-4.5": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "opus-4": "us.anthropic.claude-opus-4-20250514-v1:0",
    "opus-4.5": "us.anthropic.claude-opus-4-5-20251101-v1:0",
    "llama-3.3-70b": "meta.llama3-3-70b-instruct-v1:0",
    "llama-3.2-90b": "meta.llama3-2-90b-instruct-v1:0",
    "llama-3.1-70b": "meta.llama3-1-70b-instruct-v1:0",
    "nova-pro": "amazon.nova-pro-v1:0",
}

# Azure OpenAI model IDs (deployment names, configure via AZURE_API_BASE)
AZURE_MODELS = {
    "gpt-4.5": "azure/gpt-4.5",
    "gpt-4.1": "azure/gpt-4.1",
    "gpt-4.1-mini": "azure/gpt-4.1-mini",
    "gpt-4.1-nano": "azure/gpt-4.1-nano",
    "gpt-4o": "azure/gpt-4o",
    "gpt-4o-mini": "azure/gpt-4o-mini",
    "gpt-5": "azure/gpt-5",
    "gpt-5.1": "azure/gpt-5.1",
    "gpt-5.2": "azure/gpt-5.2",
}

# GCP Vertex AI model IDs
GCP_MODELS = {
    "gemini-2.0-flash": "vertex_ai/gemini-2.0-flash",
    "gemini-2.5-flash": "vertex_ai/gemini-2.5-flash",
    "gemini-2.5-pro": "vertex_ai/gemini-2.5-pro",
    "gemini-3-flash": "vertex_ai/gemini-3-flash-preview",
    "gemini-3-pro": "vertex_ai/gemini-3-pro-preview",
}

MODELS = {**BEDROCK_MODELS, **AZURE_MODELS, **GCP_MODELS}

# Path to repo root (fuzzer-agent/src/fuzzer_agent -> repo root)
REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
PROMPTS_DIR = REPO_ROOT / "tools" / "fuzzer" / "prompts"


class FuzzerFixer:
    """Agent that finds and fixes fuzzer bugs in Parable."""

    def __init__(self, model: str = "sonnet-4.5"):
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
        if self.model_name in AZURE_MODELS:
            from azure.identity import DefaultAzureCredential

            credential = DefaultAzureCredential()
            token = credential.get_token("https://cognitiveservices.azure.com/.default")
            model = LiteLLMModel(
                model_id=self.model_id,
                params={"temperature": 0.2, "max_tokens": 4096, "azure_ad_token": token.token},
            )
        elif self.model_name in GCP_MODELS:
            model = LiteLLMModel(
                model_id=self.model_id,
                params={
                    "temperature": 0.2,
                    "max_tokens": 4096,
                    "vertex_project": os.environ["VERTEXAI_PROJECT"],
                    "vertex_location": os.environ["VERTEXAI_LOCATION"],
                },
            )
        else:
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
            summary += f"| **Cost** | ${cost:.2f} |\n"
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
            if "merge successful" in output or "gh pr create" in str(response):
                return 0
            return 2
        except Exception as e:
            self.log.error("agent_failed", error=str(e))
            error_msg = str(e).replace("`", "'")  # Escape backticks for markdown
            self._write_summary(f"\n### Error\n```\n{error_msg}\n```\n")
            return 2
