"""Session route: wipe everything tied to a session."""

import asyncio
import logging

from fastapi import APIRouter, Depends
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_session_id
from models import Document, Message
from rag import vector_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/session", tags=["session"])


@router.delete("", status_code=204)
async def reset_session(
    session_id: str = Depends(get_session_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete all messages, documents, and the ChromaDB collection for a session.

    The frontend follows this by generating a fresh session UUID locally.
    """
    await asyncio.to_thread(vector_store.delete_session, session_id)
    await db.execute(delete(Message).where(Message.session_id == session_id))
    await db.execute(delete(Document).where(Document.session_id == session_id))
    await db.commit()
    logger.info("Reset session %s", session_id)
