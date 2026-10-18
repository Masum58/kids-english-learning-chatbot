"""Postgres <-> LearnerState. Engine DB jane na, ei file duto ke jore."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.services.learning_engine import LearnerState, Turn
from app.storage import Answer, ChatSession, WordStat

HISTORY_LIMIT = 6


def load(db: Session, session_id: str) -> tuple[ChatSession, LearnerState]:
    # with_for_update: ek-i session er duto request ek shathe elei serial e cholbe
    row = db.get(ChatSession, session_id, with_for_update=True)
    if row is None:
        row = ChatSession(id=session_id, level=1, mode="conversation", last_answers=[],
                          recent_messages=[], pending_question={"id": None, "attempts": 0, "recent": []})
        db.add(row)
        db.flush()
    pq = row.pending_question or {}
    stats = {
        w.word: {"correct": w.correct_count, "wrong": w.wrong_count}
        for w in db.scalars(select(WordStat).where(WordStat.session_id == session_id))
    }
    state = LearnerState(
        level=row.level,
        last_answers=list(row.last_answers or []),
        pending_question_id=pq.get("id"),
        attempts=pq.get("attempts", 0),
        recent_question_ids=list(pq.get("recent", [])),
        word_stats=stats,
    )
    return row, state


def save(db: Session, row: ChatSession, state: LearnerState, *, mode: str, child_text: str,
         bot_reply: str, turn: Turn | None, level_before: int) -> None:
    row.level = state.level
    row.mode = mode
    row.last_answers = list(state.last_answers)
    row.pending_question = {"id": state.pending_question_id, "attempts": state.attempts,
                            "recent": list(state.recent_question_ids)}
    row.recent_messages = (list(row.recent_messages or []) + [
        {"role": "child", "text": child_text},
        {"role": "bot", "text": bot_reply},
    ])[-HISTORY_LIMIT:]

    if turn and turn.graded and turn.word:
        db.add(Answer(session_id=row.id, word=turn.word, level=level_before, correct=bool(turn.correct)))
        stat = state.word_stats[turn.word]
        ws = db.get(WordStat, (row.id, turn.word)) or WordStat(session_id=row.id, word=turn.word)
        ws.correct_count, ws.wrong_count = stat["correct"], stat["wrong"]
        db.add(ws)
    db.commit()