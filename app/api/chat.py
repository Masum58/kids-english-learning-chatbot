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