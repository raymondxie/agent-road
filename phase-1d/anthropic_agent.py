#!/usr/bin/env python3
"""Phase 1d: news briefing agent — raw Anthropic API with token and latency tracking."""

import time
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
            "markdown briefing with a section for each topic and write it to disk.\n\n"
            "Format each section:\n"
            "- ### Bold headline\n"
            "- 2–3 sentence summary per story\n"
            "- Attribution: *Source (Date)*\n"
            "- 3–4 stories per section\n"
            "- Section emoji headers: 💼 Business · 💻 Technology · 🌍 World Events"
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
    if name == "write_file":
        path = Path(inputs["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(inputs["content"])
        return f"Written to {path}"
    raise ValueError(f"Unknown tool: {name}")


def run(task: str) -> dict:
    messages = [{"role": "user", "content": task}]
    total_input = 0
    total_output = 0
    total_cache_read = 0
    total_cache_write = 0
    search_count = 0
    start = time.monotonic()

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})
        total_input += response.usage.input_tokens
        total_output += response.usage.output_tokens
        total_cache_read += getattr(response.usage, "cache_read_input_tokens", 0)
        total_cache_write += getattr(response.usage, "cache_creation_input_tokens", 0)

        for block in response.content:
            block_type = getattr(block, "type", "")
            block_name = getattr(block, "name", "")
            if block_type == "server_tool_use" and block_name == "web_search":
                search_count += 1

        if response.stop_reason == "end_turn":
            break

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

    return {
        "input_tokens": total_input,
        "output_tokens": total_output,
        "cache_read_tokens": total_cache_read,
        "cache_write_tokens": total_cache_write,
        "web_searches": search_count,
        "latency_s": round(time.monotonic() - start, 1),
    }


def append_metadata(output_path: str, meta: dict) -> None:
    p = Path(output_path)
    if not p.exists():
        return
    block = (
        f"\n\n---\n\n"
        f"| Metric | Value |\n"
        f"|--------|-------|\n"
        f"| Agent | Anthropic raw API · {MODEL} |\n"
        f"| Input tokens | {meta['input_tokens']} |\n"
        f"| Output tokens | {meta['output_tokens']} |\n"
        f"| Cache read | {meta['cache_read_tokens']} |\n"
        f"| Cache write | {meta['cache_write_tokens']} |\n"
        f"| Web searches | {meta['web_searches']} |\n"
        f"| Latency | {meta['latency_s']}s |\n"
    )
    p.write_text(p.read_text() + block)


if __name__ == "__main__":
    today = date.today().isoformat()
    output = f"phase-1d/briefings/{today}-anthropic.md"
    print(f"[Anthropic] Fetching news for {today}...")
    meta = run(
        f"Search for today's ({today}) top news in business, technology, and world events. "
        f"Write a well-formatted markdown briefing with sections for each topic to {output}."
    )
    append_metadata(output, meta)
    print(
        f"[Anthropic] Done — {meta['latency_s']}s | "
        f"{meta['input_tokens']} in / {meta['output_tokens']} out tokens | "
        f"{meta['web_searches']} searches"
    )
