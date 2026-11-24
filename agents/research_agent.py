import asyncio
import re
import sqlite3
from pathlib import Path

from langchain_core.tools import tool

from state import OrchestratorState, ResearchReport


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@tool
def search_reports(query: str) -> list[ResearchReport]:
    """Query a local SQLite FTS5 incident index for citable technical reports.

    Returns source IDs, relative paths, and exact source text. Use this before
    analyzing an incident; do not invent values that are absent from a report.
    """
    incident_ids = sorted(set(re.findall(r"INC-\d+", query.upper())))
    words = sorted(set(re.findall(r"[A-Za-z]{4,}", query.lower())))
    with sqlite3.connect(":memory:") as database:
        database.execute("CREATE VIRTUAL TABLE reports USING fts5(source_id UNINDEXED, path UNINDEXED, text)")
        for path in sorted(DATA_DIR.glob("*.md")):
            database.execute(
                "INSERT INTO reports(source_id, path, text) VALUES (?, ?, ?)",
                (path.stem.upper(), f"data/{path.name}", path.read_text(encoding="utf-8")),
            )
        if incident_ids:
            placeholders = ",".join("?" for _ in incident_ids)
            rows = database.execute(
                f"SELECT source_id, path, text FROM reports WHERE source_id IN ({placeholders}) ORDER BY source_id LIMIT 3",
                incident_ids,
            ).fetchall()
        elif words:
            expression = " OR ".join(f'"{word}"' for word in words)
            rows = database.execute(
                "SELECT source_id, path, text FROM reports WHERE reports MATCH ? ORDER BY bm25(reports) LIMIT 3",
                (expression,),
            ).fetchall()
        else:
            rows = []
    return [{"source_id": source_id, "path": path, "text": text} for source_id, path, text in rows]


async def research_node(state: OrchestratorState) -> dict:
    """Use only the search tool and return citable source material."""
    reports = await asyncio.to_thread(search_reports.invoke, {"query": state["query"]})
    source_ids = [report["source_id"] for report in reports]
    summary = f"Found {len(reports)} matching report(s): {', '.join(source_ids) or 'none'}"
    return {
        "reports": reports,
        "analysis": None,
        "contributions": [{"agent": "research", "summary": summary, "source_ids": source_ids}],
    }
