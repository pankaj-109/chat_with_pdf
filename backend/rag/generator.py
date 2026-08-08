"""Gemini streaming answer generation for the RAG pipeline.

The system prompt forbids the model from using outside knowledge: if the
retrieved context does not contain the answer, it must say so verbatim.
"""

import logging
from collections.abc import AsyncIterator

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

genai.configure(api_key=GEMINI_API_KEY)

_model = genai.GenerativeModel(GEMINI_MODEL)

# "Labeled fallback" behavior (chosen over strict refusal): the bot answers
# document questions from the CONTEXT, but when the CONTEXT does not contain the
# answer it falls back to the model's general knowledge AND prefixes the reply with
# this label, so grounded vs. general answers stay clearly distinguishable.
GENERAL_ANSWER_LABEL = (
    "**⚠️ Not from your uploaded documents — general knowledge answer:**"
)

_PROMPT_TEMPLATE = """You are a helpful assistant for the user's uploaded documents. You are given CONTEXT
extracted from those documents. Answer the QUESTION using these two rules:

1. If the CONTEXT contains the answer, answer using ONLY the CONTEXT. Treat references such
   as "the document", "the pdf", "it", or "this" as referring to the CONTEXT, and summarize
   the CONTEXT when asked for an overview. Do not add outside information in this case.

2. If the CONTEXT does NOT contain the answer, answer from your own general knowledge — but
   you MUST begin your reply with this exact line, on its own line, followed by a blank line:
   {label}
   Then give a concise, accurate general answer. If you are unsure, say so.

CONVERSATION HISTORY (for follow-up context only — not source material):
{history}

CONTEXT (excerpts from the user's uploaded documents):
{context}

QUESTION: {question}

ANSWER:"""


def _format_history(history: list[tuple[str, str]]) -> str:
    """Render prior Q/A pairs, or a placeholder if there are none."""
    if not history:
        return "(none)"
    lines: list[str] = []
    for question, answer in history:
        lines.append(f"Q: {question}")
        lines.append(f"A: {answer}")
    return "\n".join(lines)


def _format_context(context_chunks: list[str]) -> str:
    """Render retrieved chunks as a numbered list."""
    if not context_chunks:
        return "(no context retrieved)"
    return "\n".join(f"[{i + 1}] {chunk}" for i, chunk in enumerate(context_chunks))


def _build_prompt(
    question: str, context_chunks: list[str], history: list[tuple[str, str]]
) -> str:
    """Assemble the full prompt from its parts."""
    return _PROMPT_TEMPLATE.format(
        label=GENERAL_ANSWER_LABEL,
        history=_format_history(history),
        context=_format_context(context_chunks),
        question=question,
    )


async def generate_stream(
    question: str,
    context_chunks: list[str],
    history: list[tuple[str, str]],
) -> AsyncIterator[str]:
    """Stream a grounded answer token-by-token.

    Args:
        question: The user's question.
        context_chunks: Retrieved chunk texts (the only allowed source).
        history: Recent (question, answer) pairs for follow-up continuity.

    Yields:
        Incremental text fragments of the model's answer.
    """
    prompt = _build_prompt(question, context_chunks, history)
    try:
        response = await _model.generate_content_async(prompt, stream=True)
        async for chunk in response:
            if getattr(chunk, "text", None):
                yield chunk.text
    except google_exceptions.ResourceExhausted:
        logger.warning("Gemini generation rate-limited / quota exceeded")
        yield (
            "⚠️ The AI is rate-limited right now — the Gemini free-tier quota has "
            "been reached. Please wait a little while and try again, or switch to a "
            "paid API key."
        )
    except Exception as exc:
        logger.error("Gemini generation failed: %s", exc)
        yield "Sorry, I ran into an error while generating an answer. Please try again."
