"""Pedagogical Learning Engine (Levels 1-3).

What this file does:
    Implements pure pedagogical logic: serves level-appropriate quiz questions,
    grades child responses with forgiving token normalization, provides gentle hints
    on first mistake, reveals answers on second mistake, tracks weak words for spaced
    repetition, and promotes children upon scoring 4 out of 5 without ever demoting.

Connections with other files:
    - app/data/lessons.py: Supplies curriculum questions for Levels 1, 2, and 3.
    - app/repository.py: Maps database records to and from LearnerState.
    - app/services/orchestrator.py: Calls engine.start(), engine.answer(), and engine.progress().
    - app/services/mode_router.py: Uses engine.is_struggling() to detect learning distress.
"""
import random
import re
from dataclasses import dataclass, field

from app.data.lessons import QUESTIONS_BY_ID, QUESTIONS_BY_LEVEL, Question

WINDOW = 5          # Sliding window size of recent answers
PASS_MARK = 4       # Minimum correct answers in window required for level advancement
MAX_LEVEL = 3
RECENT_MEMORY = 3   # Bounded history to prevent immediate question repetition

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
    """In-memory domain state representing the child's learning journey.

    Attributes:
        level: Current pedagogical level (1, 2, or 3).
        last_answers: Recent boolean results (first-try attempts only) within the sliding window.
        pending_question_id: ID of the active question waiting for an answer, or None.
        attempts: Number of consecutive incorrect tries on the active question.
        recent_question_ids: Circular buffer of recently presented questions.
        word_stats: Aggregated dictionary of {word: {'correct': int, 'wrong': int}}.
    """
    level: int = 1
    last_answers: list[bool] = field(default_factory=list)
    pending_question_id: str | None = None
    attempts: int = 0
    recent_question_ids: list[str] = field(default_factory=list)
    word_stats: dict[str, dict[str, int]] = field(default_factory=dict)


@dataclass
class Turn:
    """Result of processing a pedagogical learning turn.

    Attributes:
        reply: Message text to display and speak to the child.
        quick_replies: List of answer choices or options presented to the child.
        question_id: ID of the question active at the end of this turn.
        graded: True if a first-attempt answer was evaluated and needs DB logging.
        correct: True if the answer was correct, False if incorrect, None if question presented.
        word: Target vocabulary word if this turn was graded.
        level_up: True if the child advanced to a new level during this turn.
        mastered: True if the child completed Level 3 with honors.
    """
    reply: str
    quick_replies: list[str]
    question_id: str | None
    graded: bool = False
    correct: bool | None = None
    word: str | None = None
    level_up: bool = False
    mastered: bool = False


# ---------- Answer matching helpers ----------
_LEAD = ("it is ", "its ", "this is ", "a ", "an ", "the ")


def normalize(text: str) -> str:
    """Normalizes raw input text for clean comparison.

    What it does:
        Converts text to lowercase, removes emoji variation selectors,
        strips punctuation marks, and collapses whitespace.

    Args:
        text (str): Input string from the child.

    Returns:
        str: Normalized clean string.
    """
    text = text.lower().replace("\ufe0f", "")
    text = re.sub(r"[.,!?;:'\"’]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _canon(text: str) -> str:
    """Removes common natural language prefixes like 'it is a...' from answers."""
    t = normalize(text)
    changed = True
    while changed:
        changed = False
        for prefix in _LEAD:
            if t.startswith(prefix):
                t, changed = t[len(prefix):], True
    return t


def is_correct(q: Question, text: str) -> bool:
    """Evaluates whether the child's input matches the question's expected answer.

    What it does:
        Canonicalizes both the child's answer and the acceptable answers defined
        in the Question dataclass (including 'also_accept' synonyms).

    Args:
        q (Question): The active lesson question.
        text (str): Raw string submitted by the child.

    Returns:
        bool: True if matched, False otherwise.
    """
    given = _canon(text)
    return bool(given) and given in {_canon(a) for a in (q.answer, *q.also_accept)}


# ---------- Learning Engine ----------
class LearningEngine:
    """Core pedagogical progression and quiz engine."""

    def __init__(self, rng: random.Random | None = None):
        """Initializes the engine with an optional seeded random generator."""
        self.rng = rng or random.Random()

    def start(self, state: LearnerState) -> Turn:
        """Starts a new learning session or resumes an ongoing question.

        Args:
            state (LearnerState): Current learning state of the child.

        Returns:
            Turn: Formatted question prompt with randomized choices.
        """
        if state.pending_question_id is None:
            self._set_pending(state, self._pick(state))
            prefix = LEVEL_INTRO[state.level]
        else:
            prefix = "Let's keep going! 😊"
        q = QUESTIONS_BY_ID[state.pending_question_id]
        return Turn(f"{prefix}\n{q.prompt}", self._options(q), q.id)

    def answer(self, state: LearnerState, text: str) -> Turn:
        """Evaluates an answer from the child and manages progression.

        What it does:
            - If correct on first try: praises, records success, checks for level-up, and presents next question.
            - If incorrect on first try: gives an encouraging hint, keeps question active, does not advance.
            - If incorrect on second try: kindly reveals the answer and moves to the next question.

        Args:
            state (LearnerState): Child's active learning state.
            text (str): Answer string submitted by the child.

        Returns:
            Turn: Evaluation result with next step feedback and choices.
        """
        if state.pending_question_id is None:
            return self.start(state)
        q = QUESTIONS_BY_ID[state.pending_question_id]
        if is_correct(q, text):
            return self._on_correct(state, q)
        return self._on_wrong(state, q)

    def hint(self, state: LearnerState) -> str | None:
        """Returns the hint for the currently pending question, if any.

        Args:
            state (LearnerState): Child's active learning state.

        Returns:
            str | None: The hint text or None if no question is pending.
        """
        if state.pending_question_id is None:
            return None
        return QUESTIONS_BY_ID[state.pending_question_id].hint

    def is_struggling(self, state: LearnerState) -> bool:
        """Determines if the child is experiencing cognitive struggle.

        What it does:
            Checks if the child has missed their last 3 consecutive questions.

        Args:
            state (LearnerState): Child's active learning state.

        Returns:
            bool: True if the child missed 3 in a row; False otherwise.
        """
        return len(state.last_answers) >= 3 and not any(state.last_answers[-3:])

    def progress(self, state: LearnerState) -> dict:
        """Builds a progress dictionary for UI display.

        Args:
            state (LearnerState): Child's active learning state.

        Returns:
            dict: Contains 'level', 'answered', 'correct', and 'target'.
        """
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