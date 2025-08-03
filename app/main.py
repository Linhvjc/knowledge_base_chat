from __future__ import annotations

import gradio as gr
from fastapi import FastAPI

from app.api import endpoints
from app.db.session import create_tables_on_startup
from app.ui.gradio_ui import create_ui

app = FastAPI(
    title='Knowledge Base AI System',
    description='An interview project using FastAPI, '
    'PGVector, LangChain, and Gemini.',
    version='1.0.0',
)


@app.on_event('startup')
async def on_startup():
    print('Application is starting up...')
    await create_tables_on_startup()
    print('Application startup is complete.')


app.include_router(endpoints.router)


@app.get('/health', tags=['Health Check'])
def health_check():
    return {'status': 'ok'}


gradio_app = create_ui()

app = gr.mount_gradio_app(app, gradio_app, path='/ui')
