from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.chat import router as chat_router
from app.storage import SessionLocal, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="English Learning Chatbot for Kids", lifespan=lifespan)
app.include_router(chat_router)


@app.get("/health")
def health():
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}