"""Pydantic API Request and Response Schemas.

What this file does:
    Defines the contract for incoming HTTP requests and outgoing HTTP responses
    for the '/chat' endpoint, including input validation and typing constraints.

Connections with other files:
    - app/api/chat.py: Uses ChatRequest for body validation and ChatResponse for serialization.
    - frontend/app.js: Sends payloads matching ChatRequest and receives ChatResponse.
"""
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

Message = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class ChatRequest(BaseModel):
    """Payload sent by the client when sending a message to Teddy.

    Attributes:
        session_id: Optional client session UUID. If omitted, the server generates a new one.
        message: Non-empty user text bounded to 200 characters for young child interactions.
    """
    session_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{8,64}$")
    message: Message


class Progress(BaseModel):
    """Child's progress snapshot within their current learning level.

    Attributes:
        level: Current difficulty level (1, 2, or 3).
        answered: Number of recent questions answered in the sliding mastery window.
        correct: Number of correct answers in the window (out of target).
        target: Target count needed to advance to the next level (typically 5).
    """
    level: int
    answered: int
    correct: int
    target: int


class ChatResponse(BaseModel):
    """Structured response returned by the chatbot to the client.

    Attributes:
        session_id: The session ID corresponding to this conversation.
        reply: Child-friendly textual response to be spoken and displayed.
        mode: The detected operational mode (learning, conversation, engagement, support).
        reason: Explanatory tag detailing why this mode/response was chosen.
        level: Active learning level (1, 2, or 3).
        progress: Progress model showing score towards next star/level.
        quick_replies: Array of suggested button options or choices for the child.
        llm_used: True if Gemini LLM generated the reply; False if handled by rules/SEL templates.
        latency_ms: Total end-to-end server processing time in milliseconds.
    """
    session_id: str
    reply: str
    mode: str
    reason: str
    level: int
    progress: Progress
    quick_replies: list[str]
    llm_used: bool
    latency_ms: int