from typing import Optional

from fastapi_limiter import FastAPILimiter
from redis.asyncio import from_url as redis_from_url, Redis


async def init_rate_limiter(redis_url: str) -> Redis:
    redis = redis_from_url(redis_url, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis)
    return redis


async def shutdown_rate_limiter(redis: Optional[Redis]) -> None:
    if redis is not None:
        await redis.close()

