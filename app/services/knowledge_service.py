# /app/services/knowledge_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from uuid import UUID

from app.core.config import settings
from app.db.models import Document
from app.schemas.schema import DocumentInput, DocumentMetadataOutput
from typing import List


class KnowledgeService:

    def __init__(self):
        # KHẮC PHỤC: Truyền API key trực tiếp vào constructor
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001", google_api_key=settings.GEMINI_API_KEY
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=100
        )

    async def upsert_documents(
        self, documents_in: List[DocumentInput], db: AsyncSession
    ) -> List[UUID]:
        """
        Phân tách, tạo embedding và lưu các document vào database.
        """
        all_chunks_text = []
        all_metadata = []

        for doc in documents_in:
            chunks = self.text_splitter.split_text(doc.content)
            for chunk_content in chunks:
                all_chunks_text.append(chunk_content)
                # Lưu metadata gốc cho mỗi chunk
                all_metadata.append(doc.metadata or {})

        if not all_chunks_text:
            return []

        # Tạo embedding cho tất cả các chunk trong một lần gọi API (hiệu quả hơn)
        embeddings = self.embedding_model.embed_documents(all_chunks_text)

        # Tạo các đối tượng Document ORM
        new_docs_to_add = [
            Document(content=text, embedding=embedding, doc_metadata=meta)
            for text, embedding, meta in zip(all_chunks_text, embeddings, all_metadata)
        ]

        db.add_all(new_docs_to_add)
        await db.commit()

        # Trả về ID của các chunk đã được tạo
        return [doc.id for doc in new_docs_to_add]

    async def delete_document(self, doc_id: UUID, db: AsyncSession) -> bool:
        """
        Xóa một document chunk khỏi database bằng ID của nó.
        """
        result = await db.execute(delete(Document).where(Document.id == doc_id))
        await db.commit()
        # `rowcount` > 0 nghĩa là đã có hàng bị xóa
        return result.rowcount > 0

    async def list_documents(self, db: AsyncSession) -> List[DocumentMetadataOutput]:
        """
        Liệt kê tất cả các document chunks với metadata của chúng.
        """
        result = await db.execute(select(Document))
        documents = result.scalars().all()

        # Ánh xạ kết quả sang Pydantic model
        return [
            DocumentMetadataOutput(
                id=doc.id,
                size=len(doc.content),  # Tính toán kích thước
                created_at=doc.created_at,
                doc_metadata=doc.doc_metadata,
            )
            for doc in documents
        ]


# Tạo một instance duy nhất để sử dụng trong toàn ứng dụng
knowledge_service = KnowledgeService()
