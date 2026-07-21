# Phase 2a Findings — LangGraph Research-Analyst Agent

Building the same research task (Phase 1a/1c news briefing pattern, now applied to
company research) on LangGraph with PostgresSaver and human-in-the-loop. Goal: learn
what changes when you move from a linear agent loop to an explicit state graph.

---

## 0. The core shift: loop → graph

In Phase 1a and 1c, the "agent" is a `while True:` loop (or `Runner.run()` equivalent)
where the model calls tools until it stops. The flow is implicit — you infer what
happened by reading tool call logs.

In LangGraph, the flow is a **named directed graph**:

```
plan → search → analyze → [interrupt] → write → END
```

Each node is a Python function. Each edge is explicit. The state is a typed dict that
every node reads from and writes to. This has three practical consequences:

1. **Inspectability** — you can call `app.get_state(config)` at any point and see
   exactly what the agent knows: queries it planned, raw search results, the synthesized
   analysis, whether human feedback was provided. No log parsing required.

2. **Testability** — you can unit test individual nodes by passing a `ResearchState`
   dict directly. `plan({"company": "Stripe", ...})` runs just the planning step in
   isolation. In Phase 1a, testing a specific step meant mocking the entire API loop.

3. **Resumability** — because state is checkpointed at every node boundary, a crash
   mid-run is recoverable. The Hinge Health first run crashed at `input()` due to a
   non-TTY stdin. Calling `app.invoke(None, config=config)` resumed exactly at the
   `write` node with all prior state intact — no re-searching, no re-analyzing.

**The tradeoff:** more upfront design. You have to decide your nodes, state schema,
and edge routing before you write a line of LLM code. In Phase 1a, you just start
the loop and let the model figure it out.

---

## 1. PostgresSaver: checkpointing is the difference between a script and a service

In Phase 1a, a crash means starting over. In LangGraph with PostgresSaver, a crash
means resuming from the last completed node.

The setup:
```python
with psycopg.connect(conn_string, autocommit=True) as conn:
    checkpointer = PostgresSaver(conn)
    checkpointer.setup()  # creates checkpoint tables on first run
    app = graph.compile(checkpointer=checkpointer, interrupt_before=["write"])
```

`checkpointer.setup()` creates three tables in Postgres: `checkpoints`,
`checkpoint_blobs`, and `checkpoint_writes`. Every time a node completes, LangGraph
serializes the full state and writes a checkpoint. Resuming is:
```python
app.invoke(None, config=config)  # None = resume from last checkpoint
```

**What this unlocks:**
- **Multi-session runs** — stop the process, come back later, resume where you left off
- **Time travel** — `app.get_state_history(config)` returns every checkpoint; you can
  rewind to any prior state and re-run from there
- **Parallel threads** — multiple companies can be researched simultaneously without
  interfering; each has its own `thread_id`

**What it requires:**
- A running Postgres instance (Docker Compose handles this locally)
- The connection must stay open during the entire `invoke` call — the `with` block
  pattern in `main()` handles this correctly

**Operational note:** `MemorySaver` (in-memory, no Postgres) works for testing and
is a drop-in swap. Use it to verify graph logic before wiring up the database.

---

## 2. Human-in-the-loop: three primitives

LangGraph's interrupt pattern uses three operations:

**1. `interrupt_before=["write"]` at compile time**
Tells LangGraph to pause before executing the `write` node. The graph runs normally
through `analyze`, then halts. The process doesn't block — `app.invoke()` returns
with the current state.

**2. `app.update_state(config, {"human_feedback": feedback})`**
Injects data into the checkpointed state without re-running any node. After this
call, the checkpoint in Postgres contains the human's feedback. The next `invoke`
picks it up automatically.

**3. `app.invoke(None, config=config)` to resume**
Passing `None` (instead of an initial state dict) tells LangGraph to resume from the
last checkpoint. It runs only the remaining nodes — in this case, just `write`.

**What the `write` node does with feedback:**
```python
feedback = state.get("human_feedback", "").strip()
feedback_section = f"\n\nAnalyst additions: {feedback}" if feedback else ""
```
The LLM sees the full research findings plus any human additions in the same prompt.
This is the simplest possible human-in-the-loop pattern — the human adds context, not
corrections. More complex patterns (human approves or rejects the plan, human edits
individual search results) would require either more interrupt points or a
`human_review` node with conditional routing.

---

## 3. `input()` breaks in non-TTY environments — design for it

The first Hinge Health run crashed with `EOFError: EOF when reading a line` because
Claude Code's bash tool has no TTY attached to stdin. `input()` only works in an
interactive terminal.

This is not an edge case — it's any automated or piped invocation:
```bash
echo "" | python agent.py "Stripe"   # breaks
python agent.py "Stripe" < /dev/null  # breaks
launchctl (Phase 1d)                  # breaks
CI/CD pipelines                       # breaks
```

**Fix added:** `--fresh` flag for new threads, and `--resume` flag to show state and
accept feedback. But the deeper fix for production is to replace `input()` with a
`--feedback` CLI argument:
```bash
python agent.py "Hinge Health" --feedback "focus on Medicare Advantage expansion"
```
This makes the agent fully scriptable. Human interaction becomes a flag, not a
blocking call. The interrupt still fires; the feedback is just pre-supplied.

---

## 4. Date injection is required for research agents — same finding as Phase 1d, different cause

Without an explicit date in the plan prompt, Claude generated queries anchored to
2025 (its training data period), not 2026 (today):

```
# Without date injection:
"Hinge Health news announcements partnerships 2025"   ← stale

# With date injection (today = 2026-07-21):
"Hinge Health news announcements June July 2026"      ← current
```

The root cause here is different from Phase 1d's GPT-4o issue. Claude knows it has a
training cutoff and will try to be helpful by searching for "recent" news — but
"recent" defaults to the last period well-represented in its training data, not the
actual current date. Injecting `today = date.today().isoformat()` into the plan
prompt and instructing the model to reference it in the news query fixes this.

**Fix:**
```python
f"Today's date is {today}. "
f"Make sure the news query explicitly references {today[:7]} or recent months."
```

The result: the updated Hinge Health run surfaced Q1 2026 earnings ($182.3M, +47%),
the June 10 Investor Day guidance raise, and the surgery addition to HingeSelect —
none of which appeared in the stale first run.

---

## 5. Tavily vs. Anthropic built-in web search

Phase 1a used Anthropic's `web_search_20250305` built-in tool. Phase 2a uses Tavily.
The practical differences:

| Dimension | Anthropic built-in | Tavily |
|-----------|-------------------|--------|
| API key required | No | Yes (free tier) |
| Result format | Text blocks via tool_result | Structured JSON (`url`, `content`, `score`) |
| URL visibility | Hidden (agent synthesizes) | Explicit (can cite sources directly) |
| langchain-community | Not needed | Not needed (use `tavily-python` directly) |
| Search provider | Undisclosed | Tavily's own index |
| Phase 1d finding: UTM | No utm_source | No utm_source |

Tavily's structured output (url + content per result) makes citations easier to
include in the final memo. The `write` node can instruct the LLM to "cite sources by
company/publication name" because the URLs are explicitly in the search_results state.

**Note on langchain-community:** The initial implementation used
`langchain_community.tools.TavilySearchResults`. LangChain has deprecated
`langchain-community` in favor of standalone integration packages. Using
`from tavily import TavilyClient` directly is simpler, has no deprecation warning,
and removes an unnecessary dependency layer.

---

## 6. Thread ID is run identity — design it intentionally

LangGraph uses the `thread_id` in the config to identify which checkpoint to load:
```python
config = {"configurable": {"thread_id": "hinge-health-2026-07-21"}}
```

If you run the same company on the same day with the same thread_id, LangGraph
resumes from the existing checkpoint rather than starting a new run. This is the
correct behavior for the `--resume` use case but the wrong behavior when you want a
fresh run on the same day.

**Fix:** `--fresh` generates a unique thread_id suffix:
```python
suffix = f"-{int(date.today().toordinal())}" if fresh else ""
thread_id = f"{slug}-{date.today().isoformat()}{suffix}"
```

For production agents, thread_id design matters:
- **Per-request ID** (UUID): every invocation is independent, no resume
- **Per-topic + date** (this pattern): one canonical run per topic per day, resumable
- **Per-user + session**: multi-turn conversation continuity

The right choice depends on whether resumability or isolation is more important.

---

## 7. LangSmith tracing: what you actually get

With `LANGSMITH_TRACING=true` and a valid API key, every `app.invoke()` call sends a
trace to LangSmith automatically — no code changes required.

Each trace shows:
- The full graph execution path (which nodes ran, in what order)
- Input and output state at each node boundary
- Token counts and latency per LLM call
- The exact prompts sent to the model (including injected state values)

This is qualitatively different from Phase 1a/1c logging, where you'd add `print()`
statements or parse tool call logs. LangSmith gives you a structured, searchable,
replayable record of every run. You can click a prior run, see the exact analysis
that was synthesized, and compare it to a fresh run to understand what changed.

The trace URL format: `https://smith.langchain.com/projects/{project_name}`
Navigate to the project and click any run to see the full trace.

**Note:** LangSmith tracing adds ~100–200ms of latency per node due to the async
write to the LangSmith API. For a 5-node graph running 5 searches + 3 LLM calls,
this is negligible. For a high-frequency agent with hundreds of short nodes per
second, it would matter.

---

## Phase 1 vs Phase 2: What changed

| Concern | Phase 1a/1c (linear loop) | Phase 2a (LangGraph graph) |
|---------|--------------------------|---------------------------|
| Flow definition | Implicit (while loop + tool dispatch) | Explicit (named nodes + edges) |
| State | Message accumulation list | Typed dict with named fields |
| Checkpointing | None (crash = start over) | PostgresSaver (crash = resume) |
| Human interaction | Not supported | `interrupt_before` + `update_state` |
| Observability | Print statements / log parsing | LangSmith structured traces |
| Testability | Mock the full API loop | Unit test individual nodes |
| Parallelism | `asyncio.gather` in code | Parallel edges in graph |
| Resume | Not possible | `app.invoke(None, config=config)` |

The graph model adds overhead upfront (state schema, node design) but pays back in
observability, recoverability, and composability. For a one-shot script, Phase 1a is
fine. For anything that runs repeatedly, handles failures, or involves human oversight,
Phase 2a's architecture is the right foundation.
