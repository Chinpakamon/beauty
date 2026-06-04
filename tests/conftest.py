import json
import sys
from pathlib import Path
from typing import Any

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.booking.router import router as booking_router
from app.api.review.router import router as review_router
from app.api.service.router import router as service_router
from app.api.service_type.router import router as service_type_router
from app.api.user.router import router as user_router
from app.core.database.core import Base, get_session

ROOT = Path(__file__).resolve().parents[1]
MOCKS_DIR = Path(__file__).resolve().parent / "mocks" / "user"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


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
    app.include_router(user_router)
    app.include_router(service_type_router)
    app.include_router(service_router)
    app.include_router(booking_router)
    app.include_router(review_router)

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
