# Phase 1c Findings — OpenAI Agents SDK

Same news-briefing agent as Phase 1a and 1b, rebuilt on the OpenAI Agents SDK.
Goal: identify what differs structurally across all three approaches.

## Structural Comparison

| Dimension | Phase 1a (raw Anthropic API) | Phase 1b (Claude Agent SDK) | Phase 1c (OpenAI Agents SDK) |
|-----------|------------------------------|-----------------------------|-----------------------------|
| Agent loop | Hand-written `while True:` | Managed by Claude Code | Managed by `Runner.run()` |
| System prompt | `SYSTEM` list with `cache_control` dict | `CLAUDE.md` file on disk | `instructions` string in code |
| Tool definition | JSON schema dicts | Declared in SKILL.md workflow | `@function_tool` decorator + type hints |
| Web search | `{"type": "web_search_20250305"}` | `WebSearch` (Claude Code built-in) | `WebSearchTool()` class instance |
| Tool dispatch | Manual `handle_tool()` switch | Automatic | Automatic |
| Invocation | `python agent.py` | `/news-briefing` skill | `python agent.py` |
| Sub-agents | Not used | Agent tool → spawns Claude instance | Handoffs (control passed within process) |
| Event hooks | Not available | PostToolUse hooks in settings.json | Not available |
| Final output | Parse `response.content` blocks manually | File written by agent | `result.final_output` string |
| Provider lock | Anthropic | Anthropic (Claude Code runtime) | OpenAI |

## Key Findings

### Finding #1 — Phase 1c is structurally closer to Phase 1a than Phase 1b

Phase 1a and 1c are both imperative Python programs. The difference is that 1c's
SDK owns the agentic loop (`Runner.run()`), while 1a owns it manually (`while True:`).
Phase 1b is a different kind of thing entirely — declarative config files, not a
Python program. The loop, context, and execution are all managed by the Claude Code
process itself.

### Finding #2 — `@function_tool` is a decorator-based replacement for JSON schema dicts

Phase 1a requires writing raw JSON schema objects:
```python
{"name": "write_file", "input_schema": {"type": "object", "properties": {...}}}
```
Phase 1c replaces this with a typed Python function and a decorator:
```python
@function_tool
def write_file(path: str, content: str) -> str: ...
```
The SDK infers the schema from type annotations. Same intent, far less boilerplate.
The tradeoff: you lose the ability to add fine-grained JSON Schema constraints
(e.g., `minLength`, `pattern`) without a separate schema override.

### Finding #3 — Web search is a first-class class vs. a string-typed dict

Phase 1a: `{"type": "web_search_20250305", "name": "web_search", "max_uses": 9}`
Phase 1c: `WebSearchTool(user_location={"type": "approximate", "city": "..."})`

OpenAI's `WebSearchTool` is a Python class with a typed constructor. Anthropic's
built-in web search is a dict with a magic `type` string. The class-based approach
is more discoverable and IDE-friendly, but both achieve the same thing.

### Finding #4 — No hooks equivalent in OpenAI Agents SDK

Phase 1b's PostToolUse hook fires a shell command every time a Write completes —
no agent code required. OpenAI Agents SDK has no equivalent. You'd need to
subclass `Agent` or wrap `Runner.run()` to intercept tool calls. This is a
meaningful gap if you want event-driven side effects (logging, notifications,
audit trails) without touching agent code.

### Finding #5 — Multi-agent composition is process-based in 1b, in-process in 1c

Phase 1b sub-agents: the Agent tool spawns a new Claude Code process with its own
context window and tool permissions.

Phase 1c handoffs: `agent_a` passes control to `agent_b` within the same
`Runner.run()` call. State is shared in the same Python process; context is
carried across by the SDK.

The Phase 1b model is heavier (separate process, separate context window) but
more isolated. The Phase 1c model is lightweight but means all agents share the
same failure domain.

### Finding #6 — `WebSearchTool` silently does nothing with `gpt-4o-mini`

`WebSearchTool` is a hosted tool that runs via OpenAI's Responses API. With
`gpt-4o-mini`, the model never calls it — it skips the search and generates
plausible-sounding but fully hallucinated stories with fake citations. There is
no error or warning; the agent just completes normally.

Switching to `gpt-4o` fixes it: the tool fires, results are grounded in real
sources, and citations include actual URLs. Verified with `AgentHooks.on_tool_start`
and a forced query (current SF weather) that the model cannot answer from training.

**Lesson:** With hosted tools, always verify tool invocation explicitly — the model
may silently skip tools it doesn't know how to invoke. `AgentHooks` is the right
instrumentation for this.

## Running and Debugging

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Requires `OPENAI_API_KEY` in the environment.

To verify tools are actually firing (see Finding #6):

```bash
python diagnose.py
```

`diagnose.py` uses `AgentHooks.on_tool_start` / `on_tool_end` to print every tool
invocation and a 200-character preview of the result. Run it whenever you suspect
the model is skipping a tool silently.
