from langchain_core.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

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
    Node sinh ngôn ngữ: Tạo prompt, gọi LLM để sinh câu trả lời.
    """
    print("---NODE: GENERATE---")
    question = state["question"]
    context = state["context"]

    prompt_template = """Bạn là một trợ lý AI hữu ích. Hãy trả lời câu hỏi của người dùng chỉ dựa trên ngữ cảnh được cung cấp.
Nếu thông tin không có trong ngữ cảnh, hãy trả lời 'Tôi không tìm thấy thông tin để trả lời câu hỏi này.'.
Không thêm bất kỳ thông tin nào không có trong ngữ cảnh.

Ngữ cảnh:
{context}

Câu hỏi:
{question}
"""
    prompt = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    chain = prompt | llm

    response = await chain.ainvoke({"context": context, "question": question})

    return {"response": response.content}
