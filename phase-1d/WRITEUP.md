# Phase 1d Writeup — A Week of Running Two AI Agents in Parallel

## What I built

The same news briefing agent, implemented twice — once using the raw Anthropic API
(`anthropic.messages.create` in a manual loop) and once using the OpenAI Agents SDK
(`Runner.run()`). Both agents fetch today's top news across business, technology, and
world events, then write a formatted markdown briefing to disk.

I ran both every day for a week via a macOS LaunchAgent scheduled at 11:30am. Each
run produces two dated files: `YYYY-MM-DD-anthropic.md` and `YYYY-MM-DD-openai.md`,
each with a metadata table appended (tokens, latency, search count).

The goal: not to find a winner, but to observe how two different execution models
behave under the same real-world task, every day, unattended.

---

## The week in numbers

| Date | Anthropic latency | OpenAI latency | Anthropic searches | OpenAI searches |
|------|-------------------|----------------|--------------------|-----------------|
| Jun 30 | 67.5s | 20.5s | 3 | 1 |
| Jul 1 | 79.5s | 25.2s | 5 | 1 |
| Jul 2 | 106.1s | 29.3s | 6 | 1 |
| Jul 3–5 | FAILED | FAILED | — | — |
| Jul 6 | 81.4s | 18.1s | 5 | 1 |
| Jul 7 | 68.8s | 31.0s | 3 | 1 |
| Jul 8 | 79.1s | 22.0s | 5 | 1 |
| Jul 9 | 88.1s | 23.1s | 5 | 1 |

7 days of data. 3 failures (Jul 3–5, Netskope SSL issue over the July 4th weekend —
more on that below). Both agents produced complete, grounded briefings on every
successful run.

---

## Finding 1: Latency is architecture, not configuration

OpenAI is consistently 3x faster. Anthropic runs 68–106 seconds; OpenAI runs 18–31
seconds. No amount of tuning closes this gap because the difference isn't in the
model — it's in how search works.

The Anthropic agent issues 3–6 web searches as separate API turns. Each search is a
round trip: model calls `web_search`, API executes it server-side, results come back,
model processes them, then decides whether to search again. 5 searches = 5+ API
round trips. Latency scales linearly with search count.

OpenAI's `WebSearchTool` executes inside a single API call. The model calls the tool,
the results come back in the same response, and the model continues. No round trips.
This is why OpenAI's latency is flat at 18–31 seconds regardless of the news day.

If you're building a latency-sensitive agent (real-time assistant, webhook handler,
anything user-facing), this is a structural constraint to know before you commit to
an architecture.

---

## Finding 2: Search count is editorial breadth, not just cost

I expected search count to be a cost and latency metric. It's also a content metric.

Anthropic issues one targeted query per section:
```
"top business news today July 1 2026"
"top technology news today July 1 2026"
"top world news today July 1 2026"
```

OpenAI issues one broad query:
```
"top business news July 1 2026"
```

(Confirmed by instrumenting both agents and logging the exact queries and result URLs.
OpenAI uses Bing — every result URL carries `?utm_source=openai`. Anthropic's provider
is undisclosed — no UTM parameters in result URLs.)

More queries means more diverse source pool. Anthropic's 3 queries return ~22 URLs
spanning CNN, Bloomberg, CNBC, NPR, TechCrunch, Al Jazeera, and others. OpenAI's
single Bing query returns whatever ranks highest for one broad term.

The result: both agents always covered the same top headlines (the stories appearing
everywhere). Divergence happened at the edges — stories only reachable via a
targeted section query. On July 1, Anthropic covered NPR's World Cup heat wave piece;
OpenAI covered the SpaceX/AI IPO angle. Neither picked the other's story because
neither issued the query that would have surfaced it.

Search count is a proxy for coverage breadth. When you see "1 search vs 5 searches,"
you're not just seeing a cost tradeoff — you're seeing a decision about how much of
the news ecosystem the agent is allowed to see.

---

## Finding 3: Production scheduling reveals infrastructure you forgot about

Running `python agent.py` locally, everything works. Running via launchd at 11:30am
daily surfaces two things you'd never encounter in development:

**Netskope and launchd don't agree on SSL.** launchd runs agents in a clean
environment — it doesn't inherit your shell's keychain trust. Our corporate TLS
proxy (Netskope) requires its CA cert to be trusted explicitly. In a terminal
session this is handled automatically. In launchd it isn't. Both agents failed with
`SSL: CERTIFICATE_VERIFY_FAILED` until I added
`SSL_CERT_FILE=/private/etc/netskope/netskope-cert-bundle.pem` to the `.env` file
that the run script sources.

**Holiday weekends are a different network.** Even after fixing the SSL issue, Jul
3–5 failed with the same error. The cert file hadn't changed. The most likely
explanation: Netskope's proxy configuration changes when most of the company is
offline — different routing, cert rotation, or edge behavior during reduced traffic.
It self-resolved on Jul 6 with zero code changes. Agents running unattended need
retry logic and failure alerting. A silent failure at 11:30am that you only discover
when checking the briefings folder is not an acceptable failure mode in production.

---

## What surprised me

**The hook observability gap.** OpenAI's `AgentHooks.on_tool_start` fires for
`@function_tool` functions but not for hosted tools like `WebSearchTool`. Web search
calls don't trigger the hook — they're invisible to the instrumentation layer. I had
to inspect `result.new_items` post-run and look for `raw_item.type == "web_search_call"`
to count them. If you're building observability dashboards around hook data, hosted
tools are a blind spot.

**Date injection is required, not optional.** Without an explicit date in the prompt,
GPT-4o uses its training cutoff as "today." In a diagnostic run without a date,
it searched for "top tech news October 13 2023." Both production agents inject the
date explicitly: `"Search for today's ({today}) top news..."`. This one line is
the difference between grounded results and confident hallucination.

**The briefings are genuinely different.** I expected near-identical output. The
story selection diverges daily on the edges, and the framing diverges even when both
agents cover the same story. On July 1, both reported Anthropic's Claude Sonnet 5
launch — Claude framed it as a product release, GPT-4o framed it as context for
upcoming AI company IPOs. Same fact, different angle. The model's editorial judgment
is a meaningful variable.

---

## What I'd change for production

1. **Retry with backoff on SSL errors.** Three consecutive daily failures went
   unnoticed until I checked manually. `run_daily.sh` should retry both agents
   once after a 60-second wait and send an alert (email, Slack) on persistent failure.

2. **Track OpenAI token counts.** The OpenAI Agents SDK doesn't expose token usage
   as cleanly as the raw Anthropic API. I'd need to sum usage across `result.raw_responses`
   to get accurate cost data. Without it, I can only estimate.

3. **Version the prompt.** Both agents ran the same instructions for 7 days. If I
   changed the format or sections mid-run, comparing day 1 to day 7 would be
   meaningless. Prompt version should be in the metadata block.

4. **Store raw search results separately.** Right now the agent writes the synthesized
   briefing but discards the raw search results. Storing them would let me audit
   attribution accuracy and trace exactly which source each story came from.

---

## Summary

Two agents. Same task. Seven days. The Anthropic agent is slower (3–6 API round
trips per run), searches more specifically (one query per section), draws from a
broader source pool, and writes longer editorial prose. The OpenAI agent is faster
(one server-side search), queries Bing once broadly, and writes shorter summaries
with inline URLs.

Neither is better. They reflect the tradeoffs their architectures make: Anthropic
optimizes for coverage and depth; OpenAI optimizes for speed and cost. The interesting
part wasn't the comparison — it was what running them unattended for a week revealed
about the production gap between `python agent.py` and an agent that actually runs.
