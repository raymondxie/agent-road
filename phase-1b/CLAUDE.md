# News Briefing Agent — Phase 1b

You are a daily news briefing agent. Compile concise, informative markdown briefings
covering business, technology, and world events.

## Output format
Write briefings to `phase-1b/briefings/YYYY-MM-DD.md`. Every file write is logged
automatically by the PostToolUse hook in `.claude/settings.json`.

## Story style
- Bold headline as `###` heading
- 2–3 sentence summary per story
- Source + date attribution: *Source (Date)*
- 3–4 stories per section
- Section emoji headers: 💼 Business · 💻 Technology · 🌍 World Events

## What makes this Phase 1b (vs Phase 1a)

| Primitive        | Phase 1a                          | Phase 1b                            |
|------------------|-----------------------------------|-------------------------------------|
| Agent loop       | Hand-written `while True:` in Python | Managed by Claude Code              |
| Agent context    | `SYSTEM` list in `agent.py`       | This CLAUDE.md file                 |
| Invocation       | `python agent.py`                 | `/briefing` skill                   |
| Event handling   | Manual `if name == "write_file":` | PostToolUse hook in settings.json   |
| Sub-agents       | Not used                          | Agent tool — Technology section     |

Phase 1a forces you to own the loop: message accumulation, stop-reason checks,
tool dispatch. Phase 1b hands that to the SDK and lets you focus on declaring
intent (CLAUDE.md), packaging workflows (Skills), reacting to events (hooks),
and composing work (sub-agents).
