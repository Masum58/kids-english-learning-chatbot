"""Learning engine: proshno dewa, uttor check, level unlock, weak word tracking.
LLM lage na. Database o lage na: shudhu LearnerState niye kaj kore."""
import random
import re
from dataclasses import dataclass, field

from app.data.lessons import QUESTIONS_BY_ID, QUESTIONS_BY_LEVEL, Question

WINDOW = 5          # shesh koyta uttor dekhbe
PASS_MARK = 4       # koyta thik hole next level
MAX_LEVEL = 3
RECENT_MEMORY = 3   # shesh 3 ta proshno abar dibe na

LEVEL_INTRO = {
    1: "⭐ Level 1: Let's learn words!",
    2: "⭐⭐ Level 2: Let's finish the sentences!",
    3: "⭐⭐⭐ Level 3: Let's talk in English!",
}
LEVEL_UP = "🎉 Level up! You are ready for Level {level}!"
MASTERED = "🏆 Wow! You are an English star! Let's keep practicing!"
PRAISE = ["Great job! ⭐", "Wow, you got it! 🎉", "Super! 🌟", "Yay, that's right! 👏"]
TRY_AGAIN = ["Almost! Let's try again 💪", "Good try! 🌈", "Oops, not quite! You can do it 😊"]


@dataclass
class LearnerState:
    level: int = 1
    last_answers: list[bool] = field(default_factory=list)       # shesh 5 ta (prothom chesta)
    pending_question_id: str | None = None
    attempts: int = 0                                            # ei proshno e koybar bhul
    recent_question_ids: list[str] = field(default_factory=list)
    word_stats: dict[str, dict[str, int]] = field(default_factory=dict)


@dataclass
class Turn:
    reply: str
    quick_replies: list[str]
    question_id: str | None
    graded: bool = False        # ei turn e notun uttor record hoyeche kina (DB log er jonno)
    correct: bool | None = None
    word: str | None = None
    level_up: bool = False
    mastered: bool = False


# ---------- uttor milano ----------
_LEAD = ("it is ", "its ", "this is ", "a ", "an ", "the ")


def normalize(text: str) -> str:
    text = text.lower().replace("\ufe0f", "")
    text = re.sub(r"[.,!?;:'\"’]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _canon(text: str) -> str:
    t = normalize(text)
    changed = True
    while changed:
        changed = False
        for prefix in _LEAD:
            if t.startswith(prefix):
                t, changed = t[len(prefix):], True
    return t


def is_correct(q: Question, text: str) -> bool:
    given = _canon(text)
    return bool(given) and given in {_canon(a) for a in (q.answer, *q.also_accept)}


# ---------- engine ----------
class LearningEngine:
    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    # public
    def start(self, state: LearnerState) -> Turn:
        if state.pending_question_id is None:
            self._set_pending(state, self._pick(state))
            prefix = LEVEL_INTRO[state.level]
        else:
            prefix = "Let's keep going! 😊"
        q = QUESTIONS_BY_ID[state.pending_question_id]
        return Turn(f"{prefix}\n{q.prompt}", self._options(q), q.id)

    def answer(self, state: LearnerState, text: str) -> Turn:
        if state.pending_question_id is None:
            return self.start(state)
        q = QUESTIONS_BY_ID[state.pending_question_id]
        if is_correct(q, text):
            return self._on_correct(state, q)
        return self._on_wrong(state, q)

    def hint(self, state: LearnerState) -> str | None:
        """Support mode e kaje lagbe."""
        if state.pending_question_id is None:
            return None
        return QUESTIONS_BY_ID[state.pending_question_id].hint

    def is_struggling(self, state: LearnerState) -> bool:
        """Shesh 3 ta uttor-i bhul hole true (Mode Router eta dekhbe)."""
        return len(state.last_answers) >= 3 and not any(state.last_answers[-3:])

    def progress(self, state: LearnerState) -> dict:
        return {"level": state.level, "answered": len(state.last_answers),
                "correct": sum(state.last_answers), "target": WINDOW}

    # private
    def _on_correct(self, state, q) -> Turn:
        if state.attempts == 0:
            self._record(state, q, True)
            return self._advance(state, self.rng.choice(PRAISE), graded=True, correct=True, word=q.word)
        # bhul er pore retry te thik: abar record kori na
        return self._advance(state, "You got it this time! 🌟 I'm proud of you!",
                             graded=False, correct=True, word=q.word)

    def _on_wrong(self, state, q) -> Turn:
        state.attempts += 1
        if state.attempts == 1:
            self._record(state, q, False)
            reply = f"{self.rng.choice(TRY_AGAIN)}\n💡 Hint: {q.hint}\n{q.prompt}"
            return Turn(reply, self._options(q), q.id, graded=True, correct=False, word=q.word)
        feedback = f"That's okay! 🌈 The answer is {q.answer}. Let's try another one!"
        return self._advance(state, feedback, graded=False, correct=False, word=q.word)

    def _advance(self, state, feedback, *, graded, correct, word) -> Turn:
        state.pending_question_id = None
        event = self._check_level_up(state)
        extra = ""
        if event == "level_up":
            extra = f"{LEVEL_UP.format(level=state.level)}\n{LEVEL_INTRO[state.level]}"
        elif event == "mastered":
            extra = MASTERED
        q = self._pick(state)
        self._set_pending(state, q)
        reply = "\n".join(p for p in (feedback, extra, q.prompt) if p)
        return Turn(reply, self._options(q), q.id, graded=graded, correct=correct, word=word,
                    level_up=event == "level_up", mastered=event == "mastered")

    def _check_level_up(self, state) -> str | None:
        window = state.last_answers[-WINDOW:]
        if len(window) == WINDOW and sum(window) >= PASS_MARK:
            state.last_answers = []
            if state.level < MAX_LEVEL:
                state.level += 1
                return "level_up"
            return "mastered"
        return None

    def _record(self, state, q, correct: bool) -> None:
        state.last_answers = (state.last_answers + [correct])[-WINDOW:]
        stat = state.word_stats.setdefault(q.word, {"correct": 0, "wrong": 0})
        stat["correct" if correct else "wrong"] += 1

    def _set_pending(self, state, q) -> None:
        state.pending_question_id = q.id
        state.attempts = 0
        state.recent_question_ids = (state.recent_question_ids + [q.id])[-RECENT_MEMORY:]

    def _pick(self, state) -> Question:
        level_qs = QUESTIONS_BY_LEVEL[state.level]
        recent = set(state.recent_question_ids)
        pool = [q for q in level_qs if q.id not in recent] or level_qs
        weak = [q for q in pool if self._is_weak(state, q.word)]
        return self.rng.choice(weak or pool)    # weak shobdo age

    @staticmethod
    def _is_weak(state, word: str) -> bool:
        s = state.word_stats.get(word)
        return bool(s) and s["wrong"] > s["correct"]

    def _options(self, q: Question) -> list[str]:
        opts = list(q.options)
        self.rng.shuffle(opts)      # sothik uttor jeno shobshomoy prothome na thake
        return opts