# My Agent Engineering Roadmap

*Personalized from https://github.com/codejunkie99/agent-roadmap-2026 on 2026-05-19.*

## Profile
- Level: Built simple agents (not yet shipped to production)
- Time: 10 hrs/week
- Stack: Python + TypeScript · Anthropic + OpenAI
- Goal: All — get hired, ship at current job, launch a product, learn for fun
- Total estimated duration: ~29 weeks + ongoing Phase 5

## Phase Plan

| Phase | Mode | Adjusted Duration | Why |
|---|---|---|---|
| Phase 0: Foundations | SPEEDRUN | ~0.5 weeks (3–4 sessions) | You've built agents; skip the "what is an agent" beginner ramp. Write the 2-page doc and move on. |
| Phase 1: First Agent | NORMAL | ~5 weeks | Scratch agent + both Claude Agent SDK *and* OpenAI Agents SDK — you want both provider ecosystems solid. |
| Phase 2: Real Architecture | NORMAL | ~7 weeks | LangGraph Python is the primary runtime; add Mastra (TS-native) as a parallel exploration for TS depth. |
| Phase 3: Build the Harness | NORMAL | ~7 weeks | Do not skip. Building from scratch is the fastest path to "get hired" credibility and understanding production trade-offs. |
| Phase 4: Evals & Regression | DEEP | ~9 weeks | Weighted heaviest — eval infra is the #1 hiring signal and the #1 quality gap in the field. |
| Phase 5: Production Hardening | DEEP | Ongoing | Elevated for product-launch discipline. Cost, safety, drift monitoring never stop. |

*Math: 0.5 + 5 + 7 + 7 + 9 = 28.5 → rounded to 29 weeks. Canonical 17-week timeline × 2.0 pace adjustment for 10 hrs/week.*

---

## Curated Resources for This Profile

### Anthropic (primary provider)
- **Building Effective Agents** (Anthropic, Dec 2024) — workflows vs. agents, failure modes
- **Effective context engineering for AI agents** (Anthropic, Sep 2025) — read twice
- **Tutorial: Build a tool-using agent** (Anthropic docs) — Phase 1 scratch loop reference
- **Claude Agent SDK docs** — CLAUDE.md, Skills, hooks, sub-agents
- **Scaling Managed Agents** (Anthropic) — session/harness/sandbox separation
- **Code execution with MCP** (Anthropic, Nov 2025) — 150K → 2K token reduction pattern
- **Introducing advanced tool use** (Anthropic) — `defer_loading: true`, CORE 79.5% → 88.1%
- **Beyond permission prompts** (Anthropic, Oct 2025) — Claude Code safety model
- **Demystifying evals for AI agents** (Anthropic) — best primer on four eval types

### OpenAI (secondary provider)
- **OpenAI Agents SDK docs** — April 2026: sandboxing and harness added
- **OpenAI Cookbook** — tool use, structured outputs, eval notebooks
- ⚠️ *OpenAI-locked caveat from roadmap:* OpenAI Agents SDK is fine for OpenAI-only workloads. Phase 3 harness lessons port across providers regardless — build it provider-agnostic (LiteLLM or direct SDK swap) from day one.

### Both Providers / Framework-Agnostic
- **LangGraph docs** — primary runtime: state graphs, PostgresSaver, time-travel, OTEL
- **Doubling down on Deep Agents** (LangChain) — harness vs. framework vs. runtime
- **Context Engineering for Agents** (LangChain) — Write/Select/Compress/Isolate framework
- **How Middleware Lets You Customize Your Agent Harness** (LangChain, Mar 2026)
- **The Anatomy of an Agent Harness** (LangChain) — Phase 3 decomposition reference
- **Improving Deep Agents with harness engineering** (Vivek Trivedy, Feb 2026) — Rank 30 → 5 on Terminal-Bench
- **Evaluating Deep Agents: Our Learnings** (LangChain) — single-step, full-turn, multi-turn eval patterns
- **Agent Evaluation Readiness Checklist** (LangChain) — 17-min practical checklist
- **Inspect docs + inspect_evals** — 200+ standard evals (GAIA, SWE-bench, Cybench)

### TypeScript / Mastra
- **Mastra docs** (mastra.ai) — TS-native LangGraph alternative, v1.0 Jan 2026, YC W25
- Use in Phase 2 as a parallel track: build the research-analyst agent in both LangGraph (Python) and Mastra (TS) to internalize the same architecture in both stacks

### Free Courses (stack-relevant)
- **LangChain Academy: Introduction to LangGraph** — free, covers state/memory/multi-agent
- **HuggingFace Agents Course** — smolagents and MCP coverage
- **Anthropic Interactive Prompt Engineering** — 9 Jupyter notebook chapters
- **MCP Fundamentals on FreeAcademy** — building MCP servers and custom tools

---

## Project Deliverables

- [x] **Phase 0:** 2-page mental-model doc (hand-written or typed without references)
- [x] **Phase 1a:** ~100-line scratch agent using `anthropic.messages.create` (web_search, read_file, write_file)
- [x] **Phase 1b:** Same agent rebuilt on Claude Agent SDK (CLAUDE.md, Skill, PostToolUse hook, Task sub-agent)
- [ ] **Phase 1c:** Same agent rebuilt on OpenAI Agents SDK — note what differs structurally
- [ ] **Phase 1d:** Daily-briefing agent running for 1 week on real data → public GitHub repo + writeup
- [ ] **Phase 2a:** Research-analyst deep agent in LangGraph Python (PostgresSaver, human-in-the-loop, LangSmith trace URL)
- [ ] **Phase 2b:** Same agent in Mastra (TypeScript) — public GitHub repo + comparison writeup
- [ ] **Phase 3:** ~1,500-line Python mini-harness (loop, dispatch, compression, sub-agents, hooks, OTEL, SQLite resume) + 1,000-word post-mortem comparing to Claude Agent SDK and Deep Agents → public GitHub + writeup
- [ ] **Phase 4:** Golden dataset (30–50 questions) + all four eval types + CI gate + `make eval` target + Inspect benchmark run → public GitHub
- [ ] **Phase 4 bonus:** Publish benchmark numbers with full configuration (hiring signal)
- [ ] **Phase 5:** Production hardening checklist (prompt caching, model routing, sandbox, drift alerts) — living document, updated per model upgrade
- [ ] **Phase 5 product:** Cost-discipline deliverable — cost-per-task budget with monitoring (required for product launch)

*"Get hired" rule applied: one public repo + writeup per phase. Phase 4 is the heaviest hiring signal — don't shortcut it.*

---

## Next Action

Read **"Building Effective Agents"** (Anthropic, Dec 2024) — search for it on the Anthropic blog — then immediately open a blank doc and write your 2-page mental-model explainer from memory. That doc *is* the Phase 0 deliverable.

---

*Future sessions: check unchecked deliverables above to identify current phase. "Next Action" updates after each deliverable is completed.*
