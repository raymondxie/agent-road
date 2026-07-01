#!/usr/bin/env python3
"""Phase 1d: news briefing agent — OpenAI Agents SDK with hook-based tracking."""

import asyncio
import time
from datetime import date
from pathlib import Path

from agents import Agent, AgentHooks, Runner, WebSearchTool, function_tool, set_tracing_disabled
from agents.run_context import RunContextWrapper

# Suppress tracing 403 spam — OpenAI's zero-data-retention orgs block trace ingestion
set_tracing_disabled(True)

MODEL = "gpt-4o"

INSTRUCTIONS = (
    "You are a daily news briefing agent. Search for today's top stories "
    "across business, technology, and world events. Compile a concise "
    "markdown briefing with a section for each topic and write it to disk.\n\n"
    "Format each section:\n"
    "- ### Bold headline\n"
    "- 2–3 sentence summary per story\n"
    "- Attribution: *Source (Date)*\n"
    "- 3–4 stories per section\n"
    "- Section emoji headers: 💼 Business · 💻 Technology · 🌍 World Events"
)


class TrackingHooks(AgentHooks):
    def __init__(self) -> None:
        self.tool_calls: list[str] = []
        self.search_count = 0

    async def on_tool_start(
        self, context: RunContextWrapper, agent: Agent, tool
    ) -> None:
        name = getattr(tool, "name", str(tool))
        self.tool_calls.append(name)
        if "search" in name.lower():
            self.search_count += 1
        print(f"  [TOOL] {name}")


@function_tool
def write_file(path: str, content: str) -> str:
    """Write content to a local file, creating parent directories as needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"Written to {p}"


def append_metadata(output_path: str, meta: dict) -> None:
    p = Path(output_path)
    if not p.exists():
        return
    block = (
        f"\n\n---\n\n"
        f"| Metric | Value |\n"
        f"|--------|-------|\n"
        f"| Agent | OpenAI Agents SDK · {MODEL} |\n"
        f"| Web searches | {meta['search_count']} |\n"
        f"| Total tool calls | {meta['total_tools']} |\n"
        f"| Latency | {meta['latency_s']}s |\n"
    )
    p.write_text(p.read_text() + block)


async def run(task: str) -> dict:
    hooks = TrackingHooks()
    agent = Agent(
        name="news-briefing",
        instructions=INSTRUCTIONS,
        tools=[WebSearchTool(), write_file],
        model=MODEL,
        hooks=hooks,
    )
    start = time.monotonic()
    result = await Runner.run(agent, task)
    latency = time.monotonic() - start

    # Hosted tools (WebSearchTool) don't trigger on_tool_start; count from new_items instead.
    search_count = sum(
        1
        for item in result.new_items
        if getattr(getattr(item, "raw_item", None), "type", "") == "web_search_call"
    )
    return {
        "search_count": search_count,
        "total_tools": len(hooks.tool_calls) + search_count,
        "latency_s": round(latency, 1),
    }


if __name__ == "__main__":
    today = date.today().isoformat()
    output = f"phase-1d/briefings/{today}-openai.md"
    print(f"[OpenAI] Fetching news for {today}...")
    meta = asyncio.run(run(
        f"Search for today's ({today}) top news in business, technology, and world events. "
        f"Write a well-formatted markdown briefing with sections for each topic to {output}."
    ))
    append_metadata(output, meta)
    print(
        f"[OpenAI] Done — {meta['latency_s']}s | "
        f"{meta['search_count']} searches | "
        f"{meta['total_tools']} total tool calls"
    )
