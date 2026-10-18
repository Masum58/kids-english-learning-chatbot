"""Central Conversational & Pedagogical Orchestrator.

What this file does:
    Coordinates the complete turn-by-turn request pipeline:
        1. clean_input: Sanitizes whitespace and strips control characters.
        2. repository.load: Loads short-term state and long-term word statistics.
        3. safety.check: Zero-latency check for distress, PII, or memory probing.
        4. mode_router.detect: Classifies intent into learning, conversation, engagement, or support.
        5. Execution:
            - If Learning: Evaluates answers or presents new questions via LearningEngine.
            - If Engagement: Selects fun micro-games and rhymes via sel.
            - If Support (stuck): Provides hints without punitive grading.
            - If Support (emotion) or Conversation: Queries Gemini with 1.3s timeout and SEL fallback.
        6. repository.save: Persists updated state and logs graded answers.

Connections with other files:
    - app/api/chat.py: Calls handle_message() for every incoming HTTP chat request.
    - app/repository.py: Loads and commits ChatSession and WordStat records.
    - app/services/safety.py: Evaluates safety flags.
    - app/services/mode_router.py: Classifies modes and emotional states.
    - app/services/learning_engine.py: Evaluates quizzes and handles level progression.
    - app/services/llm.py: Generates natural language responses for open-ended chat.
    - app/services/sel.py: Supplies empathetic responses, games, and fallback templates.
"""
import random
import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app import repository
from app.data.lessons import QUESTIONS_BY_ID
from app.services import llm, mode_router, safety, sel
from app.services.learning_engine import LearningEngine

engine = LearningEngine()
rng = random.Random()


@dataclass
class ChatResult:
    """Internal result container produced by the orchestrator.

    Attributes:
        reply: Response text for the child.
        mode: Active interaction mode for this turn.
        reason: Explanation tag for decision logging.
        quick_replies: Array of suggested button options.
        level: Current pedagogical level (1, 2, or 3).
        progress: Progress dictionary containing answered, correct, and target counts.
        llm_used: True if Gemini generated the reply, False if handled by rules/templates.
    """
    reply: str
    mode: str
    reason: str
    quick_replies: list[str]
    level: int
    progress: dict
    llm_used: bool = False


def clean_input(text: str) -> str:
    """Sanitizes raw user input by stripping control characters and collapsing whitespace.

    Args:
        text (str): Raw string message submitted by the user.

    Returns:
        str: Cleaned, whitespace-collapsed string.
    """
    return re.sub(r"\s+", " ", re.sub(r"[\x00-\x1f\x7f]", " ", text)).strip()


async def _talk(mode: str, text: str, state, row, emotion: str | None) -> tuple[str, bool]:
    answer = await llm.reply(mode, text, level=state.level, history=row.recent_messages or [], emotion=emotion)
    if answer:
        return answer, True
    return (sel.EMOTION_REPLIES[emotion] if emotion else sel.CONVERSATION_FALLBACK), False


def _with_menu(reply: str, state) -> tuple[str, list[str]]:
    if state.pending_question_id:
        return f"{reply}\n{sel.BACK_TO_QUESTION}", sel.menu(True)
    return reply, sel.menu(False)


async def handle_message(db: Session, session_id: str, text: str) -> ChatResult:
    """Executes the complete end-to-end processing pipeline for a chat turn.

    What it does:
        Sanitizes text, loads child session state, checks safety filters, routes the
        appropriate mode, evaluates learning quizzes or queries the LLM with fallback,
        saves all updates to PostgreSQL, and returns a ChatResult.

    Args:
        db (Session): Active SQLAlchemy database session.
        session_id (str): Unique session identifier for the child.
        text (str): Incoming message text from the child.

    Returns:
        ChatResult: Dataclass containing the bot's reply, mode, level, progress,
                    interactive choices, and telemetry metadata.
    """

    text = clean_input(text)
    row, state = repository.load(db, session_id)
    previous_mode, level_before = row.mode, state.level
    stored_text, turn, llm_used = text, None, False

    flag = safety.check(text)
    if flag == "unsafe":
        mode, reason, reply, buttons = "support", "safety_concern", safety.UNSAFE_REPLY, []
    elif flag == "personal_info":
        mode, reason = "conversation", "privacy"
        reply, buttons = safety.PRIVACY_REPLY, sel.menu(False)
        stored_text = "[removed for privacy]"
    elif flag == "memory_question":
        mode, reason = "conversation", "privacy_memory"
        reply, buttons = safety.MEMORY_REPLY, sel.menu(False)
    else:
        d = mode_router.detect(text, state, previous_mode)
        mode, reason = d.mode, d.reason

        if mode == mode_router.LEARNING:
            turn = engine.answer(state, text) if d.is_answer else engine.start(state)
            reply, buttons = turn.reply, turn.quick_replies

        elif mode == mode_router.ENGAGEMENT:
            reply, buttons = rng.choice(sel.ENGAGEMENT), list(sel.ENGAGEMENT_BUTTONS)

        elif mode == mode_router.SUPPORT:
            q = QUESTIONS_BY_ID.get(state.pending_question_id) if state.pending_question_id else None
            if d.emotion:
                reply, llm_used = await _talk("support", text, state, row, d.emotion)
                reply, buttons = _with_menu(reply, state)
            elif q:      # atke gese: hint dei, grade kori na
                pool = sel.STRUGGLING if reason == mode_router.STRUGGLING else sel.STUCK
                reply = f"{rng.choice(pool)}\n💡 {q.hint}\n{q.prompt}"
                buttons = rng.sample(list(q.options), len(q.options))
            else:
                reply, buttons = sel.STUCK_NO_QUESTION, sel.menu(False)

        else:  # conversation
            if reason == mode_router.CHAT_OPENER:
                reply, buttons = sel.CHAT_OPENER, ["📚 Learn", "🎮 Play"]
            elif reason == "change_topic":
                state.pending_question_id = None
                state.attempts = 0
                reply, buttons = "Sure! 😊 What would you like to do now?", sel.menu(False)
            elif reason == "friendly_check_in":
                reply, buttons = "I'm happy to learn with you! 😊 How are you feeling today?", sel.menu(bool(state.pending_question_id))
            elif reason == mode_router.GREETING:
                if state.pending_question_id:
                    reply, buttons = "Hi again! 👋 Want to keep practicing or play a game?", sel.menu(True)
                else:
                    reply, buttons = sel.GREETING, sel.menu(False)
            else:
                reply, llm_used = await _talk("conversation", text, state, row, d.emotion)
                reply, buttons = _with_menu(reply, state)

    repository.save(db, row, state, mode=mode, child_text=stored_text,
                    bot_reply=reply, turn=turn, level_before=level_before)
    return ChatResult(reply, mode, reason, buttons, state.level, engine.progress(state), llm_used)
