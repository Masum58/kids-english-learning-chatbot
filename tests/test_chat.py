import uuid

import pytest

from app.data.lessons import QUESTIONS_BY_LEVEL


def send(client, text, sid=None):
    r = client.post("/chat", json={"session_id": sid, "message": text})
    assert r.status_code == 200, r.text
    return r.json()


def correct_answer(reply: str) -> str:
    for qs in QUESTIONS_BY_LEVEL.values():
        for q in qs:
            if q.prompt in reply:
                return q.answer
    raise AssertionError(f"no question found in: {reply}")


def test_greeting_creates_session(client):
    r = send(client, "hi")
    assert r["mode"] == "conversation" and r["reason"] == "greeting"
    assert r["session_id"] and r["quick_replies"]


def test_learning_flow_and_progress(client):
    r = send(client, "teach me")
    sid = r["session_id"]
    assert r["mode"] == "learning" and r["quick_replies"]
    r = send(client, correct_answer(r["reply"]), sid)
    assert r["progress"]["correct"] == 1 and r["progress"]["answered"] == 1


def test_support_keeps_pending_question(client):
    first = send(client, "teach me")
    sid = first["session_id"]
    s = send(client, "I am sad", sid)
    assert s["mode"] == "support" and s["reason"] == "emotion:sad" and not s["llm_used"]
    back = send(client, correct_answer(first["reply"]), sid)         # persistence proman
    assert back["mode"] == "learning" and back["progress"]["correct"] == 1


def test_stuck_child_gets_hint_and_is_not_graded(client):
    sid = send(client, "teach me")["session_id"]
    r = send(client, "I don't know", sid)
    assert r["mode"] == "support" and "💡" in r["reply"]
    assert r["progress"]["answered"] == 0


def test_sessions_are_isolated(client):
    a = send(client, "teach me")
    for _ in range(5):
        a = send(client, correct_answer(a["reply"]), a["session_id"])
    assert a["level"] == 2
    assert send(client, "teach me")["level"] == 1


def test_unsafe_message_gets_safe_reply(client):
    r = send(client, "someone hurts me")
    assert r["mode"] == "support" and r["reason"] == "safety_concern"
    assert "grown-up" in r["reply"] and not r["llm_used"]


def test_personal_info_is_refused(client):
    r = send(client, "my phone is 01712345678")
    assert r["reason"] == "privacy" and "secret" in r["reply"]


@pytest.mark.parametrize("payload", [
    {"message": ""},
    {"message": "   "},
    {"message": "a" * 201},
    {"message": "hi", "session_id": "bad id!"},
])
def test_validation_errors(client, payload):
    assert client.post("/chat", json=payload).status_code == 422


def test_llm_failure_falls_back_to_template(client, monkeypatch):
    async def fail(*a, **k):
        return None
    monkeypatch.setattr("app.services.llm.reply", fail)
    r = send(client, "Why is the sky blue?", uuid.uuid4().hex)
    assert r["mode"] == "conversation" and r["reply"] and r["llm_used"] is False


def test_llm_reply_is_used_when_available(client, monkeypatch):
    async def ok(*a, **k):
        return "Because of the sunlight! ☀️"
    monkeypatch.setattr("app.services.llm.reply", ok)
    r = send(client, "Why is the sky blue?", uuid.uuid4().hex)
    assert r["llm_used"] is True and r["reply"].startswith("Because of the sunlight")