"""Pydantic v2 request/response models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentOut(BaseModel):
    """A document as returned to the client."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    chunk_count: int
    uploaded_at: datetime


class MessageOut(BaseModel):
    """A chat message as returned to the client."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    created_at: datetime


class ChatRequest(BaseModel):
    """Body for POST /api/chat."""

    question: str = Field(..., min_length=1)
