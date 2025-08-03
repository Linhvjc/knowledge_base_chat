from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AuditLog
from app.db import get_db_session
from app.schemas import AuditLogOutput
from app.schemas import ChatInput
from app.schemas import DocumentMetadataOutput
from app.schemas import DocumentUploadRequest
from app.schemas import GeneralStatusResponse
from app.services import chat_service
from app.services import knowledge_service

router = APIRouter()


@router.post(
    '/knowledge/update',
    response_model=GeneralStatusResponse,
    status_code=status.HTTP_201_CREATED,
    tags=['Knowledge Base'],
)
async def update_knowledge(
    request: DocumentUploadRequest, db: AsyncSession = Depends(get_db_session),
):
    if not request.documents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='No documents provided.',
        )

    created_ids = await knowledge_service.upsert_documents(
        request.documents,
        db,
    )
    return GeneralStatusResponse(
        status='success',
        detail=f'Successfully added {len(created_ids)} document chunks.',
    )


@router.delete(
    '/knowledge/{doc_id}',
    response_model=GeneralStatusResponse,
    tags=['Knowledge Base'],
)
async def delete_knowledge(
    doc_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    deleted = await knowledge_service.delete_document(doc_id, db)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Document with id {doc_id} not found.',
        )
    return GeneralStatusResponse(
        status='success',
        detail=f'Document {doc_id} deleted.',
    )


@router.get(
    '/knowledge',
    response_model=List[DocumentMetadataOutput],
    tags=['Knowledge Base'],
)
async def get_knowledge_list(db: AsyncSession = Depends(get_db_session)):
    documents = await knowledge_service.list_documents(db)
    return documents


@router.delete(
    '/knowledge/all',
    response_model=GeneralStatusResponse,
    tags=['Knowledge Base'],
)
async def delete_all_knowledge(db: AsyncSession = Depends(get_db_session)):
    deleted_count = await knowledge_service.delete_all_documents(db)
    return GeneralStatusResponse(
        status='success',
        detail=f'Deleted all successfully {deleted_count} document chunks.',
    )


@router.post('/chat', tags=['Chat'])
async def chat_with_knowledge_base(
    request: ChatInput,
    db: AsyncSession = Depends(get_db_session),
):
    generator = chat_service.stream_chat(request.question, request.history, db)
    return StreamingResponse(generator, media_type='text/plain')


@router.get('/audit/{chat_id}', response_model=AuditLogOutput, tags=['Audit'])
async def get_audit_log(
    chat_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(AuditLog).where(AuditLog.chat_id == chat_id),
    )
    log = result.scalars().first()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Audit log with chat_id {chat_id} not found.',
        )
    return log
