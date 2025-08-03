from langchain_core.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.core.config import settings
from app.graph.state import GraphState

# --- Khởi tạo các model cần thiết ---
embedding_model = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001", google_api_key=settings.GEMINI_API_KEY
)

# Model cho việc sinh ngôn ngữ, hỗ trợ streaming
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    google_api_key=settings.GEMINI_API_KEY,
    convert_system_message_to_human=True,
)

# --- Định nghĩa các Node ---


async def retrieve_node(state: GraphState, db: AsyncSession) -> Dict[str, Any]:
    """
    Node truy xuất: Lấy câu hỏi, tạo embedding, và tìm các document liên quan.
    """
    print("---NODE: RETRIEVE---")
    question = state["question"]

    # Tạo embedding cho câu hỏi
    question_embedding = await embedding_model.aembed_query(question)

    # Tìm kiếm trong PGVector (dùng toán tử cosine distance <->)
    # Lấy top 3 document liên quan nhất
    stmt = text(
        """
        SELECT content, doc_metadata, 1 - (embedding <=> :query_embedding) AS similarity
        FROM documents
        ORDER BY similarity DESC
        LIMIT 3
        """
    )
    result = await db.execute(stmt, {"query_embedding": str(question_embedding)})
    retrieved_docs = [dict(row) for row in result.mappings().all()]

    context = "\n\n---\n\n".join([doc["content"] for doc in retrieved_docs])

    print(f"Retrieved {len(retrieved_docs)} documents.")
    return {"retrieved_docs": retrieved_docs, "context": context}


async def generate_node(state: GraphState) -> Dict[str, Any]:
    """
    Node sinh ngôn ngữ, giờ đây có nhận biết về lịch sử hội thoại.
    """
    print("---NODE: GENERATE (MULTI-TURN)---")
    question = state["question"]
    context = state["context"]
    chat_history = state.get("chat_history", [])  # Lấy history từ state

    # 1. Chuyển đổi history từ dict sang các đối tượng Message của LangChain
    history_messages = []
    for message in chat_history:
        if message.get("role") == "user":
            history_messages.append(HumanMessage(content=message["content"]))
        elif message.get("role") == "assistant" or message.get("role") == "model":
            history_messages.append(AIMessage(content=message["content"]))

    # 2. Tạo prompt mới kết hợp RAG và history
    # Đây là prompt cuối cùng mà người dùng gửi, được bổ sung ngữ cảnh RAG
    rag_prompt_template = """Dựa vào lịch sử trò chuyện trước đó và Ngữ cảnh được cung cấp dưới đây, hãy trả lời Câu hỏi cuối cùng của người dùng. Nếu thông tin không có trong Ngữ cảnh, hãy trả lời dựa trên cuộc trò chuyện

Ngữ cảnh:
{context}

Câu hỏi:
{question}
"""
    final_prompt_text = rag_prompt_template.format(context=context, question=question)

    # 3. Xây dựng toàn bộ danh sách tin nhắn để gửi đến model
    messages_to_llm = [
        SystemMessage(
            content="Bạn là một trợ lý AI hữu ích, trò chuyện và trả lời câu hỏi dựa trên thông tin được cung cấp."
        ),
        *history_messages,  # Thêm tất cả các tin nhắn cũ
        HumanMessage(content=final_prompt_text),  # Thêm prompt cuối cùng
    ]

    # 4. Gọi LLM không cần qua PromptTemplate nữa
    response = await llm.ainvoke(messages_to_llm)

    return {"response": response.content}
