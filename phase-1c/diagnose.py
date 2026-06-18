#!/usr/bin/env python3
"""Diagnose whether WebSearchTool actually fires during a run."""

import asyncio
from pathlib import Path

from agents import Agent, AgentHooks, Runner, WebSearchTool, function_tool
from agents.run_context import RunContextWrapper


class LoggingHooks(AgentHooks):
    async def on_tool_start(self, context: RunContextWrapper, agent: Agent, tool) -> None:
        print(f"  [TOOL START] {tool.name}")

    async def on_tool_end(self, context: RunContextWrapper, agent: Agent, tool, result: str) -> None:
        preview = result[:200].replace("\n", " ") if result else "(empty)"
        print(f"  [TOOL END]   {tool.name} → {preview}")


@function_tool
def write_file(path: str, content: str) -> str:
    """Write content to a local file, creating parent directories as needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"Written to {p}"


agent = Agent(
    name="news-briefing-diag",
    instructions="Search the web for today's top AI news story and write a 2-sentence summary to diag-output.txt.",
    tools=[WebSearchTool(), write_file],
    model="gpt-4o",
    hooks=LoggingHooks(),
)


async def main() -> None:
    print("Running with hooks — watching for tool calls...\n")
    result = await Runner.run(agent, "Find today's top AI news story and write a 2-sentence summary to diag-output.txt.")
    print(f"\nFinal output: {result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())
