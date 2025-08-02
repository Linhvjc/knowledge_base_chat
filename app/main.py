from fastapi import FastAPI

# Xóa comment ở dòng import endpoints
from app.api import endpoints
from app.db.session import create_tables_on_startup

app = FastAPI(
    title="Knowledge Base AI System",
    description="An interview project using FastAPI, PGVector, LangChain, and Gemini.",
    version="1.0.0",
)


@app.on_event("startup")
async def on_startup():
    print("Application is starting up...")
    await create_tables_on_startup()
    print("Application startup is complete.")


# Xóa comment ở dòng này và thêm prefix
app.include_router(endpoints.router)


@app.get("/health", tags=["Health Check"])
def health_check():
    """Kiểm tra xem hệ thống có hoạt động không"""
    return {"status": "ok"}
