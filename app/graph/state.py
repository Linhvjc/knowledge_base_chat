from typing import List, TypedDict


class GraphState(TypedDict):
    """
    Đại diện cho trạng thái của graph.

    Attributes:
        question: Câu hỏi của người dùng.
        context: Ngữ cảnh được lấy từ vector store.
        response: Câu trả lời do AI tạo ra.
        retrieved_docs: Toàn bộ thông tin các document được lấy về.
    """

    question: str
    context: str
    response: str
    retrieved_docs: List[dict]
