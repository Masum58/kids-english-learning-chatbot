"""Orchestrator: puro flow ek jaygay. validate -> load -> safety -> mode -> respond -> save."""
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
    reply: str
    mode: str
    reason: str
    quick_replies: list[str]
    level: int
    progress: dict
    llm_used: bool = False


def clean_input(text: str) -> str:
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
            elif reason == mode_router.GREETING:
                reply, buttons = _with_menu(sel.GREETING, state)
            else:
                reply, llm_used = await _talk("conversation", text, state, row, d.emotion)
                reply, buttons = _with_menu(reply, state)

    repository.save(db, row, state, mode=mode, child_text=stored_text,
                    bot_reply=reply, turn=turn, level_before=level_before)
    return ChatResult(reply, mode, reason, buttons, state.level, engine.progress(state), llm_used)