from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

Message = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class ChatRequest(BaseModel):
    session_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{8,64}$")
    message: Message


class Progress(BaseModel):
    level: int
    answered: int
    correct: int
    target: int


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    mode: str
    reason: str
    level: int
    progress: Progress
    quick_replies: list[str]
    llm_used: bool
    latency_ms: int