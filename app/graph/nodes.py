from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.messages import HumanMessage
from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .state import GraphState
from app.core import settings

embedding_model = GoogleGenerativeAIEmbeddings(
    model=settings.EMBEDDING_MODEL, google_api_key=settings.GEMINI_API_KEY,
)

llm = ChatGoogleGenerativeAI(
    model=settings.LLM_MODEL,
    google_api_key=settings.GEMINI_API_KEY,
    convert_system_message_to_human=True,
)


async def retrieve_node(state: GraphState, db: AsyncSession) -> dict[str, Any]:
    print('---NODE: RETRIEVE---')
    question = state['question']

    question_embedding = await embedding_model.aembed_query(question)

    stmt = text(
        """
        SELECT content, doc_metadata, 1 -
        (embedding <=> :query_embedding) AS similarity
        FROM documents
        ORDER BY similarity DESC
        LIMIT 3
        """,
    )
    result = await db.execute(
        stmt,
        {'query_embedding': str(question_embedding)},
    )
    retrieved_docs = [dict(row) for row in result.mappings().all()]

    context = '\n\n---\n\n'.join([doc['content'] for doc in retrieved_docs])

    print(f'Retrieved {len(retrieved_docs)} documents.')
    return {'retrieved_docs': retrieved_docs, 'context': context}


async def generate_node(state: GraphState) -> dict[str, Any]:
    print('---NODE: GENERATE (MULTI-TURN)---')
    question = state['question']
    context = state['context']
    chat_history = state.get('chat_history', [])

    history_messages = []
    for message in chat_history:
        if message.get('role') == 'user':
            history_messages.append(HumanMessage(content=message['content']))
        elif (
            message.get('role') == 'assistant'
            or message.get('role') == 'model'
        ):
            history_messages.append(AIMessage(content=message['content']))

    rag_prompt_template = """Based on the previous chat history and
    the Context provided below, answer the user's Last Question.
    If the information is not in the Context,
    answer based on the conversation history.

Context:
{context}

Question:
{question}
"""
    final_prompt_text = rag_prompt_template.format(
        context=context, question=question,
    )

    messages_to_llm = [
        SystemMessage(
            content='You are a helpful AI assistant, chatting and '
            'answering questions based on the information provided.',
        ),
        *history_messages,
        HumanMessage(content=final_prompt_text),
    ]

    response = await llm.ainvoke(messages_to_llm)

    return {'response': response.content}
