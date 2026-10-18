"""Chat API Endpoint Router.

What this file does:
    Exposes the primary HTTP POST '/chat' endpoint. It receives user messages,
    measures total execution latency, delegates processing to the orchestrator,
    and returns a structured ChatResponse.

Connections with other files:
    - app/models/schemas.py: Uses ChatRequest for input validation and ChatResponse for output.
    - app/services/orchestrator.py: Calls handle_message() to execute safety, routing, pedagogy, and LLM steps.
    - app/storage.py: Depends on get_db() to inject an active database session.
    - app/main.py: Mounts this router into the central FastAPI app.
"""
import time
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.schemas import ChatRequest, ChatResponse
from app.services.orchestrator import handle_message
from app.storage import get_db

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """Handles an interactive chat turn between the child and Teddy.

    What it does:
        1. Records high-precision start time using time.perf_counter().
        2. Assigns an existing session_id or generates a new hex UUID if none was provided.
        3. Calls orchestrator.handle_message() to run input sanitization, safety guardrails,
           mode routing, pedagogical quizzes, and optional LLM generation.
        4. Calculates end-to-end server latency in milliseconds.
        5. Formats and returns the complete ChatResponse.

    Args:
        req (ChatRequest): Incoming validated JSON payload containing session_id and message.
        db (Session): Database session injected by FastAPI dependency.

    Returns:
        ChatResponse: Pydantic model with reply, operational mode, level, progress,
                      quick reply buttons, LLM usage flag, and latency_ms.
    """
    start = time.perf_counter()
    session_id = req.session_id or uuid.uuid4().hex
    result = await handle_message(db, session_id, req.message)
    return ChatResponse(
        session_id=session_id,
        reply=result.reply,
        mode=result.mode,
        reason=result.reason,
        level=result.level,
        progress=result.progress,
        quick_replies=result.quick_replies,
        llm_used=result.llm_used,
        latency_ms=int((time.perf_counter() - start) * 1000),
    )