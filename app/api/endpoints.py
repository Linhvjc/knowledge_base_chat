# /app/api/endpoints.py
from fastapi import APIRouter, Depends, HTTPException, status

# Thêm StreamingResponse
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select  # Thêm select
from typing import List
from uuid import UUID

from app.db.session import get_db_session
from app.db.models import AuditLog  # Thêm AuditLog model
from app.services.knowledge_service import knowledge_service

# Import chat service và các schema mới
from app.services.chat_service import chat_service
from app.schemas.schema import (
    DocumentUploadRequest,
    GeneralStatusResponse,
    DocumentMetadataOutput,
    ChatInput,
    AuditLogOutput,
)

router = APIRouter()


@router.post(
    "/knowledge/update",
    response_model=GeneralStatusResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Knowledge Base"],
)
async def update_knowledge(
    request: DocumentUploadRequest, db: AsyncSession = Depends(get_db_session)
):
    """
    Nhận một danh sách các document, xử lý và thêm vào vector store.
    """
    if not request.documents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No documents provided."
        )

    created_ids = await knowledge_service.upsert_documents(request.documents, db)
    return GeneralStatusResponse(
        status="success",
        detail=f"Successfully added {len(created_ids)} document chunks.",
    )


@router.delete(
    "/knowledge/{doc_id}", response_model=GeneralStatusResponse, tags=["Knowledge Base"]
)
async def delete_knowledge(doc_id: UUID, db: AsyncSession = Depends(get_db_session)):
    """
    Xóa một document chunk bằng ID của nó.
    """
    deleted = await knowledge_service.delete_document(doc_id, db)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {doc_id} not found.",
        )
    return GeneralStatusResponse(status="success", detail=f"Document {doc_id} deleted.")


@router.get(
    "/knowledge", response_model=List[DocumentMetadataOutput], tags=["Knowledge Base"]
)
async def get_knowledge_list(db: AsyncSession = Depends(get_db_session)):
    """
    Lấy danh sách tất cả các document chunk và metadata của chúng.
    """
    documents = await knowledge_service.list_documents(db)
    return documents


@router.delete(
    "/knowledge/all", response_model=GeneralStatusResponse, tags=["Knowledge Base"]
)
async def delete_all_knowledge(db: AsyncSession = Depends(get_db_session)):
    """
    Xóa TẤT CẢ các document khỏi cơ sở tri thức.
    Đây là một hành động không thể hoàn tác.
    """
    deleted_count = await knowledge_service.delete_all_documents(db)
    return GeneralStatusResponse(
        status="success",
        detail=f"Đã xóa thành công toàn bộ {deleted_count} document chunks.",
    )


@router.post("/chat", tags=["Chat"])
async def chat_with_knowledge_base(
    request: ChatInput,  # request giờ đã chứa cả question và history
    db: AsyncSession = Depends(get_db_session),
):
    """
    Gửi câu hỏi và nhận câu trả lời streaming từ AI.
    Hỗ trợ multi-turn conversation.
    """
    # Truyền cả request.question và request.history xuống service
    generator = chat_service.stream_chat(request.question, request.history, db)
    return StreamingResponse(generator, media_type="text/plain")


# --- API Audit ---
@router.get("/audit/{chat_id}", response_model=AuditLogOutput, tags=["Audit"])
async def get_audit_log(chat_id: UUID, db: AsyncSession = Depends(get_db_session)):
    """
    Lấy thông tin chi tiết của một cuộc hội thoại đã được ghi lại.
    """
    result = await db.execute(select(AuditLog).where(AuditLog.chat_id == chat_id))
    log = result.scalars().first()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit log with chat_id {chat_id} not found.",
        )
    return log
