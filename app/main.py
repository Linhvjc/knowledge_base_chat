from fastapi import FastAPI
import gradio as gr  # Thêm import Gradio

from app.api import endpoints
from app.db.session import create_tables_on_startup
from app.ui.gradio_ui import create_ui  # Thêm import hàm tạo UI

# --- Khởi tạo FastAPI ---
app = FastAPI(
    title="Knowledge Base AI System",
    description="An interview project using FastAPI, PGVector, LangChain, and Gemini.",
    version="1.0.0",
)


# --- Các sự kiện và router của FastAPI ---
@app.on_event("startup")
async def on_startup():
    print("Application is starting up...")
    await create_tables_on_startup()
    print("Application startup is complete.")


app.include_router(endpoints.router)


@app.get("/health", tags=["Health Check"])
def health_check():
    """Kiểm tra xem hệ thống có hoạt động không"""
    return {"status": "ok"}


# --- Gắn ứng dụng Gradio ---
# Tạo giao diện Gradio
gradio_app = create_ui()

# Gắn ứng dụng Gradio vào ứng dụng FastAPI tại đường dẫn /ui
# FastAPI sẽ vẫn xử lý các route API của nó, và chuyển các request đến /ui cho Gradio.
app = gr.mount_gradio_app(app, gradio_app, path="/ui")
