import json
from typing import Literal, Protocol

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from state import OrchestratorState


MAX_SUPERVISOR_STEPS = 5


class RouteDecision(BaseModel):
    next_agent: Literal["research", "analysis", "finish"]
    reason: str = Field(min_length=1)


class Router(Protocol):
    async def decide(self, state: OrchestratorState) -> RouteDecision: ...


class OpenAISupervisor:
    def __init__(self, model_name: str = "gpt-4o-mini") -> None:
        model = ChatOpenAI(model=model_name, temperature=0)
        self.chain = ChatPromptTemplate.from_messages(
            [
                ("system", "You supervise two specialists. Choose research for missing or conflicting sources; choose analysis only after citable measurements exist; choose finish only when a source-backed calculation exists. Never invent evidence. A bounded graph guard may override your choice."),
                ("human", "Question: {query}\nResearch: {reports}\nAnalysis: {analysis}\nContributions: {contributions}\nSupervisor steps: {steps}"),
            ]
        ) | model.with_structured_output(RouteDecision)

    async def decide(self, state: OrchestratorState) -> RouteDecision:
        return await self.chain.ainvoke(
            {
                "query": state["query"],
                "reports": json.dumps([{"source_id": report["source_id"], "text": report["text"][:1200]} for report in state["reports"]]),
                "analysis": json.dumps(state.get("analysis")),
                "contributions": json.dumps(state["contributions"][-4:]),
                "steps": state["supervisor_steps"],
            }
        )


async def supervisor_node(state: OrchestratorState, router: Router) -> dict:
    steps = state["supervisor_steps"] + 1
    if steps >= MAX_SUPERVISOR_STEPS:
        route = "finish"
        requested = "finish"
        reason = "step limit reached"
    else:
        decision = await router.decide(state)
        route = decision.next_agent
        requested = route
        reason = decision.reason
        if not state["reports"]:
            route = "research"
        elif state.get("analysis") is None and route == "finish":
            route = "analysis"
    return {
        "next_agent": route,
        "supervisor_steps": steps,
        "decisions": [{"step": steps, "requested": requested, "selected": route, "reason": reason}],
    }
