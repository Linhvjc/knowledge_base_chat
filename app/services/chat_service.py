from __future__ import annotations

import time
import uuid
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AuditLog
from app.graph import get_graph_runnable


class ChatService:

    async def stream_chat(
        self, question: str, history: list[dict[str, str]], db: AsyncSession,
    ) -> AsyncGenerator[str, None]:
        start_time = time.time()
        chat_id = uuid.uuid4()

        graph = get_graph_runnable(db)

        full_response = ''
        retrieved_docs = []

        initial_input = {'question': question, 'chat_history': history}

        async for event in graph.astream(initial_input):
            if 'generate' in event:
                response_chunk = event['generate'].get('response', '')
                full_response = response_chunk
                yield response_chunk

            if 'retrieve' in event:
                retrieved_docs = event['retrieve'].get('retrieved_docs', [])

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
        print(f'Audit log saved for chat_id: {chat_id}')


chat_service = ChatService()
