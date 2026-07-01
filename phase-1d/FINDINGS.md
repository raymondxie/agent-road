# Phase 1d Findings — Week-Long Parallel Run

Running the same news briefing agent every day for 7 days using both the raw
Anthropic API (Phase 1a pattern) and the OpenAI Agents SDK (Phase 1c pattern).
Comparing cost, latency, quality, and operational behavior.

---

## Run Log

| Date | Anthropic latency | OpenAI latency | Anthropic tokens (in/out) | OpenAI searches | Notes |
|------|-------------------|----------------|---------------------------|-----------------|-------|
| 2026-06-30 | — | — | — | — | First run |
| 2026-07-01 | | | | | |
| 2026-07-02 | | | | | |
| 2026-07-03 | | | | | |
| 2026-07-04 | | | | | |
| 2026-07-05 | | | | | |
| 2026-07-06 | | | | | |

---

## Operational Findings

Record anything surprising about running both agents in production daily:
- Failures and how they manifested (API errors, rate limits, empty output)
- Differences in how each agent handles the same news day
- Reliability patterns across the week

---

## Quality Comparison

After 7 runs, compare a few dimensions:

**Completeness** — Does each agent cover all three sections (Business, Tech, World)?

**Attribution accuracy** — Are sources and dates real? Any hallucinated citations?

**Formatting consistency** — Does the emoji/section structure hold up across days?

**Story selection** — Do both agents pick the same top stories? When they differ, which is better?

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
