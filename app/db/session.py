import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text  # Thêm dòng này

from app.core.config import settings
from app.db.models import Base

# Tạo một async engine.
# echo=True sẽ log tất cả các câu lệnh SQL mà SQLAlchemy thực thi, rất hữu ích để debug.
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
)

# Tạo một "nhà máy" sản xuất session bất đồng bộ (async session factory)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_tables_on_startup():
    """
    Hàm được gọi khi ứng dụng khởi động để tạo bảng và kích hoạt extension.
    """
    async with async_engine.begin() as conn:
        # Rất quan trọng: Phải tạo extension TRƯỚC khi tạo các bảng sử dụng kiểu 'vector'
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

        # Tạo tất cả các bảng được định nghĩa trong Base.metadata
        # run_sync là cách để chạy các phương thức đồng bộ (như create_all) trong môi trường async
        await conn.run_sync(Base.metadata.create_all)

    print("Database tables created and pgvector extension enabled successfully.")


async def get_db_session() -> AsyncSession:
    """
    Hàm Dependency Injection để cung cấp một DB session cho mỗi request.

    Nó đảm bảo session được đóng đúng cách sau khi request hoàn thành,
    ngay cả khi có lỗi xảy ra.
    """
    async with AsyncSessionLocal() as session:
        yield session
