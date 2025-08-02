# /app/schemas/schema.py

from pydantic import BaseModel, Field
from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime
from typing import List, Dict, Any, Optional

# --- Schemas cho Knowledge Base ---


class DocumentInput(BaseModel):
    """Schema cho một document đầu vào."""

    # Bạn có thể cung cấp ID nguồn hoặc để trống
    source_id: str | None = None
    content: str
    metadata: Dict[str, Any] | None = None


class DocumentUploadRequest(BaseModel):
    """Schema cho request POST /knowledge/update."""

    documents: List[DocumentInput]


class DocumentMetadataOutput(BaseModel):
    """Schema cho dữ liệu trả về của một document."""

    id: UUID
    # Thêm trường size như yêu cầu, sẽ được tính toán
    size: int
    created_at: datetime
    doc_metadata: Dict[str, Any] | None

    class Config:
        # Cho phép Pydantic làm việc với các đối tượng ORM
        from_attributes = True


class GeneralStatusResponse(BaseModel):
    """Schema cho các phản hồi trạng thái chung."""

    status: str
    detail: str | None = None


# --- Schemas cho Chat ---


class ChatInput(BaseModel):
    """Schema cho đầu vào của API /chat."""

    question: str


class AuditLogOutput(BaseModel):
    """Schema cho đầu ra của API /audit/{chat_id}."""

    chat_id: UUID
    question: str
    response: str
    retrieved_docs: List[Dict[str, Any]]  # Danh sách các document đã lấy
    latency_ms: float
    timestamp: datetime
    feedback: Optional[str] = None

    class Config:
        from_attributes = True
