"""Document CRUD routes, scoped to the caller's session."""

import asyncio
import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import CHUNK_OVERLAP, CHUNK_SIZE, MAX_PDF_BYTES
from database import get_db
from dependencies import get_session_id
from models import Document
from rag import embeddings, pdf_processor, vector_store
from schemas import DocumentOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    session_id: str = Depends(get_session_id),
    db: AsyncSession = Depends(get_db),
) -> list[Document]:
    """List the current session's documents, newest first."""
    result = await db.execute(
        select(Document)
        .where(Document.session_id == session_id)
        # id tiebreaker: uploaded_at has only second resolution on SQLite.
        .order_by(Document.uploaded_at.desc(), Document.id.desc())
    )
    return list(result.scalars().all())


def _ingest(session_id: str, document_id: int, filename: str, pdf_bytes: bytes) -> int:
    """Extract, chunk, embed, and store a PDF. Runs in a worker thread.

    Returns:
        The number of chunks stored.
    """
    text = pdf_processor.extract_text(pdf_bytes)
    chunks = pdf_processor.chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
    if not chunks:
        return 0
    vectors = embeddings.embed_batch(chunks)
    vector_store.add_document(session_id, document_id, filename, chunks, vectors)
    return len(chunks)


@router.post("", response_model=DocumentOut, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = Depends(get_session_id),
    db: AsyncSession = Depends(get_db),
) -> Document:
    """Upload a PDF: validate, extract, chunk, embed, and persist."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=415, detail="Only PDF files are accepted.")

    pdf_bytes = await file.read()
    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise HTTPException(
            status_code=413, detail="File too large. Maximum size is 20 MB."
        )

    filename = file.filename or "document.pdf"

    # Create the Document row first so we have an id for the chunk metadata.
    document = Document(session_id=session_id, filename=filename, chunk_count=0)
    db.add(document)
    await db.flush()  # assigns document.id without committing

    try:
        chunk_count = await asyncio.to_thread(
            _ingest, session_id, document.id, filename, pdf_bytes
        )
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        await db.rollback()
        logger.error("Failed to ingest PDF for session %s: %s", session_id, exc)
        raise HTTPException(
            status_code=500, detail="Failed to process the PDF."
        ) from exc

    if chunk_count == 0:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="No extractable text found (the PDF may be scanned images).",
        )

    document.chunk_count = chunk_count
    try:
        await db.commit()
    except Exception as exc:
        # The Chroma write already happened inside _ingest; if the DB commit
        # fails the Document row won't persist, so remove the orphaned chunks
        # to keep the two stores consistent.
        await db.rollback()
        await asyncio.to_thread(vector_store.delete_document, session_id, document.id)
        logger.error("Commit failed after ingest for session %s: %s", session_id, exc)
        raise HTTPException(
            status_code=500, detail="Failed to save the document."
        ) from exc
    await db.refresh(document)
    return document


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: int,
    session_id: str = Depends(get_session_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a document (and its chunks), verifying session ownership."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id, Document.session_id == session_id
        )
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    await asyncio.to_thread(vector_store.delete_document, session_id, document_id)
    await db.delete(document)
    await db.commit()
