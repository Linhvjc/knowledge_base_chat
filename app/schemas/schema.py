from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class DocumentInput(BaseModel):
    source_id: str | None = None
    content: str
    metadata: dict[str, Any] | None = None


class DocumentUploadRequest(BaseModel):
    documents: list[DocumentInput]


class DocumentMetadataOutput(BaseModel):
    id: UUID
    size: int
    created_at: datetime
    doc_metadata: dict[str, Any] | None

    class Config:
        from_attributes = True


class GeneralStatusResponse(BaseModel):

    status: str
    detail: str | None = None


class ChatInput(BaseModel):
    question: str
    history: list[dict[str, str]] = []


class AuditLogOutput(BaseModel):
    chat_id: UUID
    question: str
    response: str
    retrieved_docs: list[dict[str, Any]]
    latency_ms: float
    timestamp: datetime
    feedback: str | None = None

    class Config:
        from_attributes = True
