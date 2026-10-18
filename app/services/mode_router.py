"""Mode Router: shishu ekhon ki chay? Rule-based, fast (~ms), explain kora jay.
Priority: correct answer > emotion/stuck > option tap > play > learn > greeting > question > answer > chat"""
import re
from dataclasses import dataclass

from app.data.lessons import QUESTIONS_BY_ID
from app.services.learning_engine import LearnerState, LearningEngine, is_correct, normalize

LEARNING, CONVERSATION, ENGAGEMENT, SUPPORT = "learning", "conversation", "engagement", "support"

# reason constants (orchestrator o use kore)
GREETING = "greeting"
CHAT_OPENER = "chat_opener"
STUCK_REASON = "child_stuck"
STRUGGLING = "child_struggling"

NEGATIVE_EMOTIONS = {
    "sad": ("sad", "cry", "crying", "unhappy", "upset", "miss my"),
    "angry": ("angry", "mad", "hate"),
    "scared": ("scared", "afraid", "frightened", "nightmare", "bad dream", "scary"),
    "tired": ("tired", "sleepy"),
    "lonely": ("lonely", "alone", "no friends", "nobody likes me"),
}
POSITIVE = ("happy", "excited", "yay", "great")
STUCK = ("dont know", "idk", "dunno", "cant", "too hard", "help", "dont understand", "dont get it")
ENGAGEMENT_WORDS = ("play", "game", "fun", "song", "sing", "rhyme", "joke", "bored", "dance")
PLAY_CONTINUATIONS = {"yes", "yeah", "yep", "ok", "okay", "more", "again"}
LEARN_WORDS = ("teach", "learn", "learning", "lesson", "quiz", "practice", "next", "start",
               "continue", "more", "yes", "yeah", "ok", "okay", "again")
GREETINGS = {"hi", "hello", "hey", "hi there", "hello there", "hey there",
             "good morning", "good afternoon", "good evening"}
CHAT_OPENERS = {"chat", "lets chat"}
QUESTION_WORDS = {"why", "how", "who", "where", "when"}

_engine = LearningEngine()


@dataclass(frozen=True)
class Decision:
    mode: str
    reason: str
    is_answer: bool = False
    emotion: str | None = None


def _has(t: str, phrases) -> bool:
    return any(re.search(rf"\b{re.escape(p)}\b", t) for p in phrases)


def _negative_emotion(t: str) -> str | None:
    for emotion, words in NEGATIVE_EMOTIONS.items():
        if _has(t, words):
            return emotion
    return None


def _answer(state: LearnerState, previous_mode: str) -> Decision:
    # porpor 3 ta bhul hole ekbar support dei, tarpor abar chesta korte dei
    if _engine.is_struggling(state) and previous_mode != SUPPORT:
        return Decision(SUPPORT, STRUGGLING)
    return Decision(LEARNING, "answered_pending_question", is_answer=True)


def detect(text: str, state: LearnerState, previous_mode: str = CONVERSATION) -> Decision:
    t = normalize(text)
    words = " ".join(re.findall(r"[a-z]+", t))
    tokens = words.split()
    q = QUESTIONS_BY_ID.get(state.pending_question_id) if state.pending_question_id else None

    # 1. sothik uttor shobar upore
    if q and is_correct(q, text):
        return Decision(LEARNING, "answered_pending_question", is_answer=True)

    # 2. mon kharap ba atke gele: support (learning er cheye boro)
    emotion = _negative_emotion(t)
    if emotion:
        return Decision(SUPPORT, f"emotion:{emotion}", emotion=emotion)
    if _has(t, STUCK):
        return Decision(SUPPORT, STUCK_REASON)

    # 3. bhul option e tap korle seta-o uttor
    if q and t in {normalize(o) for o in q.options}:
        return _answer(state, previous_mode)

    # 4. intent
    if _has(t, ENGAGEMENT_WORDS) or ("again" in tokens and previous_mode == ENGAGEMENT):
        return Decision(ENGAGEMENT, "wants_to_play")
    # A child often answers a game prompt with only "yes". Keep the play context;
    # do not unexpectedly turn this into a lesson.
    if previous_mode == ENGAGEMENT and words in PLAY_CONTINUATIONS:
        return Decision(ENGAGEMENT, "continues_play")
    if _has(t, LEARN_WORDS):
        return Decision(LEARNING, "wants_to_learn")
    if words in GREETINGS:
        return Decision(CONVERSATION, GREETING)
    if words in CHAT_OPENERS:
        return Decision(CONVERSATION, CHAT_OPENER)
    if "?" in text or (tokens and tokens[0] in QUESTION_WORDS):
        return Decision(CONVERSATION, "child_question")
    if _has(t, POSITIVE):
        return Decision(CONVERSATION, "emotion:happy", emotion="happy")

    # 5. proshno pending, choto message: uttor dhorbo
    if q and t and len(t.split()) <= 5:
        return _answer(state, previous_mode)

    return Decision(CONVERSATION, "general_chat")
