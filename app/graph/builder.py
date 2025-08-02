# /app/graph/builder.py
from langgraph.graph import StateGraph, END
from functools import partial
from sqlalchemy.ext.asyncio import AsyncSession

from .state import GraphState
from .nodes import retrieve_node, generate_node


def get_graph_runnable(db: AsyncSession):
    """
    Xây dựng và biên dịch graph, truyền session DB vào node retrieve.
    """
    workflow = StateGraph(GraphState)

    # Partial để "đóng gói" tham số db vào hàm node
    # LangGraph chỉ chấp nhận các node có 1 tham số là `state`
    retrieve_with_db = partial(retrieve_node, db=db)

    # Thêm các node vào graph
    workflow.add_node("retrieve", retrieve_with_db)
    workflow.add_node("generate", generate_node)

    # Định nghĩa luồng chạy của graph
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)

    # Biên dịch graph thành một đối tượng có thể chạy được
    return workflow.compile()
