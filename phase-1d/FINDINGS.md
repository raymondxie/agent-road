# Phase 1d Findings — Week-Long Parallel Run

Running the same news briefing agent every day for 7 days using both the raw
Anthropic API (Phase 1a pattern) and the OpenAI Agents SDK (Phase 1c pattern).
Comparing cost, latency, quality, and operational behavior.

---

## Run Log

| Date | Anthropic latency | OpenAI latency | Anthropic tokens (in/out/cache_read) | Anthropic searches | OpenAI searches | Notes |
|------|-------------------|----------------|--------------------------------------|-------------------|-----------------|-------|
| 2026-06-30 | 67.5s | 20.5s | 23352 / 3190 / 4186 | 3 | 1 | First run; both verified grounded |
| 2026-07-01 | 79.5s | 25.2s | 36077 / 3428 / 24181 | 5 | 1 | Cache read 67% of input |
| 2026-07-02 | 106.1s | 29.3s | 49882 / 4529 / 24615 | 6 | 1 | Highest token + latency day |
| 2026-07-03 | FAILED | FAILED | — | — | — | Netskope SSL (holiday weekend) |
| 2026-07-04 | FAILED | FAILED | — | — | — | Netskope SSL (July 4th) |
| 2026-07-05 | FAILED | FAILED | — | — | — | Netskope SSL; self-resolved next day |
| 2026-07-06 | 81.4s | 18.1s | 36874 / 3576 / 29748 | 5 | 1 | |
| 2026-07-07 | 68.8s | 31.0s | 25787 / 3013 / 4186 | 3 | 1 | Cache cold (low cache_read) |
| 2026-07-08 | 79.1s | 22.0s | 48720 / 3294 / 31039 | 5 | 1 | |
| 2026-07-09 | 88.1s | 23.1s | 37505 / 3759 / 29475 | 5 | 1 | |

**Totals (7 successful runs):**
- Anthropic input tokens: 258,127 — cost: ~$0.77
- Anthropic output tokens: 23,789 — cost: ~$0.36
- Anthropic cache read tokens: 147,390 — cost: ~$0.04
- Anthropic total: **~$1.17**
- OpenAI: token counts not tracked; estimated ~$0.05–0.08/run × 7 = **~$0.40–0.56**

---

## Operational Findings

**Day 1 (Jun 30) — Netskope SSL failure in launchd environment**
Both agents failed when triggered via LaunchAgent (`launchctl start`) with
`SSL: CERTIFICATE_VERIFY_FAILED`. Root cause: launchd runs in a clean environment
that doesn't inherit the system keychain trust for the Netskope TLS proxy. Fix:
add `SSL_CERT_FILE=/private/etc/netskope/netskope-cert-bundle.pem` to `phase-1d/.env`,
which `run_daily.sh` sources before running the agents.

**Days 3–5 (Jul 3–5) — SSL failures over the July 4th holiday weekend**
Despite the SSL fix, all three runs failed over the holiday weekend with the same
`CERTIFICATE_VERIFY_FAILED` error. The cert file existed and hadn't changed. Most
likely cause: Netskope's network configuration changes when many employees are
offline (different proxy routing, cert rotation, or VPN edge case). Self-resolved
on Jul 6 with no code changes. Lesson: TLS proxy environments are fragile during
network config changes; production agents need retry logic and failure alerting.

**Day 1 — AgentHooks doesn't instrument hosted tools**
`AgentHooks.on_tool_start` never fires for `WebSearchTool` (a server-side hosted
tool). It only fires for `@function_tool` decorated functions. Web search call
counts must be read from `result.new_items` by checking
`raw_item.type == "web_search_call"` after the run completes.

**Cache warming is within-run, not across-run**
Anthropic's `cache_read_input_tokens` varies unpredictably across days (4k on days
with 3 searches, 24–31k on days with 5–6 searches). It resets to baseline between
runs. The cache is reused across turns within a single run — as each search result
feeds into the next API call, prior context is served from cache. Days with more
searches accumulate more cacheable context, explaining the correlation.

**Latency scales with search count (Anthropic only)**
3 searches → ~68s. 5 searches → ~79–88s. 6 searches → ~106s. Each search is a
separate API round-trip, so latency is strictly search-count-bound. OpenAI's
WebSearchTool executes server-side within a single API call — latency is flat at
18–31s regardless of the news day.

---

## Quality Comparison

**Completeness** — Both agents covered all three sections (Business, Tech, World)
on every successful run. ✅

**Attribution accuracy** — Anthropic: named sources with dates, no raw URLs.
OpenAI: inline clickable URLs with `?utm_source=openai` — easier to verify at a
glance. One formatting hiccup on day 1: OpenAI emitted `:briefcase:` as literal
text instead of rendering the emoji.

**Formatting consistency** — Anthropic's structure (h3 headers, `---` dividers,
editorial prose) was nearly identical across all 7 runs. OpenAI varied slightly
(h3 vs h4, occasional emoji rendering inconsistency).

**Story selection** — Major headlines overlapped on every day (top 3–4 stories
covered by both). Divergence on edge stories. Explained by two layers:

*Retrieval strategy (primary driver).* Verified by instrumentation on July 1:

Anthropic issues **3 targeted queries, one per section**:
```
"top business news today July 1 2026"
"top technology news today July 1 2026"
"top world news today July 1 2026"
```
Each query returns ~7–8 URLs. Total source pool: ~22 URLs across CNN, Bloomberg,
CNBC, Yahoo Finance, NPR, Fox News, NBC News, TechCrunch, Al Jazeera, and others.
The model synthesizes prose from these — raw URLs never appear in the briefing.
Search provider not disclosed by Anthropic; no `utm_source` in result URLs.

OpenAI issues **1 broad query**:
```
"top business news July 1 2026"
```
URLs in OpenAI output carry `?utm_source=openai` — confirmed Bing (Microsoft's
OpenAI partnership routes searches through Bing, which tags results). The model
covers all three sections from a single result set.

Stories both agents always picked: those covered everywhere (top SCOTUS, major
corporate news, Five Eyes). Stories only one agent picked: those only reachable
via a targeted section query (Anthropic: NPR's World Cup heat wave, regional
stories; OpenAI: SpaceX/AI IPO angle from Bing's top result set).

**Search count is a proxy for coverage breadth**, not just a cost/latency metric.

*Editorial judgment (secondary driver).* Even with the same raw material, Claude
and GPT-4o frame the same story differently. On July 1, both surfaced the
Anthropic Sonnet 5 launch — Claude framed it as a product release; GPT-4o framed
it in the context of upcoming AI company IPOs.

**Note on date injection:** Without an explicit date in the prompt, GPT-4o uses
its training cutoff when formulating queries (observed: "top tech news October 13
2023" in a dateless diagnostic). Both production agents inject today's date
explicitly to prevent this.

**Summary depth** — Anthropic: ~3 sentences, editorial framing, no raw URLs.
OpenAI: 1–2 sentences, punchier, inline source URLs. Anthropic is more readable
offline; OpenAI is more verifiable.

---

## Cost Estimate

Anthropic (claude-sonnet-4-6):
- Input: $3.00 / 1M tokens → $0.774 for 258,127 tokens
- Output: $15.00 / 1M tokens → $0.357 for 23,789 tokens
- Cache read: $0.30 / 1M tokens → $0.044 for 147,390 tokens
- **Total: ~$1.17 for 7 runs (~$0.17/run avg)**

OpenAI (gpt-4o): token counts not tracked. Based on typical gpt-4o usage at
~20–30k tokens/run plus 1 Bing search call:
- **Estimated: ~$0.40–0.56 for 7 runs (~$0.06–0.08/run avg)**

OpenAI is roughly 2–3x cheaper per run than Anthropic for this task, primarily
because Anthropic issues more search calls and processes more total tokens.

---

## Key Findings

1. **Latency is architecture, not configuration.** Anthropic's multi-turn search
   loop is structurally slower than OpenAI's server-side tool. You can't tune
   your way to parity — they are different execution models.

2. **Search count is editorial breadth, not just cost.** More queries = more
   diverse source pool = more varied story selection. The tradeoff between
   Anthropic's 3-query approach and OpenAI's 1-query approach is really a
   tradeoff between coverage depth and cost/latency.

3. **Production scheduling surfaces infrastructure you forgot about.** Netskope,
   launchd's clean environment, holiday network changes — none of these exist in
   `python agent.py`. They only exist when the agent runs unattended.

4. **Hook observability has blind spots.** AgentHooks doesn't instrument hosted
   tools. If you're building dashboards or audits around hook data, hosted tools
   are invisible. You need post-run inspection of raw response items.

5. **Date injection is required, not optional.** LLMs use their training cutoff
   as "today" when the current date isn't in the prompt. For any time-sensitive
   agent, inject the date explicitly — or the agent silently queries the past.
