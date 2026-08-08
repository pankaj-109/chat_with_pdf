"""FastAPI application entrypoint: CORS, routers, startup, health check."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import validate_config
from database import init_db
from routes import chat, documents, session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate config and create database tables on startup."""
    validate_config()
    await init_db()
    logger.info("Startup complete: database ready.")
    yield


# redirect_slashes=False adds immunity against 308 POST-to-GET redirect drops
app = FastAPI(
    title="Chat with PDF",
    lifespan=lifespan,
    redirect_slashes=False
)

# Allowed origins set to "*" to fix Vercel preflight CORS error
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(session.router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}