"""Print the Coach Chat LangGraph as a Mermaid diagram (rendered locally -- never
via mermaid.ink). Run from backend/: python -m scripts.draw_coach_graph [--no-tools] [--out FILE]"""

import argparse
import sys

from services import coach_tools
from services.coach_graph import build_graph
from services.coach_model import FakeCoachModel


def render_mermaid(with_tools: bool = True) -> str:
    # Tool executors are per-turn closures that only hit the DB when invoked, so a
    # dummy user id is safe for building the graph's structure.
    tools = coach_tools.build_tools(user_id=0, kb_api_key="unused") if with_tools else None
    graph = build_graph(model=FakeCoachModel(), retrieve_fn=lambda q: [], tools=tools)
    return graph.get_graph().draw_mermaid()


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the Coach Chat graph as Mermaid")
    parser.add_argument("--no-tools", action="store_true", help="Draw the linear no-API-key graph")
    parser.add_argument("--out", help="Write a Markdown file with a fenced mermaid block instead of stdout")
    args = parser.parse_args()
    diagram = render_mermaid(with_tools=not args.no_tools)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(f"```mermaid\n{diagram}\n```\n")
    else:
        sys.stdout.write(diagram)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
