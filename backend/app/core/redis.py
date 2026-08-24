from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import ArqRedis
from fastapi import FastAPI, Request

from app.workers.dependencies import redis_settings
from app.core.config import settings


@asynccontextmanager
async def redis_lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.redis = None
    if not settings.BACKGROUND_JOBS_ENABLED:
        yield
        return

    redis = await create_pool(redis_settings)
    app.state.redis = redis
    try:
        yield
    finally:
        await redis.aclose()


def get_redis(request: Request) -> ArqRedis | None:
    return request.app.state.redis
