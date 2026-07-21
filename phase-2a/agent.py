#!/usr/bin/env python3
"""Phase 2a: research-analyst agent built on LangGraph.

Graph: plan → search → analyze → [human interrupt] → write
Persistence: PostgresSaver (resume across sessions via thread_id)
Tracing: LangSmith (set LANGSMITH_API_KEY + LANGSMITH_TRACING=true)

Usage:
    python agent.py "Stripe"
    python agent.py "Stripe" --resume   # resume a prior interrupted run
"""

import operator
import os
import sys
from datetime import date
from pathlib import Path
from typing import Annotated

import psycopg
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, StateGraph
from tavily import TavilyClient
from typing_extensions import TypedDict

# ── Models and tools ──────────────────────────────────────────────────────────

llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0, max_tokens=4096)
tavily = TavilyClient()


# ── State ─────────────────────────────────────────────────────────────────────

class ResearchState(TypedDict):
    company: str
    queries: list[str]
    search_results: Annotated[list[str], operator.add]
    analysis: str
    human_feedback: str
    memo: str
    output_path: str


# ── Nodes ─────────────────────────────────────────────────────────────────────

def plan(state: ResearchState) -> dict:
    print(f"  → Planning research queries for {state['company']}...")
    today = date.today().isoformat()
    response = llm.invoke(
        f"You are a research analyst. Today's date is {today}. "
        f"Generate exactly 5 targeted search queries to research {state['company']} as a company.\n"
        f"Cover: (1) business model and revenue, (2) scale and financials, "
        f"(3) main competitors, (4) recent news in the last 60 days as of {today}, (5) key risks.\n"
        f"Make sure the news query explicitly references {today[:7]} or recent months to get current results.\n"
        f"Return only the 5 queries, one per line, no numbering or bullets."
    )
    queries = [q.strip() for q in response.content.strip().splitlines() if q.strip()][:5]
    for q in queries:
        print(f"    • {q}")
    return {"queries": queries}


def search(state: ResearchState) -> dict:
    print(f"  → Running {len(state['queries'])} searches...")
    results = []
    for query in state["queries"]:
        response = tavily.search(query, max_results=5)
        hits = response.get("results", [])
        block = f"Query: {query}\n" + "\n".join(
            f"[{h['url']}]\n{h['content']}" for h in hits
        )
        results.append(block)
        print(f"    ✓ {query[:60]}")
    return {"search_results": results}


def analyze(state: ResearchState) -> dict:
    print("  → Synthesizing findings...")
    context = "\n\n---\n\n".join(state["search_results"])
    response = llm.invoke(
        f"You are a senior research analyst. Based on the following search results "
        f"about {state['company']}, write a structured analysis.\n\n"
        f"Cover these five areas, clearly labeled:\n"
        f"1. Business Overview — what they do, revenue model, scale\n"
        f"2. Competitive Position — main rivals, market share, differentiation\n"
        f"3. Recent Developments — notable news from the past 60 days\n"
        f"4. Risks & Opportunities — top 2-3 each\n"
        f"5. Preliminary Verdict — one paragraph, your read on the company\n\n"
        f"Search results:\n{context}"
    )
    return {"analysis": response.content}


def write(state: ResearchState) -> dict:
    print("  → Writing analyst memo...")
    feedback = state.get("human_feedback", "").strip()
    feedback_section = f"\n\nAnalyst additions: {feedback}" if feedback else ""

    response = llm.invoke(
        f"Write a professional analyst memo about {state['company']}.\n\n"
        f"Research findings:\n{state['analysis']}"
        f"{feedback_section}\n\n"
        f"Format as a proper analyst memo in markdown with these sections:\n"
        f"- Executive Summary (3-5 bullet points)\n"
        f"- Business Overview\n"
        f"- Competitive Landscape\n"
        f"- Recent Developments\n"
        f"- Risk / Opportunity Matrix (table)\n"
        f"- Analyst Verdict\n\n"
        f"Be specific and factual. Cite sources by company/publication name where relevant."
    )
    memo = response.content
    slug = state["company"].lower().replace(" ", "-")
    output_path = f"phase-2a/memos/{date.today().isoformat()}-{slug}.md"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(memo)
    return {"memo": memo, "output_path": output_path}


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(ResearchState)
    g.add_node("plan", plan)
    g.add_node("search", search)
    g.add_node("analyze", analyze)
    g.add_node("write", write)
    g.set_entry_point("plan")
    g.add_edge("plan", "search")
    g.add_edge("search", "analyze")
    g.add_edge("analyze", "write")
    g.add_edge("write", END)
    return g


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]
    resume = "--resume" in args
    fresh = "--fresh" in args
    company_args = [a for a in args if a not in ("--resume", "--fresh")]

    if company_args:
        company = " ".join(company_args)
    else:
        company = input("Company to research: ").strip()

    conn_string = os.environ["DATABASE_URL"]
    with psycopg.connect(conn_string, autocommit=True) as conn:
        checkpointer = PostgresSaver(conn)
        checkpointer.setup()

        app = build_graph().compile(
            checkpointer=checkpointer,
            interrupt_before=["write"],
        )

        slug = company.lower().replace(" ", "-")
        suffix = f"-{int(date.today().toordinal())}" if fresh else ""
        thread_id = f"{slug}-{date.today().isoformat()}{suffix}"
        config = {"configurable": {"thread_id": thread_id}}

        if resume:
            print(f"\nResuming thread: {thread_id}")
            snapshot = app.get_state(config)
            print("\n" + "=" * 60)
            print("CURRENT ANALYSIS")
            print("=" * 60)
            print(snapshot.values.get("analysis", "(no analysis yet)"))
        else:
            print(f"\nResearching {company}  [thread: {thread_id}]")
            print("-" * 60)
            app.invoke(
                {"company": company, "queries": [], "search_results": [],
                 "analysis": "", "human_feedback": "", "memo": "", "output_path": ""},
                config=config,
            )
            snapshot = app.get_state(config)
            print("\n" + "=" * 60)
            print("ANALYSIS PREVIEW — review before writing memo")
            print("=" * 60)
            print(snapshot.values.get("analysis", ""))

        print("=" * 60)
        feedback = input(
            "\nAdditional context or analyst notes (press Enter to proceed): "
        ).strip()
        if feedback:
            app.update_state(config, {"human_feedback": feedback})

        print()
        final = app.invoke(None, config=config)
        print(f"\n✓ Memo saved → {final['output_path']}")

        project = os.environ.get("LANGSMITH_PROJECT", "agent-road-phase-2a")
        if os.environ.get("LANGSMITH_TRACING") == "true":
            print(f"✓ Traces    → https://smith.langchain.com/projects/{project}")


if __name__ == "__main__":
    main()
