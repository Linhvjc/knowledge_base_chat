from fastapi import FastAPI

# Xóa comment ở các dòng import và router mà chúng ta đã chuẩn bị ở bước 1
# from .api import endpoints  # Chúng ta sẽ dùng nó ở bước sau
from .db.session import create_tables_on_startup

app = FastAPI(
    title="Knowledge Base AI System",
    description="An interview project using FastAPI, PGVector, LangChain, and Gemini.",
    version="1.0.0",
)


@app.on_event("startup")
async def on_startup():
    """
    Hàm này được gọi một lần duy nhất khi ứng dụng FastAPI khởi động.
    """
    print("Application is starting up...")
    await create_tables_on_startup()
    print("Application startup is complete.")


# app.include_router(endpoints.router, prefix="/api/v1") # Vẫn comment dòng này


@app.get("/health", tags=["Health Check"])
def health_check():
    """Kiểm tra xem hệ thống có hoạt động không"""
    return {"status": "ok"}
