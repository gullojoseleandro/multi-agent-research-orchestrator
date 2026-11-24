import asyncio
import re

from langchain_core.tools import tool

from state import OrchestratorState


@tool
def calculate_percent_change(baseline: float, current: float) -> float:
    """Calculate the percentage change from a nonzero baseline to a current measurement."""
    if baseline <= 0:
        raise ValueError("Baseline must be greater than zero")
    return round((current - baseline) / baseline * 100, 1)


def _metric(text: str, name: str) -> float | None:
    match = re.search(rf"(?m)^\s*{re.escape(name)}\s*:\s*(\d+(?:\.\d+)?)\s*$", text)
    return float(match.group(1)) if match else None


async def analysis_node(state: OrchestratorState) -> dict:
    """Extract measurements from research evidence and calculate a checked result."""
    candidates = []
    for report in state["reports"]:
        baseline = _metric(report["text"], "baseline_p95_ms")
        current = _metric(report["text"], "current_p95_ms")
        if baseline is not None and current is not None:
            candidates.append((report["source_id"], baseline, current))

    if not candidates:
        return {
            "analysis": None,
            "contributions": [{"agent": "analysis", "summary": "No complete measurements in research evidence", "source_ids": []}],
        }
    if len({(baseline, current) for _, baseline, current in candidates}) != 1:
        return {
            "analysis": None,
            "contributions": [{"agent": "analysis", "summary": "Conflicting measurements across reports", "source_ids": [item[0] for item in candidates]}],
        }

    source_id, baseline, current = candidates[0]
    try:
        change = await asyncio.to_thread(calculate_percent_change.invoke, {"baseline": baseline, "current": current})
    except ValueError:
        return {
            "analysis": None,
            "contributions": [{"agent": "analysis", "summary": "Invalid baseline measurement", "source_ids": [source_id]}],
        }
    return {
        "analysis": {"source_id": source_id, "baseline_ms": baseline, "current_ms": current, "percent_change": change},
        "contributions": [{"agent": "analysis", "summary": f"Computed p95 change: {change}%", "source_ids": [source_id]}],
    }
