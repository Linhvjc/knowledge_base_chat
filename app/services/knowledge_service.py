# /app/services/knowledge_service.py
from __future__ import annotations

from uuid import UUID

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import settings
from app.db import Document
from app.schemas import DocumentInput
from app.schemas import DocumentMetadataOutput


class KnowledgeService:

    def __init__(self):
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=100,
        )

    async def upsert_documents(
        self, documents_in: list[DocumentInput], db: AsyncSession,
    ) -> list[UUID]:
        all_chunks_text = []
        all_metadata = []

        for doc in documents_in:
            chunks = self.text_splitter.split_text(doc.content)
            for chunk_content in chunks:
                all_chunks_text.append(chunk_content)
                all_metadata.append(doc.metadata or {})

        if not all_chunks_text:
            return []

        embeddings = self.embedding_model.embed_documents(all_chunks_text)

        new_docs_to_add = [
            Document(content=text, embedding=embedding, doc_metadata=meta)
            for text, embedding, meta in zip(
                all_chunks_text,
                embeddings,
                all_metadata,
            )
        ]

        db.add_all(new_docs_to_add)
        await db.commit()

        return [doc.id for doc in new_docs_to_add]

    async def delete_document(self, doc_id: UUID, db: AsyncSession) -> bool:
        result = await db.execute(
            delete(Document).
            where(Document.id == doc_id),
        )
        await db.commit()
        return result.rowcount > 0

    async def list_documents(
        self,
        db: AsyncSession,
    ) -> list[DocumentMetadataOutput]:
        result = await db.execute(select(Document))
        documents = result.scalars().all()

        return [
            DocumentMetadataOutput(
                id=doc.id,
                size=len(doc.content),
                created_at=doc.created_at,
                doc_metadata=doc.doc_metadata,
            )
            for doc in documents
        ]

    async def delete_all_documents(self, db: AsyncSession) -> int:
        result = await db.execute(delete(Document))
        await db.commit()
        return result.rowcount


knowledge_service = KnowledgeService()
