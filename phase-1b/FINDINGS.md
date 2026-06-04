# Phase 1b Findings

Real discoveries from building and running the Claude Agent SDK pattern.

---

## 0. "Claude Agent SDK" is a misleading label — Phase 1a is actually the SDK

The roadmap calls Phase 1b the "Claude Agent SDK" pattern, but this inverts the
traditional meaning of SDK.

**Phase 1a** (`anthropic.messages.create` + `while True:`) is the SDK pattern:
- You import a library and call functions
- You own the loop, state, and dispatch
- It's imperative — every behavior is explicit in your code
- It runs anywhere Python runs

**Phase 1b** (CLAUDE.md + Skill + Hook + Agent tool) is a **declarative platform**
pattern, not an SDK:
- You write markdown files that a runtime (Claude Code) interprets
- You declare intent; the platform executes it
- Debugging means observing platform behavior, not reading stack traces
- It only runs inside Claude Code

**Better analogies:**

| Phase 1a | Phase 1b |
|---|---|
| bash script | Dockerfile |
| Express route handler | nginx config |
| Python calling an API | GitHub Actions workflow YAML |
| Imperative code | Infrastructure-as-configuration |

The practical consequence: Phase 1b gives you less control but higher composability.
You can build and ship a workflow in 30 lines of markdown that would take 200 lines
of Python in Phase 1a. The tradeoff is opacity — when something goes wrong, you're
debugging the platform's interpretation of your instructions, not your own code.

**For the write-up:** Don't call Phase 1b "the SDK." Call it the
"declarative agent configuration" pattern, and position Phase 1a as the SDK baseline.

---

## 1. Hook data arrives via stdin, not env vars

**What I assumed:** PostToolUse hooks receive tool input via an env var like `CLAUDE_TOOL_INPUT`.

**What actually happens:** Claude Code passes a JSON payload to the hook script's **stdin**. Read it with:

```python
import sys, json
data = json.load(sys.stdin)
file_path = data["tool_input"]["file_path"]
```

**Full stdin schema for PostToolUse:**
```json
{
  "session_id": "...",
  "transcript_path": "...",
  "cwd": "...",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": { "file_path": "...", "content": "..." },
  "tool_response": { ... }
}
```

**Why this matters:** The SDK abstracts the agentic loop, but you still have to learn how its event plumbing actually surfaces data. Assuming env vars is a natural mistake coming from other hook systems (git hooks, GitHub Actions). The real primitive here isn't "fires on event" — it's "receives structured JSON on stdin and can inspect full context including cwd, session, and tool result."

---

## 2. Skill registration requires a manifest format, not just a file

**What I assumed:** Dropping a `.md` file into `.claude/skills/` in the project root would register a slash command.

**What actually happens:** Skills must live at `~/.claude/skills/<name>/SKILL.md` (user-level) with YAML frontmatter:

```yaml
---
name: news-briefing
description: "..."
triggers:
  - /news-briefing
  - news briefing
version: "1.0.0"
group: learning
---
```

**Why this matters:** The harness needs to discover and disambiguate skills at startup — it reads the manifest, not arbitrary markdown files. This is the same pattern as CLAUDE.md: you declare intent in a structured format; the SDK reads it. You don't write code to register anything.

---

## 3. Sub-agent is a genuine parallel call, not a prompt trick

The Technology section was fetched by a separate Agent instance with its own:
- Token budget: 19,361 tokens
- Tool use count: 3 web searches
- Execution time: ~25 seconds

This ran while the parent instance fetched Business and World Events. The sub-agent returned a self-contained markdown section; the parent merged it. No shared state, no callback — just a function call that returns a string.

**Phase 1a equivalent:** You would need to create a second `anthropic.Anthropic()` client call inside `handle_tool()`, manage its message loop, and pipe the result back manually. In Phase 1b, `Agent(prompt=..., description=...)` is the entire implementation.

---

## 4. CLAUDE.md replaces SYSTEM prompt, but scope is different

In Phase 1a, the SYSTEM prompt was injected per-API-call and controlled exactly what context the model saw. In Phase 1b, CLAUDE.md is loaded into every conversation that starts in (or below) that directory.

**Implication:** CLAUDE.md is persistent and ambient. It's the right place for identity, style, and conventions. It's the wrong place for per-task context — that belongs in the Skill.

---

## Phase 1a vs Phase 1b: What you own

| Concern | Phase 1a (raw API) | Phase 1b (Claude Agent SDK) |
|---|---|---|
| Message accumulation | You (`messages.append(...)`) | SDK |
| Stop-reason check | You (`if stop_reason == "end_turn"`) | SDK |
| Tool dispatch | You (`handle_tool()`) | SDK |
| Context injection | You (SYSTEM list in Python) | CLAUDE.md |
| Workflow packaging | You (`if __name__ == "__main__"`) | Skill |
| Event reactions | You (`if name == "write_file": log(...)`) | PostToolUse hook |
| Parallelism | You (threading / asyncio) | Agent tool |

Phase 1a gives you maximum visibility and control. Phase 1b gives you composability and removes boilerplate. The tradeoff: debugging Phase 1b requires understanding the SDK's event model (see Finding #1).
