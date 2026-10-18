"""Data Access and State Persistence Layer (Repository).

What this file does:
    Bridges PostgreSQL database models with pure in-memory pedagogical data structures
    (LearnerState). It loads session data with row-level locking (with_for_update)
    to prevent race conditions, aggregates word statistics, and persists updated turns.

Connections with other files:
    - app/storage.py: Imports ChatSession, Answer, and WordStat models.
    - app/services/learning_engine.py: Maps database rows to LearnerState and Turn.
    - app/services/orchestrator.py: Calls repository.load() at the start of a chat turn
      and repository.save() at the end to persist all state changes.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.services.learning_engine import LearnerState, Turn
from app.storage import Answer, ChatSession, WordStat

HISTORY_LIMIT = 6


def load(db: Session, session_id: str) -> tuple[ChatSession, LearnerState]:
    """Loads or creates a child's session and reconstructs their learning state.

    What it does:
        Fetches the ChatSession row using 'with_for_update=True' for thread-safe
        concurrency. If the session is new, creates and flushes a new row.
        Then queries the child's WordStat records and reconstructs a clean LearnerState.

    Args:
        db (Session): Active SQLAlchemy database session.
        session_id (str): Unique session identifier for the child.

    Returns:
        tuple[ChatSession, LearnerState]:
            - ChatSession: The live database ORM row.
            - LearnerState: The in-memory domain state used by the learning engine.
    """
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
    """Persists updated state, dialogue history, and graded answers to PostgreSQL.

    What it does:
        1. Synchronizes the ChatSession row with current mode, level, and pending question.
        2. Appends the latest user-bot exchange to recent_messages (bounded to HISTORY_LIMIT).
        3. If the turn was a graded learning answer, logs a new Answer entry and
           updates the persistent WordStat record for spaced repetition tracking.
        4. Commits the transaction to the database.

    Args:
        db (Session): Active SQLAlchemy database session.
        row (ChatSession): Database session row to update.
        state (LearnerState): Current in-memory state after turn processing.
        mode (str): Active interaction mode ('learning', 'conversation', etc.).
        child_text (str): Sanitized text received from the child.
        bot_reply (str): Response message sent by the bot.
        turn (Turn | None): Learning turn result, if this was a pedagogical quiz turn.
        level_before (int): Child's level prior to this turn (used for accurate answer logging).

    Returns:
        None
    """
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