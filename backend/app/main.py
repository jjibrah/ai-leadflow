from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.core.exceptions import global_exception_handler


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_exception_handler(
        Exception,
        global_exception_handler,
    )

    @app.get("/")
    async def root():
        return {
            "message": f"Welcome to {settings.APP_NAME}!",
            "app": settings.APP_NAME,
            "environment": settings.APP_ENV,
        }

    @app.get("/test-db")
    async def test_db(db: AsyncSession = Depends(get_db)):
        await db.execute(text("SELECT 1"))

        return {
            "message": "Database connection successful"
        }

    @app.get("/test-error")
    async def test_error():
        result = 10 / 0
        return result

    @app.get("/health")
    async def health_check(db: AsyncSession = Depends(get_db)):
        try:
            await db.execute(text("SELECT 1"))

            return {
                "status": "healthy"
            }

        except Exception:
            raise HTTPException(
                status_code=503,
                detail="Database unavailable"
            )

    return app


app = create_app()