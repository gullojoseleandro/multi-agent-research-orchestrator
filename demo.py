"""Deterministic offline route provider for a reproducible delegation demo."""

from state import OrchestratorState
from supervisor import RouteDecision


class OfflineDemoRouter:
    async def decide(self, state: OrchestratorState) -> RouteDecision:
        if not state["reports"]:
            return RouteDecision(next_agent="research", reason="Evidence is required")
        if state.get("analysis") is None:
            return RouteDecision(next_agent="analysis", reason="Calculate from retrieved evidence")
        return RouteDecision(next_agent="finish", reason="Source-backed calculation is complete")
