import os
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport

# Set test environment
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_isdp.db"

from backend.app.core.config import settings
settings.DATABASE_URL = "sqlite+aiosqlite:///./test_isdp.db"

from backend.app.core.database import Base, get_db
from backend.app.services.seed_service import seed_database
from backend.app.main import app

test_engine = create_async_engine(
    "sqlite+aiosqlite:///./test_isdp.db",
    connect_args={"check_same_thread": False}
)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    # Remove old test database if exists
    if os.path.exists("./test_isdp.db"):
        try:
            os.remove("./test_isdp.db")
        except Exception:
            pass

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        await seed_database(session)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()
    if os.path.exists("./test_isdp.db"):
        try:
            os.remove("./test_isdp.db")
        except Exception:
            pass

@pytest_asyncio.fixture(scope="function")
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
