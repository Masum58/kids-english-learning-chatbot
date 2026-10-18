import pytest

from app.services.learning_engine import LearnerState
from app.services.mode_router import detect


def st(pending=None, last=None):
    return LearnerState(pending_question_id=pending, last_answers=last or [])


@pytest.mark.parametrize("text,pending,expected", [
    ("Teach me animals", None, "learning"),
    ("I want lean new things from AI", None, "learning"),
    ("Hello, how are you?", None, "conversation"),
    ("Why is the sky blue?", None, "conversation"),
    ("Let's play a game!", None, "engagement"),
    ("I am sad", None, "support"),
    ("I am scared", None, "support"),
    ("hello", None, "conversation"),
    ("I am so happy", None, "conversation"),
    ("I am sad and I want to play", None, "support"),        # support > engagement
    ("I don't know", "l1_cat", "support"),
    ("I am sad", "l1_cat", "support"),
    ("🐱", "l1_cat", "learning"),
    ("cat", "l1_cat", "learning"),
    ("dog", "l1_cat", "learning"),                           # bhul hole-o uttor
    ("why is it red?", "l1_cat", "conversation"),
    ("let's play", "l1_cat", "engagement"),
    ("📚 Keep learning", "l1_cat", "learning"),
])
def test_mode_detection(text, pending, expected):
    assert detect(text, st(pending)).mode == expected


def test_answer_flag():
    assert detect("🐱", st("l1_cat")).is_answer
    assert not detect("teach me", st("l1_cat")).is_answer


def test_every_decision_has_a_reason():
    assert detect("I am sad", st()).reason == "emotion:sad"
    assert detect("hi", st()).reason == "greeting"
    assert detect("hello how are you", st()).reason == "friendly_check_in"


def test_struggling_child_gets_support_once():
    state = st("l1_cat", [False, False, False])
    assert detect("dog", state, "learning").reason == "child_struggling"
    assert detect("dog", state, "support").mode == "learning"      # loop hobe na


def test_again_repeats_the_game_only_after_a_game():
    assert detect("🔁 Again", st(), "engagement").mode == "engagement"
    assert detect("🔁 Again", st(), "learning").mode == "learning"


def test_yes_keeps_a_child_in_the_current_game():
    decision = detect("yes", st(), "engagement")
    assert decision.mode == "engagement" and decision.reason == "continues_play"


@pytest.mark.parametrize("text", ["are you there", "let's change topic", "let's change the topic", "something else"])
def test_conversation_does_not_be_graded_as_a_pending_answer(text):
    decision = detect(text, st("l1_cat"), "learning")
    assert decision.mode == "conversation"
