import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.user.router import router
from app.core.database.core import Base, get_session

ROOT = Path(__file__).resolve().parents[1]
MOCKS_DIR = Path(__file__).resolve().parent / "mocks" / "user"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db"
)
os.environ.setdefault("JWT_SECRET", "secret")
os.environ.setdefault("SECRET_KEY", "secret")
os.environ.setdefault("ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("ADMIN_PASSWORD", "Password123!")
os.environ.setdefault("ADMIN_PHONE_NUMBER", "+79990001122")
os.environ.setdefault("ADMIN_FIRST_NAME", "Admin")
os.environ.setdefault("ADMIN_LAST_NAME", "User")


def load_mock(*parts: str) -> dict[str, Any]:
    return json.loads((MOCKS_DIR.joinpath(*parts)).read_text())


@pytest_asyncio.fixture
async def test_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
def test_app(test_session: AsyncSession) -> FastAPI:
    app = FastAPI()
    app.include_router(router)

    async def override_session():
        yield test_session

    app.dependency_overrides[get_session] = override_session

    yield app

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_client(test_app: FastAPI) -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as client:
        yield client
