import operator
from typing import Annotated, Literal, NotRequired, TypedDict

from langgraph.graph import MessagesState


class Contribution(TypedDict):
    agent: Literal["research", "analysis"]
    summary: str
    source_ids: list[str]


class DecisionRecord(TypedDict):
    step: int
    requested: Literal["research", "analysis", "finish"]
    selected: Literal["research", "analysis", "finish"]
    reason: str


class ResearchReport(TypedDict):
    source_id: str
    path: str
    text: str


class AnalysisReport(TypedDict):
    source_id: str
    baseline_ms: float
    current_ms: float
    percent_change: float


class OrchestratorState(MessagesState):
    query: str
    reports: list[ResearchReport]
    analysis: NotRequired[AnalysisReport | None]
    contributions: Annotated[list[Contribution], operator.add]
    decisions: Annotated[list[DecisionRecord], operator.add]
    next_agent: Literal["research", "analysis", "finish"]
    supervisor_steps: int
    answer: str
