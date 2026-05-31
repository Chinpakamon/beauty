from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from sqlalchemy import text

from app.api.booking.router import router as booking_router
from app.api.service.router import router as service_router
from app.api.service_type.router import router as service_type_router
from app.api.user.router import router as user_router
from app.core.database.core import SessionLocal, engine
from app.core.middleware.auth_middleware import AuthMiddleware
from app.core.seeds.admin import create_dev_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("Database connected")
        async with SessionLocal() as session:
            await create_dev_admin(session)
    except Exception as e:
        print("Database connection failed")
        raise e

    yield

    await engine.dispose()
    print("Database connections closed")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Beauty API",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(AuthMiddleware)

    app.include_router(user_router)
    app.include_router(service_type_router)
    app.include_router(service_router)
    app.include_router(booking_router)

    @app.get(
        "/health",
        tags=["Healthcheck"],
        status_code=status.HTTP_200_OK,
    )
    async def healthcheck():
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return {"status": "ok", "database": "ok"}
        except Exception:
            return {"status": "degraded", "database": "error"}

    return app


app = create_app()
