from __future__ import annotations

from functools import partial

from langgraph.graph import END
from langgraph.graph import StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from .nodes import generate_node
from .nodes import retrieve_node
from .state import GraphState


def get_graph_runnable(db: AsyncSession):
    workflow = StateGraph(GraphState)

    retrieve_with_db = partial(retrieve_node, db=db)

    workflow.add_node('retrieve', retrieve_with_db)
    workflow.add_node('generate', generate_node)

    workflow.set_entry_point('retrieve')
    workflow.add_edge('retrieve', 'generate')
    workflow.add_edge('generate', END)

    return workflow.compile()
