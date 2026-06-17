#!/usr/bin/env python3
"""Phase 1c: news briefing agent built on the OpenAI Agents SDK."""

import asyncio
from datetime import date
from pathlib import Path

from agents import Agent, Runner, WebSearchTool, function_tool

MODEL = "gpt-4o-mini"

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


@function_tool
def write_file(path: str, content: str) -> str:
    """Write content to a local file, creating parent directories as needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"Written to {p}"


agent = Agent(
    name="news-briefing",
    instructions=INSTRUCTIONS,
    tools=[WebSearchTool(), write_file],
    model=MODEL,
)


async def run(task: str) -> None:
    result = await Runner.run(agent, task)
    print(result.final_output)


if __name__ == "__main__":
    today = date.today().isoformat()
    output = f"phase-1c/briefings/{today}.md"
    print(f"Fetching news for {today}...")
    asyncio.run(run(
        f"Search for today's ({today}) top news in business, technology, and world events. "
        f"Write a well-formatted markdown briefing with sections for each topic to {output}."
    ))
    print(f"Briefing saved to {output}")
