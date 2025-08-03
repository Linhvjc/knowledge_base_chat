from __future__ import annotations

import asyncio

import gradio as gr
import httpx

from app.core import settings

API_URL = settings.API_URL


async def handle_chat_interaction(
        message: str,
        history_tuples: list[tuple[str, str]],
):
    history_for_api = []
    for user_msg, assistant_msg in history_tuples:
        history_for_api.append({'role': 'user', 'content': user_msg})
        history_for_api.append({'role': 'assistant', 'content': assistant_msg})

    payload = {'question': message, 'history': history_for_api}

    history_tuples.append([message, ''])

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                'POST', f'{API_URL}/chat', json=payload,
            ) as response:
                response.raise_for_status()

                async for chunk in response.aiter_text():
                    if not chunk:
                        continue
                    for char in chunk:
                        history_tuples[-1][1] += char
                        await asyncio.sleep(0.005)
                        yield history_tuples

    except Exception as e:
        history_tuples[-1][1] = f'Error: {str(e)}'
        yield history_tuples


async def handle_file_upload(file):
    if not file:
        return 'Please upload a file.'

    with open(file.name, encoding='utf-8') as f:
        content = f.read()

    payload = {
        'documents': [
            {'content': content, 'metadata': {'source': file.name}},
        ],
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f'{API_URL}/knowledge/update',
            json=payload,
        )

    if response.status_code == 201:
        return f"Successfully uploaded file '{file.name}'!"
    else:
        return f'Error: {response.status_code} - {response.text}'


async def get_knowledge_list():
    async with httpx.AsyncClient() as client:
        response = await client.get(f'{API_URL}/knowledge')

    if response.status_code == 200:
        docs = response.json()
        if not docs:
            return 'No documents found in the knowledge base.'

        markdown_output = (
            '| ID | Size (bytes) | Source Metadata |\n|---|---|---|\n'
        )
        for doc in docs:
            source = doc.get('doc_metadata', {}).get('source', 'N/A')
            markdown_output += f"| `{doc['id']}` \
            | {doc['size']} | {source} |\n"
        return markdown_output
    else:
        return f'Error fetching document list: {response.text}'


async def handle_delete_knowledge(doc_id: str):
    if not doc_id or not doc_id.strip():
        return 'Please enter a Document ID.'

    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f'{API_URL}/knowledge/{doc_id.strip()}',
            )

        if response.status_code == 200:
            return f'Successfully deleted document ID: {doc_id}'
        elif response.status_code == 404:
            return f'Error: Document not found with ID: {doc_id}'
        else:
            return f'Server error: {response.status_code} - {response.text}'

    except Exception as e:
        return f'An unexpected error occurred: {str(e)}'


async def handle_delete_all_knowledge():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(f'{API_URL}/knowledge/all')

        if response.status_code == 200:
            detail = response.json().get(
                'detail',
                'All documents have been deleted.',
            )
            return f'Success: {detail}'
        else:
            return f'Server error: {response.status_code} - {response.text}'
    except Exception as e:
        return f'An unexpected error occurred: {str(e)}'


def create_ui():
    with gr.Blocks(
        theme=gr.themes.Soft(),
        title='Knowledge Base Chat',
    ) as demo:
        gr.Markdown('# Demo Interface for Q&A System')

        with gr.Tabs():
            with gr.TabItem('Chatbot'):
                chatbot = gr.Chatbot(
                    label='Conversation', height=600, bubble_full_width=False,
                )
                msg = gr.Textbox(label='Enter your question here')
                clear = gr.ClearButton([msg, chatbot])
                print(clear)

                msg.submit(
                    handle_chat_interaction,
                    [msg, chatbot],
                    chatbot,
                ).then(
                    lambda: gr.update(value=''),
                    None,
                    outputs=msg,
                    queue=False,
                )

            with gr.TabItem('Knowledge Management'):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown('## Upload New Documents')
                        file_input = gr.File(
                            label='Upload .txt file', file_types=['.txt'],
                        )
                        upload_button = gr.Button('Upload Document')
                        upload_status = gr.Textbox(
                            label='Upload Status', interactive=False,
                        )

                        upload_button.click(
                            handle_file_upload,
                            inputs=file_input,
                            outputs=upload_status,
                        )

                        gr.Markdown('---')
                        gr.Markdown('## Delete Document')
                        doc_id_to_delete = gr.Textbox(
                            label='Enter Document ID to delete',
                        )
                        delete_button = gr.Button('Delete Document')
                        delete_status = gr.Textbox(
                            label='Delete Status', interactive=False,
                        )

                        gr.Markdown('### Dangerous Actions')
                        delete_all_button = gr.Button(
                            'Delete All Knowledge', variant='stop',
                        )
                        delete_all_status = gr.Textbox(
                            label='Delete All Status', interactive=False,
                        )

                    with gr.Column(scale=2):
                        gr.Markdown('## Existing Document List')
                        refresh_button = gr.Button('Refresh List')
                        knowledge_display = gr.Markdown()

                refresh_button.click(
                    get_knowledge_list,
                    outputs=knowledge_display,
                )

                delete_button.click(
                    handle_delete_knowledge,
                    inputs=doc_id_to_delete,
                    outputs=delete_status,
                ).then(get_knowledge_list, None, outputs=knowledge_display)

                delete_all_button.click(
                    handle_delete_all_knowledge,
                    inputs=None,
                    outputs=delete_all_status,
                ).then(
                    get_knowledge_list, None, outputs=knowledge_display,
                )

    return demo
