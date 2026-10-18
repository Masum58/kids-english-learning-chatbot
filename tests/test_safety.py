import pytest

from app.services import safety


@pytest.mark.parametrize("text", ["someone hurts me", "He hit me", "I want to die", "I am scared to go home"])
def test_unsafe(text):
    assert safety.check(text) == "unsafe"


@pytest.mark.parametrize("text", ["my phone is 01712345678", "My name is Rina", "I live in Dhaka", "mail me at a@b.com"])
def test_personal_info(text):
    assert safety.check(text) == "personal_info"


@pytest.mark.parametrize("text", ["Teach me animals", "I like my dog", "I am sad", "cat"])
def test_normal_messages_pass(text):
    assert safety.check(text) is None