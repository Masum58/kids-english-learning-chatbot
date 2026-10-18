import os

# app import hobar AGE set korte hobe
os.environ["DATABASE_URL"] = "sqlite:///./test_chatbot.db"
os.environ["GEMINI_API_KEY"] = ""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    from app.main import app
    from app.storage import Base, engine

    Base.metadata.drop_all(engine)
    with TestClient(app) as c:      # lifespan chalay, table banay
        yield c
    engine.dispose()
    if os.path.exists("test_chatbot.db"):
        os.remove("test_chatbot.db")