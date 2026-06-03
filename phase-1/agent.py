#!/usr/bin/env python3
"""Phase 1a: news briefing agent built directly on anthropic.messages.create."""

from datetime import date
from pathlib import Path

import anthropic

MODEL = "claude-sonnet-4-6"
client = anthropic.Anthropic()

SYSTEM = [
    {
        "type": "text",
        "text": (
            "You are a daily news briefing agent. Search for today's top stories "
            "across business, technology, and world events. Compile a clear, concise "
            "markdown briefing with a section for each topic and write it to disk."
        ),
        "cache_control": {"type": "ephemeral"},
    }
]

TOOLS = [
    {
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": 9,
    },
    {
        "name": "read_file",
        "description": "Read a local file and return its contents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a local file, creating parent directories as needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    },
]


def handle_tool(name: str, inputs: dict) -> str:
    if name == "read_file":
        return Path(inputs["path"]).read_text()
    if name == "write_file":
        path = Path(inputs["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(inputs["content"])
        return f"Written to {path}"
    raise ValueError(f"Unknown tool: {name}")


def run(task: str) -> None:
    messages = [{"role": "user", "content": task}]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            return

        tool_results = [
            {
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": handle_tool(block.name, block.input),
            }
            for block in response.content
            if block.type == "tool_use"
        ]

        if tool_results:
            messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    today = date.today().isoformat()
    output = f"briefings/{today}.md"
    print(f"Fetching news for {today}...")
    run(
        f"Search for today's ({today}) top news in business, technology, and world events. "
        f"Write a well-formatted markdown briefing with sections for each topic to {output}."
    )
    print(f"Briefing saved to {output}")
