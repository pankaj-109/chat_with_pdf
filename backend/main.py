"""FastAPI application entrypoint: CORS, routers, startup, health check."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS, validate_config
from database import init_db
from routes import chat, documents, session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate config and create database tables on startup."""
    validate_config()
    await init_db()
    logger.info("Startup complete: database ready.")
    yield


app = FastAPI(title="Chat with PDF", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    # Explicitly allow the custom session header (and the rest).
    allow_headers=["*", "X-Session-Id"],
)

app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(session.router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}
