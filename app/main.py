"""Application Entry Point (FastAPI).

What this file does:
    Initializes the FastAPI application, manages database startup lifecycle,
    configures CORS middleware, registers API endpoints, and serves the frontend.

Connections with other files:
    - app/api/chat.py: Registers the '/chat' endpoint router.
    - app/storage.py: Calls init_db() on startup and uses SessionLocal for '/health'.
    - frontend/: Serves index.html, styles.css, and app.js as static files from the root URL.
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.chat import router as chat_router
from app.storage import SessionLocal, init_db

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    What it does:
        Runs startup tasks before the server starts accepting requests,
        specifically ensuring database tables are initialized.

    Args:
        app (FastAPI): The running FastAPI application instance.

    Yields:
        None: Hands control over to the application during its runtime.
    """
    init_db()
    yield


app = FastAPI(title="English Learning Chatbot for Kids", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Static MVP frontend; restrict to the deployed domain in production.
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(chat_router)


@app.get("/health")
def health():
    """Service health and database connectivity probe.

    What it does:
        Executes a simple 'SELECT 1' query against PostgreSQL to ensure
        both the server and database are healthy and responsive.

    Returns:
        dict: A status dictionary containing:
            - status (str): "ok"
            - database (str): "connected"
    """
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


