"""Gemini embeddings wrapper.

Document chunks and queries use different task types (``RETRIEVAL_DOCUMENT`` vs
``RETRIEVAL_QUERY``), which improves retrieval quality. Chunks are embedded in
sub-batches to respect the API's per-request / per-minute limits, with
exponential-style backoff on quota errors.
"""

import logging
import time

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from config import EMBEDDING_MODEL, GEMINI_API_KEY

logger = logging.getLogger(__name__)

genai.configure(api_key=GEMINI_API_KEY)

_MODEL_NAME = f"models/{EMBEDDING_MODEL}"
_MAX_RETRIES = 3
# Quota (429) errors are throttled per minute; wait for the window to reset.
_QUOTA_RETRY_DELAY_SECONDS = 35.0
# Each chunk counts as one request, so embed in sub-batches.
_EMBED_BATCH_SIZE = 50


def _embed_with_backoff(content: str | list[str], task_type: str):
    """Call ``embed_content`` with backoff on rate-limit errors.

    Args:
        content: A single string or list of strings.
        task_type: ``RETRIEVAL_DOCUMENT`` or ``RETRIEVAL_QUERY``.

    Returns:
        The embedding payload (list[float] or list[list[float]]).

    Raises:
        Exception: re-raises the last error if all retries are exhausted.
    """
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            result = genai.embed_content(
                model=_MODEL_NAME, content=content, task_type=task_type
            )
            return result["embedding"]
        except google_exceptions.ResourceExhausted as exc:
            last_exc = exc
            logger.warning(
                "Embedding rate-limited (attempt %d/%d); retrying in %.0fs",
                attempt + 1,
                _MAX_RETRIES,
                _QUOTA_RETRY_DELAY_SECONDS,
            )
            time.sleep(_QUOTA_RETRY_DELAY_SECONDS)
        except Exception as exc:
            logger.error("Embedding call failed: %s", exc)
            raise

    logger.error("Embedding still failing after %d retries.", _MAX_RETRIES)
    assert last_exc is not None
    raise last_exc


def embed_text(text: str) -> list[float]:
    """Embed a single query string (task type RETRIEVAL_QUERY)."""
    return _embed_with_backoff(text, task_type="RETRIEVAL_QUERY")


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed document chunks in sub-batches (task type RETRIEVAL_DOCUMENT).

    Args:
        texts: The chunk strings to embed.

    Returns:
        One embedding vector per chunk, in order. Empty list for empty input.
    """
    if not texts:
        return []

    vectors: list[list[float]] = []
    for start in range(0, len(texts), _EMBED_BATCH_SIZE):
        sub_batch = texts[start : start + _EMBED_BATCH_SIZE]
        logger.info(
            "Embedding chunks %d-%d of %d",
            start + 1,
            start + len(sub_batch),
            len(texts),
        )
        vectors.extend(_embed_with_backoff(sub_batch, task_type="RETRIEVAL_DOCUMENT"))
    return vectors
