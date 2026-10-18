import random

from app.data.lessons import QUESTIONS_BY_ID, QUESTIONS_BY_LEVEL
from app.services.learning_engine import LearnerState, LearningEngine, is_correct


def make():
    return LearningEngine(random.Random(42)), LearnerState()


def right(state):
    return QUESTIONS_BY_ID[state.pending_question_id].answer


def test_lesson_data_is_valid():
    for level, qs in QUESTIONS_BY_LEVEL.items():
        assert len(qs) >= 5
        for q in qs:
            assert q.level == level
            assert q.answer in q.options
            assert len(set(q.options)) == len(q.options)
            assert q.hint


def test_start_asks_level_1_question():
    engine, state = make()
    turn = engine.start(state)
    q = QUESTIONS_BY_ID[state.pending_question_id]
    assert q.level == 1
    assert q.answer in turn.quick_replies
    assert q.prompt in turn.reply


def test_answer_matching_is_forgiving():
    q = QUESTIONS_BY_ID["l1_cat"]
    for text in ("🐱", "cat", "A cat!", "It is a cat.", "CAT"):
        assert is_correct(q, text)
    assert not is_correct(q, "dog")
    assert not is_correct(q, "")


def test_correct_first_try_is_recorded_and_advances():
    engine, state = make()
    engine.start(state)
    first = state.pending_question_id
    turn = engine.answer(state, right(state))
    assert turn.graded and turn.correct
    assert state.last_answers == [True]
    assert state.pending_question_id != first


def test_wrong_gives_hint_and_keeps_same_question():
    engine, state = make()
    engine.start(state)
    qid = state.pending_question_id
    turn = engine.answer(state, "zzz")
    assert turn.graded and turn.correct is False
    assert "Hint" in turn.reply
    assert state.pending_question_id == qid
    assert state.last_answers == [False]


def test_retry_correct_is_not_double_counted():
    engine, state = make()
    engine.start(state)
    engine.answer(state, "zzz")
    turn = engine.answer(state, right(state))
    assert turn.correct and not turn.graded
    assert state.last_answers == [False]


def test_second_wrong_reveals_answer_and_moves_on():
    engine, state = make()
    engine.start(state)
    q = QUESTIONS_BY_ID[state.pending_question_id]
    engine.answer(state, "zzz")
    turn = engine.answer(state, "zzz")
    assert q.answer in turn.reply
    assert state.pending_question_id != q.id
    assert len(state.last_answers) == 1


def test_level_up_with_4_of_5_correct():
    engine, state = make()
    engine.start(state)
    engine.answer(state, "zzz")
    engine.answer(state, right(state))      # prothom proshno: bhul, retry te thik
    for _ in range(4):
        turn = engine.answer(state, right(state))
    assert state.level == 2
    assert turn.level_up
    assert state.last_answers == []
    assert QUESTIONS_BY_ID[state.pending_question_id].level == 2


def test_no_level_up_with_3_of_5():
    engine, state = make()
    engine.start(state)
    for _ in range(3):
        engine.answer(state, right(state))
    for _ in range(2):
        engine.answer(state, "zzz")
        engine.answer(state, right(state))
    assert state.level == 1


def test_never_demotes():
    engine, state = make()
    engine.start(state)
    for _ in range(10):
        engine.answer(state, "zzz")
        engine.answer(state, "zzz")
    assert state.level == 1


def test_mastering_level_3():
    engine, state = make()
    state.level = 3
    engine.start(state)
    for _ in range(5):
        turn = engine.answer(state, right(state))
    assert turn.mastered
    assert state.level == 3


def test_weak_word_comes_back():
    engine, state = make()
    state.word_stats = {"dog": {"correct": 0, "wrong": 2}}
    engine.start(state)
    assert QUESTIONS_BY_ID[state.pending_question_id].word == "dog"


def test_is_struggling_after_three_wrong():
    engine, state = make()
    state.last_answers = [True, False, False, False]
    assert engine.is_struggling(state)
    state.last_answers = [False, False, True]
    assert not engine.is_struggling(state)