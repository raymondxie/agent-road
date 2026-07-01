# Phase 1d Findings — Week-Long Parallel Run

Running the same news briefing agent every day for 7 days using both the raw
Anthropic API (Phase 1a pattern) and the OpenAI Agents SDK (Phase 1c pattern).
Comparing cost, latency, quality, and operational behavior.

---

## Run Log

| Date | Anthropic latency | OpenAI latency | Anthropic tokens (in/out/cache) | Anthropic searches | OpenAI searches | Notes |
|------|-------------------|----------------|----------------------------------|-------------------|-----------------|-------|
| 2026-06-30 | 67.5s | 20.5s | 23352 / 3190 / 4186 | 3 | 1 | First run; both verified grounded |
| 2026-07-01 | 67.7s | 20.4s | 33559 / 2999 / 26171 | 5 | 1 | Cache hit 78% of input; LaunchAgent SSL fix |
| 2026-07-02 | | | | | | |
| 2026-07-03 | | | | | | |
| 2026-07-04 | | | | | | |
| 2026-07-05 | | | | | | |
| 2026-07-06 | | | | | | |

---

## Operational Findings

**Day 1 (Jun 30) — Netskope SSL failure in launchd environment**
Both agents failed when triggered via LaunchAgent (`launchctl start`) with
`SSL: CERTIFICATE_VERIFY_FAILED`. Root cause: launchd runs in a clean environment
that doesn't inherit the system keychain trust for the Netskope TLS proxy. Fix:
add `SSL_CERT_FILE=/private/etc/netskope/netskope-cert-bundle.pem` to `phase-1d/.env`,
which `run_daily.sh` sources before running the agents.

**Day 1 — AgentHooks doesn't instrument hosted tools**
`AgentHooks.on_tool_start` never fires for `WebSearchTool` (a server-side hosted
tool). It only fires for `@function_tool` decorated functions. Web search call
counts must be read from `result.new_items` by checking
`raw_item.type == "web_search_call"` after the run completes.

**Day 2 (Jul 1) — Cache warming visible in token counts**
Anthropic's `cache_read_input_tokens` jumped from 4,186 on day 1 to 26,171 on
day 2 (~78% cache hit rate). The system prompt (marked `cache_control: ephemeral`)
is being reused across turns within a run, not across days — the high cache read
reflects the multi-turn nature of Anthropic's search loop (5 turns on day 2).

**Latency pattern — Anthropic is search-round-trip bound**
Anthropic runs ~68s consistently regardless of story count. Each web search is a
separate API turn, so 5 searches = 5+ round trips. OpenAI's `WebSearchTool` runs
server-side and returns results within the same API call, keeping latency flat at
~20s even with the same number of stories.

---

## Quality Comparison

After 7 runs, compare a few dimensions:

**Completeness** — Both agents covered all three sections on both days. ✅

**Attribution accuracy** — Anthropic: named sources with dates, no raw URLs. OpenAI:
inline clickable URLs with domain visible — easier to verify at a glance. One
formatting hiccup on day 1: OpenAI emitted `:briefcase:` as literal text instead
of rendering the emoji.

**Formatting consistency** — Anthropic's structure (h3, `---` dividers, editorial
prose) was identical across both days. OpenAI's structure varied slightly (h3 day 1
vs h4 day 2, emoji rendering inconsistency).

**Story selection** — Major stories overlapped (Comcast split, Five Eyes AI warning,
SCOTUS birthright citizenship). Divergence on the edges: Anthropic picked World Cup
heat wave; OpenAI picked SpaceX/Anthropic IPO angle. Both agents self-referentially
reported Anthropic's Claude Sonnet 5 launch on July 1.

Story overlap/divergence is driven by two distinct layers:

*Retrieval strategy (primary driver).* Verified by instrumentation on July 1:

Anthropic issues **3 targeted queries, one per section**:
```
"top business news today July 1 2026"
"top technology news today July 1 2026"
"top world news today July 1 2026"
```
Each query returns ~7–8 URLs. Total source pool: ~22 URLs across CNN, Bloomberg,
CNBC, Yahoo Finance, NPR, Fox News, NBC News, TechCrunch, Al Jazeera, and others.
The model synthesizes prose from these — raw URLs never appear in the briefing output.
Search provider not disclosed by Anthropic; no `utm_source` parameter in result URLs.

OpenAI issues **1 broad query**:
```
"top business news July 1 2026"
```
URLs in OpenAI briefing output carry `?utm_source=openai` — this is Bing (Microsoft's
OpenAI partnership routes web searches through Bing, which tags results with this
parameter). The model then covers all three sections from the single result set,
selecting across business, tech, and world stories from whatever Bing surfaced.

This directly explains the pattern: stories both agents picked are those covered
everywhere (Comcast, SCOTUS, Five Eyes) — any query on that day surfaces them.
Stories only one agent picked are those reachable only via targeted queries
(Anthropic: NPR's World Cup heat wave story via the world-events query; OpenAI: the
SpaceX/AI IPO angle from Bing's top result set for the broad query).

**Note on date injection:** Without an explicit date in the prompt, GPT-4o defaults
to its training cutoff when formulating search queries (observed: queried
"top tech news October 13 2023" in a dateless diagnostic). Both production agents
inject today's date explicitly (`today's ({today}) top news`) to prevent this.

*Editorial judgment (secondary driver).* Even when both agents retrieve the same raw
material, the model decides which stories to include and how to frame them. Claude
and GPT-4o have different training-based priors about newsworthiness. On July 1,
both surfaced the Anthropic Sonnet 5 launch — Claude framed it as a product release
story; GPT-4o framed it in the context of upcoming AI company IPOs.

**Implication:** Search count isn't just a cost/latency number — it's a proxy for
coverage breadth. The run log's search count column is actually measuring editorial
diversity. Anthropic's 3 section-specific queries against an undisclosed provider
produce a broader and more varied source pool; OpenAI's 1 Bing query is faster and
cheaper but anchors selection to whatever Bing's top results are for a single broad
query. This is a deliberate design tradeoff, not a quality gap.

**Summary depth** — Anthropic writes longer, more contextual summaries (~3 sentences,
editorial framing). OpenAI writes shorter, punchier summaries (1–2 sentences) with
inline URLs. Neither is objectively better — Anthropic is more readable offline;
OpenAI is more verifiable.

---

## Cost Estimate

Anthropic (claude-sonnet-4-6) pricing:
- Input: $3.00 / 1M tokens
- Output: $15.00 / 1M tokens
- Cache read: $0.30 / 1M tokens

OpenAI (gpt-4o) pricing:
- Input: $2.50 / 1M tokens
- Output: $10.00 / 1M tokens
- Web search: $0.03 / call (approximate)

Fill in weekly totals from run-log.txt after day 7.

---

## Key Findings

Write final synthesis here after the week completes — feed directly into the
public writeup.
