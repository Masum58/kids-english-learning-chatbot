"""Database Models, Engine, and Session Management.

What this file does:
    Defines the database connection engine, session factory, and SQLAlchemy ORM models
    for both short-term conversational session state and long-term learning history.
    Also provides dependency injection for FastAPI database sessions.

Connections with other files:
    - app/config.py: Reads 'settings.sqlalchemy_url' to establish the database connection.
    - app/repository.py: Performs CRUD operations on ChatSession, Answer, and WordStat models.
    - app/main.py: Calls init_db() on startup and uses SessionLocal for '/health'.
    - app/api/chat.py: Injects 'get_db' as a FastAPI dependency for each chat request.
"""
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.config import settings

# In SQLite tests, threads may differ between requests; disabled in production PostgreSQL
_connect_args = {"check_same_thread": False} if settings.sqlalchemy_url.startswith("sqlite") else {}

engine = create_engine(settings.sqlalchemy_url, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative database models."""
    pass


class ChatSession(Base):
    """Short-term conversational state and learner level for a child.

    Attributes:
        id: Unique UUID or client session identifier string.
        level: Current pedagogical level (1, 2, or 3).
        mode: Current active child interaction mode (learning, conversation, engagement, support).
        pending_question: JSON payload of the active lesson question if mid-quiz.
        last_answers: Sliding window of last 5 boolean correctness results for level-up checks.
        recent_messages: Rolling buffer of recent chat turns used for LLM conversational context.
        created_at: Session creation timestamp.
        updated_at: Timestamp of the most recent interaction.
    """
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    level: Mapped[int] = mapped_column(Integer, default=1)
    mode: Mapped[str] = mapped_column(String(20), default="conversation")
    pending_question: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    last_answers: Mapped[list] = mapped_column(JSON, default=list)      # Last 5 booleans (for 4/5 mastery)
    recent_messages: Mapped[list] = mapped_column(JSON, default=list)   # Last 6 conversation turns
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class Answer(Base):
    """Long-term history of every individual lesson attempt by the child.

    Attributes:
        id: Auto-incrementing primary key ID.
        session_id: Foreign key linking back to the child's ChatSession.
        word: Target vocabulary word tested (e.g., 'cat', 'red').
        level: Pedagogical level at the time of the question (1, 2, or 3).
        correct: True if the child answered correctly on their first try.
        created_at: Timestamp of when the answer was recorded.
    """
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), index=True)
    word: Mapped[str] = mapped_column(String(50))
    level: Mapped[int] = mapped_column(Integer)
    correct: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class WordStat(Base):
    """Long-term aggregated word mastery tracker used for weak-word repetition.

    Attributes:
        session_id: Foreign key linking back to the child's ChatSession.
        word: Vocabulary word being tracked.
        correct_count: Total successful answers for this word.
        wrong_count: Total incorrect answers (used to prioritize spaced review).
    """
    __tablename__ = "word_stats"

    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), primary_key=True)
    word: Mapped[str] = mapped_column(String(50), primary_key=True)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    wrong_count: Mapped[int] = mapped_column(Integer, default=0)


def init_db() -> None:
    """Initializes database schema.

    What it does:
        Creates all defined database tables (sessions, answers, word_stats)
        if they do not already exist. Called automatically on application startup.

    Returns:
        None
    """
    Base.metadata.create_all(engine)


def get_db():
    """FastAPI database session dependency generator.

    What it does:
        Yields an isolated SQLAlchemy session per incoming HTTP request and
        guarantees that the session connection is closed when the request completes.

    Yields:
        Session: An active SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()