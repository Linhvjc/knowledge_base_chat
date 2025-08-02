from fastapi import FastAPI

# from .api import endpoints
# from .db.session import create_tables_on_startup

app = FastAPI(
    title="Knowledge Base AI System",
    description="An interview project using FastAPI, PGVector, LangChain, and Gemini.",
    version="1.0.0",
)

# @app.on_event("startup")
# async def on_startup():
#     # Hàm này sẽ được gọi khi ứng dụng khởi động
#     # Dùng để tạo các bảng trong database nếu chúng chưa tồn tại
#     await create_tables_on_startup()

# app.include_router(endpoints.router, prefix="/api/v1")


@app.get("/health", tags=["Health Check"])
def health_check():
    """Kiểm tra xem hệ thống có hoạt động không"""
    return {"status": "ok"}
