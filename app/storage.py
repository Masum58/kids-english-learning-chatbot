from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.config import settings

# Tests e SQLite use hoy; FastAPI request gulo alada thread e cholte pare, tai eta lage.
# Production e (Postgres) eta lage na.
_connect_args = {"check_same_thread": False} if settings.sqlalchemy_url.startswith("sqlite") else {}

engine = create_engine(settings.sqlalchemy_url, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class ChatSession(Base):
    """Short-term memory + shishur ekhon-kar obostha"""
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    level: Mapped[int] = mapped_column(Integer, default=1)
    mode: Mapped[str] = mapped_column(String(20), default="conversation")
    pending_question: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    last_answers: Mapped[list] = mapped_column(JSON, default=list)      # shesh 5 ta true/false
    recent_messages: Mapped[list] = mapped_column(JSON, default=list)   # shesh 6 ta message
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class Answer(Base):
    """Long-term memory: protita uttor er history"""
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), index=True)
    word: Mapped[str] = mapped_column(String(50))
    level: Mapped[int] = mapped_column(Integer)
    correct: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class WordStat(Base):
    """Long-term memory: kon shobdo e koto bhul/thik (weak word tracking)"""
    __tablename__ = "word_stats"

    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), primary_key=True)
    word: Mapped[str] = mapped_column(String(50), primary_key=True)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    wrong_count: Mapped[int] = mapped_column(Integer, default=0)


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_db():
    """FastAPI dependency: protita request e ekta DB session dey, shesh e bondho kore."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()