"""Central configuration: environment variables and constants.

All tunable values live here so nothing is hardcoded elsewhere.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# --- Secrets / connection strings (from environment) ----------------------------

GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")
CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")

# --- RAG / chunking constants ---------------------------------------------------

CHUNK_SIZE: int = 500
CHUNK_OVERLAP: int = 50
MAX_PDF_SIZE_MB: int = 20
TOP_K_CHUNKS: int = 5
MEMORY_LAST_N: int = 5
HISTORY_PAGE_LIMIT: int = 50  # messages returned by GET /api/chat/history

# Drop retrieved chunks below this cosine similarity. NOTE: the spec specified
# 0.5, but that was calibrated for text-embedding-004. gemini-embedding-001
# (see model note below) produces lower absolute scores, so 0.5 filters out
# genuinely relevant chunks. 0.2 is calibrated for the model actually in use;
# the system prompt remains the primary grounding guard.
SIMILARITY_THRESHOLD: float = 0.2

# --- Model identifiers ----------------------------------------------------------
#
# The spec requested gemini-1.5-flash / text-embedding-004, but those models
# return HTTP 404 on the current Gemini API endpoint used by newer API keys.
# These are the working equivalents (verified against a live key).
GEMINI_MODEL: str = "gemini-2.5-flash"
EMBEDDING_MODEL: str = "gemini-embedding-001"

# --- Storage --------------------------------------------------------------------

CHROMA_PATH: str = os.getenv("CHROMA_PATH", "./chroma_db")

# --- Limits derived from constants ----------------------------------------------

MAX_PDF_BYTES: int = MAX_PDF_SIZE_MB * 1024 * 1024


def validate_config() -> None:
    """Raise a clear error at startup if required secrets are missing.

    Raises:
        RuntimeError: if ``GEMINI_API_KEY`` is not set.
    """
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "Missing required environment variable GEMINI_API_KEY. "
            "Copy .env.example to .env and fill in your key."
        )
