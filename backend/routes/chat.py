"""Chat routes: streaming SSE chat plus history read/clear."""

import asyncio
import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import HISTORY_PAGE_LIMIT, MEMORY_LAST_N, TOP_K_CHUNKS
from database import AsyncSessionLocal, get_db
from dependencies import get_session_id
from models import Document, Message
from rag import embeddings, generator, vector_store
from schemas import ChatRequest, MessageOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

NO_DOCUMENTS_MESSAGE = (
    "You haven't uploaded any documents yet. Upload a PDF first, then ask away."
)


def _sse(data: str) -> str:
    """Encode a string as one SSE 'data:' event (JSON-escaped to survive newlines)."""
    return f"data: {json.dumps(data)}\n\n"


async def _has_documents(db: AsyncSession, session_id: str) -> bool:
    """Return True if the session has at least one document."""
    result = await db.execute(
        select(Document.id).where(Document.session_id == session_id).limit(1)
    )
    return result.first() is not None


async def _recent_history(db: AsyncSession, session_id: str) -> list[tuple[str, str]]:
    """Return the last MEMORY_LAST_N (user, assistant) pairs, oldest first."""
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        # id is the tiebreaker: created_at has only second resolution on SQLite,
        # so without it same-second messages can sort/pair incorrectly.
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(MEMORY_LAST_N * 2)
    )
    messages = list(result.scalars().all())[::-1]  # back to chronological order

    pairs: list[tuple[str, str]] = []
    pending_user: str | None = None
    for msg in messages:
        if msg.role == "user":
            pending_user = msg.content
        elif msg.role == "assistant" and pending_user is not None:
            pairs.append((pending_user, msg.content))
            pending_user = None
    return pairs[-MEMORY_LAST_N:]


@router.post("")
async def chat(
    body: ChatRequest,
    session_id: str = Depends(get_session_id),
) -> StreamingResponse:
    """Answer a question, streaming the response as Server-Sent Events."""
    question = body.question.strip()

    async def event_stream() -> AsyncIterator[str]:
        # Use a dedicated DB session: the injected one may close before the
        # StreamingResponse body finishes being consumed.
        async with AsyncSessionLocal() as db:
            db.add(Message(session_id=session_id, role="user", content=question))
            await db.commit()

            # Retrieve context (blocking calls -> worker thread).
            try:
                query_vec = await asyncio.to_thread(embeddings.embed_text, question)
                matches = await asyncio.to_thread(
                    vector_store.query, session_id, query_vec, TOP_K_CHUNKS
                )
            except Exception as exc:
                logger.error("Retrieval failed for session %s: %s", session_id, exc)
                matches = []

            # With no documents at all, nudge the user to upload first. If documents
            # exist but nothing relevant was retrieved, we still generate: the labeled
            # fallback in the prompt then answers from general knowledge (clearly marked
            # as not coming from the user's documents).
            if not matches and not await _has_documents(db, session_id):
                db.add(
                    Message(
                        session_id=session_id,
                        role="assistant",
                        content=NO_DOCUMENTS_MESSAGE,
                    )
                )
                await db.commit()
                yield _sse(NO_DOCUMENTS_MESSAGE)
                yield "data: [DONE]\n\n"
                return

            context_chunks = [m["text"] for m in matches]  # may be empty
            history = await _recent_history(db, session_id)

            full_answer = ""
            async for token in generator.generate_stream(
                question, context_chunks, history
            ):
                full_answer += token
                yield _sse(token)

            db.add(
                Message(
                    session_id=session_id,
                    role="assistant",
                    content=full_answer.strip(),
                )
            )
            await db.commit()
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/history", response_model=list[MessageOut])
async def get_history(
    session_id: str = Depends(get_session_id),
    db: AsyncSession = Depends(get_db),
) -> list[Message]:
    """Return the most recent messages for the session, oldest first."""
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(HISTORY_PAGE_LIMIT)
    )
    return list(result.scalars().all())[::-1]


@router.delete("/history", status_code=204)
async def clear_history(
    session_id: str = Depends(get_session_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete all messages for the session (documents are kept)."""
    await db.execute(delete(Message).where(Message.session_id == session_id))
    await db.commit()
