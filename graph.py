from typing import Literal

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from agents.analyst_agent import analysis_node
from agents.research_agent import research_node
from state import OrchestratorState
from supervisor import OpenAISupervisor, Router, supervisor_node


def route_after_supervisor(state: OrchestratorState) -> Literal["research", "analysis", "final"]:
    return "final" if state["next_agent"] == "finish" else state["next_agent"]


async def final_node(state: OrchestratorState) -> dict:
    analysis = state.get("analysis")
    source = next((report for report in state["reports"] if analysis and report["source_id"] == analysis["source_id"]), None)
    if analysis and source:
        change = analysis["percent_change"]
        direction = "increase" if change > 0 else "decrease" if change < 0 else "no change"
        answer = (
            f"{analysis['source_id']}: p95 latency changed from {analysis['baseline_ms']:g} ms "
            f"to {analysis['current_ms']:g} ms ({abs(change):.1f}% {direction}). "
            f"Source: {source['path']}."
        )
    else:
        answer = "I could not verify a source-backed calculation from the available reports."
    return {"answer": answer, "next_agent": "finish"}


def build_graph(router: Router):
    builder = StateGraph(OrchestratorState)

    async def supervise(state: OrchestratorState) -> dict:
        return await supervisor_node(state, router)

    builder.add_node("supervisor", supervise)
    builder.add_node("research", research_node)
    builder.add_node("analysis", analysis_node)
    builder.add_node("final", final_node)
    builder.add_edge(START, "supervisor")
    builder.add_conditional_edges("supervisor", route_after_supervisor)
    builder.add_edge("research", "supervisor")
    builder.add_edge("analysis", "supervisor")
    builder.add_edge("final", END)
    return builder.compile()


async def run_query(query: str, router: Router | None = None) -> OrchestratorState:
    if not query.strip():
        raise ValueError("Query must not be empty")
    graph = build_graph(router or OpenAISupervisor())
    return await graph.ainvoke(
        {
            "messages": [HumanMessage(content=query)],
            "query": query,
            "reports": [],
            "analysis": None,
            "contributions": [],
            "decisions": [],
            "next_agent": "research",
            "supervisor_steps": 0,
            "answer": "",
        },
        config={"recursion_limit": 12},
    )
