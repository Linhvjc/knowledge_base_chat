from __future__ import annotations

from typing import Any
from typing import TypedDict


class GraphState(TypedDict):
    question: str
    context: str
    response: str
    retrieved_docs: list[dict[str, Any]]
    chat_history: list[dict[str, str]]
