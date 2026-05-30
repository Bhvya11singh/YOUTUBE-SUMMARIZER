from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from ..dependencies import get_redis

router = APIRouter()

@router.get("/health")
async def health(redis: Redis = Depends(get_redis)):
    try:
        await redis.ping()
        redis_status = "ok"
    except Exception:
        redis_status = "unavailable"

    return {"status": "ok", "redis": redis_status}