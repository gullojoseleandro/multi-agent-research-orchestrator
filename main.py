import argparse
import asyncio
import json
import os

from dotenv import load_dotenv

from demo import OfflineDemoRouter
from graph import run_query
from supervisor import OpenAISupervisor


async def main() -> int:
    parser = argparse.ArgumentParser(description="Run the multi-agent incident research orchestrator.")
    parser.add_argument("--query", default="Investigate INC-104 and calculate the p95 latency increase")
    parser.add_argument("--offline", action="store_true", help="Use a deterministic local supervisor without an API key.")
    args = parser.parse_args()
    load_dotenv()

    if not args.offline and not os.getenv("OPENAI_API_KEY"):
        parser.error("OPENAI_API_KEY is required for the LLM supervisor; use --offline for the demo")
    router = OfflineDemoRouter() if args.offline else OpenAISupervisor(os.getenv("MODEL_NAME", "gpt-4o-mini"))
    result = await run_query(args.query, router)
    print(json.dumps({
        "question": args.query,
        "answer": result["answer"],
        "decisions": result["decisions"],
        "contributions": result["contributions"],
        "analysis": result.get("analysis"),
        "mode": "offline demo" if args.offline else "OpenAI supervisor",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
