"""Fuzzer bug fixing agent using Claude Agent SDK."""

import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

import anyio
import structlog
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    query,
)

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
PROMPTS_DIR = REPO_ROOT / "tools" / "fuzzer" / "prompts"
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"


class MessageLogger:
    """Exhaustive file logger for Claude Agent SDK messages."""

    def __init__(self):
        self.log_dir = LOGS_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.messages_file = open(self.log_dir / "messages.jsonl", "w")
        self.assistant_file = open(self.log_dir / "assistant.md", "w")
        self.tools_file = open(self.log_dir / "tools.log", "w")
        self.turn = 0

    def close(self):
        self.messages_file.close()
        self.assistant_file.close()
        self.tools_file.close()

    def _ts(self) -> str:
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def _write_json(self, msg_type: str, data: dict):
        record = {"ts": self._ts(), "type": msg_type, "data": data}
        self.messages_file.write(json.dumps(record, default=str) + "\n")
        self.messages_file.flush()

    def log_assistant(self, msg: AssistantMessage):
        self.turn += 1
        self.assistant_file.write(f"\n{'=' * 60}\n## Turn {self.turn}\n{'=' * 60}\n\n")
        blocks_data = []
        for block in msg.content:
            if isinstance(block, TextBlock):
                self.assistant_file.write(f"{block.text}\n\n")
                blocks_data.append({"type": "text", "text": block.text})
            elif isinstance(block, ThinkingBlock):
                self.assistant_file.write(f"<thinking>\n{block.thinking}\n</thinking>\n\n")
                blocks_data.append({"type": "thinking", "thinking": block.thinking})
            elif isinstance(block, ToolUseBlock):
                self.assistant_file.write(
                    f"**Tool: {block.name}**\n```json\n{json.dumps(block.input, indent=2, default=str)}\n```\n\n"
                )
                self._log_tool_use(block)
                blocks_data.append(
                    {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
                )
            elif isinstance(block, ToolResultBlock):
                content_preview = str(block.content)[:500] if block.content else ""
                self.assistant_file.write(
                    f"**Tool Result ({block.tool_use_id})**\n```\n{content_preview}\n```\n\n"
                )
                blocks_data.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.tool_use_id,
                        "content": block.content,
                        "is_error": block.is_error,
                    }
                )
        self._write_json(
            "assistant",
            {
                "model": msg.model,
                "error": msg.error,
                "parent_tool_use_id": msg.parent_tool_use_id,
                "blocks": blocks_data,
            },
        )
        self.assistant_file.flush()

    def _log_tool_use(self, block: ToolUseBlock):
        ts = self._ts()
        self.tools_file.write(f"\n[{ts}] TOOL: {block.name} (id={block.id})\n")
        self.tools_file.write(f"INPUT:\n{json.dumps(block.input, indent=2, default=str)}\n")
        self.tools_file.flush()

    def log_tool_result(self, block: ToolResultBlock):
        ts = self._ts()
        content = block.content if block.content else "(empty)"
        if isinstance(content, str) and len(content) > 2000:
            content = content[:2000] + f"\n... (truncated, {len(block.content)} chars total)"
        self.tools_file.write(f"[{ts}] RESULT for {block.tool_use_id}:\n")
        if block.is_error:
            self.tools_file.write("ERROR: ")
        self.tools_file.write(f"{content}\n")
        self.tools_file.write("-" * 40 + "\n")
        self.tools_file.flush()

    def log_system(self, msg: SystemMessage):
        self._write_json("system", {"subtype": msg.subtype, "data": msg.data})

    def log_user(self, msg: UserMessage):
        if isinstance(msg.content, str):
            self._write_json("user", {"content": msg.content, "uuid": msg.uuid})
        else:
            blocks_data = []
            for block in msg.content:
                if isinstance(block, ToolResultBlock):
                    self.log_tool_result(block)
                    blocks_data.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.tool_use_id,
                            "content": str(block.content)[:1000] if block.content else None,
                            "is_error": block.is_error,
                        }
                    )
                elif isinstance(block, TextBlock):
                    blocks_data.append({"type": "text", "text": block.text})
                else:
                    blocks_data.append({"type": type(block).__name__})
            self._write_json("user", {"blocks": blocks_data, "uuid": msg.uuid})

    def log_result(self, msg: ResultMessage):
        data = {
            "subtype": msg.subtype,
            "duration_ms": msg.duration_ms,
            "duration_api_ms": msg.duration_api_ms,
            "is_error": msg.is_error,
            "num_turns": msg.num_turns,
            "session_id": msg.session_id,
            "total_cost_usd": msg.total_cost_usd,
            "usage": msg.usage,
            "result": msg.result,
        }
        self._write_json("result", data)
        # Also write standalone result file
        with open(self.log_dir / "result.json", "w") as f:
            json.dump(data, f, indent=2, default=str)


class ClaudeFuzzerFixer:
    """Agent that finds and fixes fuzzer bugs using Claude Agent SDK."""

    def __init__(self):
        self.log = structlog.get_logger()
        self.system_prompt = self._load_system_prompt()

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

    async def _run_async(self, msg_logger: MessageLogger) -> tuple[str, ResultMessage | None]:
        """Async implementation of the agent loop."""
        options = ClaudeAgentOptions(
            system_prompt=self.system_prompt,
            allowed_tools=["Bash", "Read", "Write", "Edit", "Glob", "Grep"],
            permission_mode="acceptEdits",
            cwd=str(REPO_ROOT),
        )
        output = ""
        result_msg = None
        log = self.log
        async for message in query(
            prompt="Find and fix one parser bug using the fuzzer.",
            options=options,
        ):
            if isinstance(message, AssistantMessage):
                msg_logger.log_assistant(message)
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text, flush=True)
                        output += block.text.lower()
                    elif isinstance(block, ToolUseBlock):
                        if block.name == "Bash":
                            cmd = block.input.get("command", "")
                            preview = cmd[:80] + "..." if len(cmd) > 80 else cmd
                            log.info("bash", command=preview)
                        else:
                            log.info("tool", name=block.name)
                    elif isinstance(block, ToolResultBlock):
                        msg_logger.log_tool_result(block)
            elif isinstance(message, ResultMessage):
                msg_logger.log_result(message)
                result_msg = message
                log.info("result", turns=message.num_turns, cost=message.total_cost_usd)
            elif isinstance(message, SystemMessage):
                msg_logger.log_system(message)
            elif isinstance(message, UserMessage):
                msg_logger.log_user(message)
        return output, result_msg

    def run(self) -> int:
        """Run the fuzzer fixing agent.

        Returns:
            0: Fixed a bug and created PR
            1: No bugs found (fuzzer found no discrepancies)
            2: Agent failed
        """
        base_sha = self._get_git_sha()
        self._write_summary(
            f"## Fuzzer Agent\n\n| | |\n|---|---|\n| **Model** | `claude-code` |\n| **Base SHA** | `{base_sha}` |\n"
        )
        self.log.info("agent_start", model="claude-code", base_sha=base_sha, logs=str(LOGS_DIR))
        msg_logger = MessageLogger()
        start_time = time.time()
        try:
            output, result_msg = anyio.run(lambda: self._run_async(msg_logger))
            duration = time.time() - start_time
            msg_logger.close()
            final_sha = self._get_git_sha()
            mre = ""
            mre_path = Path("/tmp/mre.txt")
            try:
                if mre_path.exists():
                    mre = mre_path.read_text().strip()
            except Exception:
                pass
            # Extract usage from result message
            input_tokens = 0
            output_tokens = 0
            cost = 0.0
            if result_msg:
                if result_msg.usage:
                    input_tokens = result_msg.usage.get("input_tokens", 0)
                    output_tokens = result_msg.usage.get("output_tokens", 0)
                cost = result_msg.total_cost_usd or 0.0
            summary = f"| **Final SHA** | `{final_sha}` |\n"
            summary += f"| **Tokens** | {input_tokens:,} in / {output_tokens:,} out |\n"
            summary += f"| **Cost** | ${cost:.4f} |\n"
            summary += f"| **Duration** | {duration:.1f}s |\n"
            summary += f"| **Logs** | `{LOGS_DIR}` |\n"
            if mre:
                summary += f"\n### MRE\n```bash\n{mre}\n```\n"
            self._write_summary(summary)
            self.log.info(
                "agent_complete",
                duration=round(duration, 2),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=round(cost, 4),
                logs=str(LOGS_DIR),
            )
            if "no discrepancies" in output or "no bugs found" in output:
                return 1
            if "merge successful" in output or "gh pr create" in output:
                return 0
            return 2
        except Exception as e:
            msg_logger.close()
            self.log.error("agent_failed", error=str(e), logs=str(LOGS_DIR))
            error_msg = str(e).replace("`", "'")
            self._write_summary(f"\n### Error\n```\n{error_msg}\n```\n")
            return 2
