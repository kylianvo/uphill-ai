"""Dev-only LangGraph Studio graph for Coach Chat. Never imported by the app.

Studio's UI is a hosted smith.langchain.com page talking to the local
`langgraph dev` server from the browser, so this must only ever run against a
local database with test users -- assert_local_dev enforces that."""

from collections.abc import Mapping
from typing import Any, TypedDict
from urllib.parse import urlparse
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

import db
from config import settings
from services import coach_context, coach_tools, kb_retrieval
from services.coach_graph import TurnState, build_graph
from services.coach_model import ChatMessage, FakeCoachModel, GeminiCoachModel, ModelEvent
from services.observability import Usage

LOCAL_DB_HOSTS = {"localhost", "127.0.0.1", "db"}


def assert_local_dev(environment: str, database_url: str) -> None:
    if (environment or "").lower() == "production":
        raise RuntimeError("LangGraph Studio refuses to run with ENVIRONMENT=production.")
    host = urlparse(database_url or "").hostname
    if host not in LOCAL_DB_HOSTS:
        raise RuntimeError(
            f"LangGraph Studio only runs against a local database (localhost/127.0.0.1/db); got host {host!r}."
        )


def load_studio_user_id(env: Mapping[str, str]) -> int:
    raw = env.get("STUDIO_USER_ID")
    if not raw:
        raise RuntimeError("Set STUDIO_USER_ID to a local test user's id before running `langgraph dev`.")
    user_id = int(raw)
    if db.get_user_by_id(user_id) is None:
        raise RuntimeError(f"STUDIO_USER_ID={user_id} does not exist in the local database.")
    return user_id


class CyclingFakeCoachModel(FakeCoachModel):
    """FakeCoachModel in explicit-rounds mode that restarts its script when it
    runs out, so repeated Studio runs against one module-level graph keep
    working. Each run consumes exactly two rounds: a get_week tool call, then a
    short reply."""

    def __init__(self) -> None:
        super().__init__(
            responses=[
                [ModelEvent(kind="tool_call", tool_call={"id": "studio-1", "name": "get_week", "args": {}})],
                [
                    ModelEvent(kind="text", text="(Studio fake model) Here is your week -- keep the easy days easy."),
                    ModelEvent(kind="usage", usage=Usage(input_tokens=0, output_tokens=0)),
                ],
            ]
        )

    async def stream(self, request):  # type: ignore[override]
        if self._cursor >= len(self.responses):
            self._cursor = 0
        async for event in super().stream(request):
            yield event


class StudioInput(TypedDict, total=False):
    question: str
    lang: str


def _make_prepare_node(user_id: int):
    def prepare(state: TurnState) -> dict[str, Any]:
        question = state.get("question") or ""
        thread = db.get_or_create_chat_thread(user_id)
        context = coach_context.build_chat_context(user_id=user_id, question=question, thread_id=thread["id"])
        if thread.get("summary"):
            context["summary"] = thread["summary"]
        prior = [
            ChatMessage(role="user" if m.get("role") == "user" else "assistant", content=m.get("content") or "")
            for m in (context.get("history") or [])
            if (m.get("content") or "").strip()
        ]
        return {
            "user_id": user_id,
            "thread_id": thread["id"],
            "request_id": str(uuid4()),
            "call_id": uuid4(),
            "lang": state.get("lang") or "en",
            "context": context,
            "messages": [*prior, ChatMessage(role="user", content=question)],
        }

    return prepare


def build_studio_graph(user_id: int, *, real_model: bool):
    if real_model:
        user = db.get_user_by_id(user_id) or {}
        api_key = user.get("gemini_api_key") or settings.GEMINI_API_KEY
        tools = coach_tools.build_tools(user_id=user_id, kb_api_key=api_key)
        model = GeminiCoachModel(api_key=api_key, tools=tools)

        def retrieve(q: str):
            return kb_retrieval.search_principles(query=q, api_key=api_key)
    else:
        tools = coach_tools.build_tools(user_id=user_id, kb_api_key="unused")
        model = CyclingFakeCoachModel()

        def retrieve(q: str):
            return []

    coach = build_graph(model=model, retrieve_fn=retrieve, tools=tools)

    workflow = StateGraph(TurnState, input_schema=StudioInput)
    workflow.add_node("prepare", _make_prepare_node(user_id))
    workflow.add_node("coach", coach)
    workflow.add_edge(START, "prepare")
    workflow.add_edge("prepare", "coach")
    workflow.add_edge("coach", END)
    return workflow.compile()
