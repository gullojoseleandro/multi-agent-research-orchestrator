import asyncio
import unittest

from agents.analyst_agent import analysis_node, calculate_percent_change
from agents.research_agent import search_reports


class SpecialistTests(unittest.TestCase):
    def test_research_queries_local_database(self) -> None:
        reports = search_reports.invoke({"query": "Investigate INC-104"})
        self.assertEqual([report["source_id"] for report in reports], ["INC-104"])
        self.assertEqual(search_reports.invoke({"query": "Investigate INC-999"}), [])

    def test_analysis_rejects_conflicting_evidence(self) -> None:
        reports = [
            {"source_id": "A", "path": "a.md", "text": "baseline_p95_ms: 240\ncurrent_p95_ms: 360\n"},
            {"source_id": "B", "path": "b.md", "text": "baseline_p95_ms: 240\ncurrent_p95_ms: 400\n"},
        ]
        output = asyncio.run(analysis_node({"reports": reports}))
        self.assertIsNone(output["analysis"])
        self.assertIn("Conflicting", output["contributions"][0]["summary"])

    def test_calculation_rejects_zero_baseline(self) -> None:
        with self.assertRaises(ValueError):
            calculate_percent_change.invoke({"baseline": 0, "current": 100})
