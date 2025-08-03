# /app/services/chat_service.py
import time
import uuid
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator, List, Dict

from app.db.models import AuditLog
from app.graph.builder import get_graph_runnable
from app.schemas.schema import ChatInput


class ChatService:

    async def stream_chat(
        self, question: str, history: List[Dict[str, str]], db: AsyncSession
    ) -> AsyncGenerator[str, None]:
        """
        Xử lý chat, stream câu trả lời và ghi nhật ký.
        """
        start_time = time.time()
        chat_id = uuid.uuid4()

        # Lấy graph runnable đã được biên dịch với session DB hiện tại
        graph = get_graph_runnable(db)

        # Dùng `astream` để nhận các cập nhật trạng thái từ graph
        full_response = ""
        retrieved_docs = []

        # Đầu vào ban đầu cho graph
        initial_input = {"question": question, "chat_history": history}

        # Chạy stream
        async for event in graph.astream(initial_input):
            # Mỗi event là một snapshot của trạng thái sau khi một node chạy xong
            if "generate" in event:
                # Node generate đã chạy, chúng ta có thể có câu trả lời
                response_chunk = event["generate"].get("response", "")
                full_response = response_chunk  # Giả sử generate trả về toàn bộ
                yield response_chunk  # Stream ra cho client

            # Lấy context đã được truy xuất
            if "retrieve" in event:
                retrieved_docs = event["retrieve"].get("retrieved_docs", [])

        # --- Stream đã kết thúc, tiến hành ghi nhật ký ---
        latency_ms = (time.time() - start_time) * 1000

        audit_log = AuditLog(
            chat_id=chat_id,
            question=question,
            response=full_response,
            retrieved_docs=retrieved_docs,
            latency_ms=latency_ms,
        )

        db.add(audit_log)
        await db.commit()
        print(f"Audit log saved for chat_id: {chat_id}")


# Tạo một instance duy nhất
chat_service = ChatService()
