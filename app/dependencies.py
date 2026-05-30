import os
from functools import lru_cache
from openai import AsyncOpenAI
from redis.asyncio import Redis
from dotenv import load_dotenv

load_dotenv()


@lru_cache
def get_openai() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

@lru_cache
def get_redis() -> Redis:
    return Redis.from_url(
        os.environ["REDIS_URL"],
        encoding="utf-8",
        decode_responses=True
    )