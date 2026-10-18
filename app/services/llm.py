"""Google Gemini LLM Integration with Strict Latency Timeout & Guardrails.

What this file does:
    Interfaces with Google Gemini (default 'gemini-2.5-flash-lite') for dynamic,
    natural language responses in Conversation and Support modes.
    Enforces three critical constraints:
        1. Sub-7-year-old child safety prompt (max 2 short sentences, friendly emojis,
           no PII collection, no scary topics).
        2. Strict hard timeout (settings.llm_timeout_seconds, default 1.3s) via asyncio.wait_for().
        3. Never raises unhandled exceptions: returns None on timeout, rate-limiting, or error,
           allowing the orchestrator to fall back to deterministic SEL templates instantly.

Connections with other files:
    - app/config.py: Reads gemini_api_key, gemini_model, and llm_timeout_seconds.
    - app/services/orchestrator.py: Calls reply() for dynamic conversational or empathetic turns.
"""
import asyncio
import logging

from google import genai
from google.genai import types

from app.config import settings

log = logging.getLogger(__name__)
MAX_CHARS = 280
_client: genai.Client | None = None

SYSTEM = """You are Teddy, a kind English teacher-friend for children under 7.
Rules:
- Reply in at most 2 short sentences, using very simple English words.
- Use 1 or 2 emojis. Be warm, cheerful and encouraging.
- Never ask for the child's name, age, address, school, phone number or photos.
- Never discuss scary, violent or adult topics. If asked, gently change the subject.
- If the child shares a feeling: name the feeling, say it is okay, suggest ONE tiny action
  (a deep breath, a hug, or telling a grown-up they trust). Do not diagnose or give advice about health.
- If the child asks a question, answer simply and truthfully, then stop.
- Do not give links. Do not claim to be human."""


def _get_client() -> genai.Client | None:
    global _client
    if not settings.gemini_api_key:
        return None
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def _clean(text: str | None) -> str | None:
    if not text:
        return None
    text = " ".join(text.split())
    if not text or "http" in text.lower():
        return None
    if len(text) > MAX_CHARS:
        cut = max(text.rfind(m, 0, MAX_CHARS) for m in (". ", "! ", "? "))
        text = text[: cut + 1] if cut > 0 else text[:MAX_CHARS].rstrip()
    return text


def _prompt(mode: str, text: str, level: int, history: list[dict], emotion: str | None) -> str:
    lines = [f"Mode: {mode}. The child's English level is L{level} of 3."]
    if emotion:
        lines.append(f"The child seems to feel: {emotion}.")
    if history:
        lines.append("Recent chat:")
        lines += [f"{'Child' if m['role'] == 'child' else 'Teddy'}: {m['text']}" for m in history[-4:]]
    lines.append(f"Child says: {text}")
    lines.append("Teddy replies:")
    return "\n".join(lines)


async def reply(mode: str, text: str, *, level: int, history: list[dict], emotion: str | None = None) -> str | None:
    """Asynchronously generates a child-friendly response using Google Gemini.

    What it does:
        Constructs a prompt incorporating the child's current level, emotional state,
        and recent dialogue history. Enforces an asynchronous deadline of
        'settings.llm_timeout_seconds' (1.3s). If generation succeeds, trims and sanitizes
        the output. If the deadline expires or any error occurs, logs a warning and returns None.

    Args:
        mode (str): Operational mode ('conversation' or 'support').
        text (str): Sanitized input message from the child.
        level (int): Child's current learning level (1, 2, or 3).
        history (list[dict]): Recent dialogue turns for conversational context.
        emotion (str | None): Detected emotion (e.g. 'sad', 'happy') or None.

    Returns:
        str | None: Cleaned child-safe reply string, or None if the LLM timed out or failed.
    """
    client = _get_client()
    if client is None:
        return None
    try:
        resp = await asyncio.wait_for(
            client.aio.models.generate_content(
                model=settings.gemini_model,
                contents=_prompt(mode, text, level, history, emotion),
                config=types.GenerateContentConfig(system_instruction=SYSTEM, max_output_tokens=150, temperature=0.7),
            ),
            timeout=settings.llm_timeout_seconds,
        )
        return _clean(resp.text)
    except Exception as exc:        # Timeout, 429, network, safety blocks gracefully fall back
        log.warning("LLM fallback used: %s", type(exc).__name__)
        return None