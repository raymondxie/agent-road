# Agent Engineering Roadmap

A personalized 29-week study plan for becoming a production-ready agent engineer.

Based on the [2026 Agent Engineering Roadmap](https://github.com/codejunkie99/agent-roadmap-2026) and inspired by [@av1dlive](https://x.com/av1dlive/status/2052063154423898603?s=46&t=5ph6HbnFtYfyltxgMGTT_Q).

## Stack

- **Languages:** Python + TypeScript
- **Providers:** Anthropic + OpenAI
- **Frameworks:** LangGraph (Python) · Mastra (TypeScript) · Claude Agent SDK · OpenAI Agents SDK

## Progress

| Phase | Topic | Status |
|-------|-------|--------|
| 0 | Foundations — 2-page mental model | ✅ Complete |
| 1a | First agent — raw Anthropic API loop | ✅ Complete |
| 1b | Claude Agent SDK — declarative platform pattern | ✅ Complete |
| 1c | OpenAI Agents SDK — structural comparison | ✅ Complete |
| 1d | Week-long parallel run — Anthropic vs OpenAI | 🔄 In Progress |
| 2a | Research-analyst deep agent in LangGraph Python | ⬜ Planned |
| 2b | Same agent in Mastra (TypeScript) | ⬜ Planned |
| 3 | Build the harness from scratch | ⬜ Planned |
| 4 | Evals & regression suite | ⬜ Planned |
| 5 | Production hardening | ⬜ Ongoing |

## Key Findings So Far

**Phase 1a vs 1b:** "Claude Agent SDK" is a misleading label. Phase 1a (raw API loop) is the SDK pattern; Phase 1b (CLAUDE.md + Skills + Hooks) is a declarative platform — closer to a Dockerfile than a library. See [`phase-1b/FINDINGS.md`](phase-1b/FINDINGS.md).

**Phase 1b vs 1c:** OpenAI Agents SDK (`Runner.run()`) is structurally closer to Phase 1a than Phase 1b. Both are imperative Python programs. Phase 1b is a different category entirely. See [`phase-1c/FINDINGS.md`](phase-1c/FINDINGS.md).

**Parallelism in declarative platforms:** In Phase 1b, the words in your skill instructions are the scheduler. "While the sub-agent runs..." reads as parallelism but produces serialization. You must say "issue all three calls in the same response" to get genuine concurrent tool calls.

## Phase 1d — Parallel Briefing Run

The same news briefing agent runs daily at 11:30am using both providers:
- `phase-1d/anthropic_agent.py` — raw Anthropic API (`claude-sonnet-4-6`)
- `phase-1d/openai_agent.py` — OpenAI Agents SDK (`gpt-4o`)

Each day produces two dated briefing files in `phase-1d/briefings/` with a metadata table (tokens, latency, search count) appended.

### Running it yourself

```bash
cd phase-1d
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env — add ANTHROPIC_API_KEY and OPENAI_API_KEY

# run both agents once
python anthropic_agent.py
python openai_agent.py

# or run the daily script
bash run_daily.sh
```

### Scheduling (macOS)

```bash
# load the LaunchAgent (runs daily at 11:30am)
launchctl load ~/Library/LaunchAgents/com.raymond.agent-briefing.plist

# verify it's registered
launchctl list | grep agent-briefing

# unload when the week is done
launchctl unload ~/Library/LaunchAgents/com.raymond.agent-briefing.plist
```

## Structure

| Path | Purpose |
|------|---------|
| `MY_ROADMAP.md` | Personalized phase plan, deliverables, and next action |
| `AGENTS.md` | Instructions for AI agents opening this project |
| `phase-0/` | Foundations mental model |
| `phase-1/` | Phase 1a — raw Anthropic API agent |
| `phase-1b/` | Phase 1b — Claude Agent SDK (declarative) |
| `phase-1c/` | Phase 1c — OpenAI Agents SDK |
| `phase-1d/` | Phase 1d — week-long parallel run |
