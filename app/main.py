import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .dependencies import get_redis
from .routes import summarize, health

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: verify Redis connection
    print("Skipping Redis for local development")
    yield
    # shutdown: close Redis connection pool
    pass


app = FastAPI(
    title="YouTube Summarizer API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(summarize.router, prefix="/api")
app.include_router(health.router, prefix="/api")