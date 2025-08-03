from typing import List, TypedDict, Dict, Any
from typing import List, TypedDict, Dict, Any


class GraphState(TypedDict):
    """
    Đại diện cho trạng thái của graph.
    """

    question: str
    context: str
    response: str
    retrieved_docs: List[Dict[str, Any]]
    # Thêm trường này để chứa lịch sử hội thoại
    chat_history: List[Dict[str, str]]
