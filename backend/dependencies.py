"""Shared FastAPI dependencies."""

from uuid import UUID

from fastapi import Header, HTTPException


async def get_session_id(x_session_id: str | None = Header(default=None)) -> str:
    """Extract and validate the session UUID from the ``X-Session-Id`` header.

    Args:
        x_session_id: Raw header value (or None if absent).

    Returns:
        The validated session UUID as a string.

    Raises:
        HTTPException: 400 if the header is missing or not a valid UUID.
    """
    if not x_session_id:
        raise HTTPException(status_code=400, detail="Missing X-Session-Id header.")
    try:
        UUID(x_session_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail="Malformed X-Session-Id header (expected a UUID)."
        ) from exc
    return x_session_id
