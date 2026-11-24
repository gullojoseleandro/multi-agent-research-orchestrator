import asyncio
import unittest

from graph import build_graph, run_query
from supervisor import RouteDecision


class ScriptedRouter:
    def __init__(self, routes: list[str]) -> None:
        self.routes = iter(routes)
        self.calls: list[dict] = []

    async def decide(self, state: dict) -> RouteDecision:
        self.calls.append(state)
        return RouteDecision(next_agent=next(self.routes), reason="offline test")


class GraphTests(unittest.TestCase):
    def test_research_analysis_and_final_synthesis(self) -> None:
        router = ScriptedRouter(["research", "analysis", "finish"])
        result = asyncio.run(
            run_query("Investigate INC-104 and calculate the p95 latency increase", router)
        )

        self.assertEqual([item["agent"] for item in result["contributions"]], ["research", "analysis"])
        self.assertEqual(result["analysis"]["percent_change"], 50.0)
        self.assertEqual(result["analysis"]["source_id"], "INC-104")
        self.assertIn("50.0%", result["answer"])
        self.assertIn("INC-104", result["answer"])
        self.assertEqual(result["next_agent"], "finish")
        self.assertEqual(len(router.calls), 3)

    def test_supervisor_rejects_premature_finish(self) -> None:
        router = ScriptedRouter(["finish", "finish", "finish"])
        result = asyncio.run(run_query("Investigate INC-104", router))

        self.assertEqual([item["agent"] for item in result["contributions"]], ["research", "analysis"])
        self.assertIn("INC-104", result["answer"])
        self.assertEqual(result["supervisor_steps"], 3)

    def test_bounded_unknown_query(self) -> None:
        router = ScriptedRouter(["research", "research", "research", "research", "research", "research"])
        result = asyncio.run(run_query("Investigate INC-999", router))

        self.assertEqual(result["supervisor_steps"], 5)
        self.assertIn("could not verify", result["answer"].lower())
        self.assertEqual(len(router.calls), 4)

    def test_supervisor_can_request_refinement(self) -> None:
        router = ScriptedRouter(["research", "analysis", "research", "analysis"])
        result = asyncio.run(run_query("Investigate INC-104", router))

        self.assertEqual(
            [item["agent"] for item in result["contributions"]],
            ["research", "analysis", "research", "analysis"],
        )
        self.assertEqual(result["analysis"]["percent_change"], 50.0)
        self.assertEqual(result["decisions"][2]["selected"], "research")

    def test_mermaid_contains_all_nodes(self) -> None:
        graph = build_graph(ScriptedRouter([]))
        mermaid = graph.get_graph().draw_mermaid()
        for node in ("supervisor", "research", "analysis", "final"):
            self.assertIn(node, mermaid)
