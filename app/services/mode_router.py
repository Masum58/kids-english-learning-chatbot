"""Child Mode & Mood Detection Router.

What this file does:
    Detects the child's interaction mode, emotional state, or cognitive intent in
    under 2 milliseconds. Categorizes input into four primary modes:
        - 'learning': Active curriculum quizzes and answers.
        - 'support': Comforting distress or providing scaffolded hints when stuck.
        - 'engagement': Playful micro-games, songs, and rhymes.
        - 'conversation': Curious questions and friendly chit-chat.

Decision Priority:
    1. Correct answer match (if a quiz question is pending)
    2. Negative emotion / feeling stuck (support mode takes priority over drills)
    3. Option tap (distractor options count as answers)
    4. Explicit play intent or continuing a game
    5. Learn intent
    6. Greetings / check-ins / topic change
    7. Curious questions ("Why?", "How?")
    8. Fallback to general conversational chat

Connections with other files:
    - app/data/lessons.py: Looks up active Question objects via QUESTIONS_BY_ID.
    - app/services/learning_engine.py: Uses normalize(), is_correct(), and is_struggling().
    - app/services/orchestrator.py: Calls detect() on every non-flagged message to route turns.
"""
import re
from dataclasses import dataclass

from app.data.lessons import QUESTIONS_BY_ID
from app.services.learning_engine import LearnerState, LearningEngine, is_correct, normalize

LEARNING, CONVERSATION, ENGAGEMENT, SUPPORT = "learning", "conversation", "engagement", "support"

# Explanatory reason constants passed back to client
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
LEARN_WORDS = ("teach", "learn", "lean", "learning", "lesson", "quiz", "practice", "next", "start",
               "continue", "more", "yes", "yeah", "ok", "okay", "again")
GREETINGS = {"hi", "hello", "hey", "hi there", "hello there", "hey there",
             "good morning", "good afternoon", "good evening"}
CHAT_OPENERS = {"chat", "lets chat"}
QUESTION_WORDS = {"why", "how", "who", "where", "when"}
TOPIC_CHANGE_WORDS = ("change topic", "change the topic", "something else", "talk about", "are you there", "hello teddy")
FRIENDLY_CHECK_IN_WORDS = ("how are you", "how do you feel", "are you happy")

_engine = LearningEngine()


@dataclass(frozen=True)
class Decision:
    """Represents the mode routing decision for the current turn.

    Attributes:
        mode: The detected operational mode (learning, conversation, engagement, support).
        reason: Machine-readable explanation tag describing why this mode was chosen.
        is_answer: True if the child's message should be evaluated as a lesson answer.
        emotion: Identified emotional state (e.g., 'sad', 'angry', 'happy') or None.
    """
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
    # If child has missed 3 in a row, intervene with support mode once before grading further
    if _engine.is_struggling(state) and previous_mode != SUPPORT:
        return Decision(SUPPORT, STRUGGLING)
    return Decision(LEARNING, "answered_pending_question", is_answer=True)


def detect(text: str, state: LearnerState, previous_mode: str = CONVERSATION) -> Decision:
    """Detects the child's active mode, intent, and emotional state.

    What it does:
        Applies hierarchical rules to classify the child's input. Balances educational
        progress with emotional awareness, ensuring stuck or distressed children receive
        comfort rather than relentless quiz grading.

    Args:
        text (str): Raw message string sent by the child.
        state (LearnerState): Current learning state including any pending question.
        previous_mode (str): Mode active during the previous turn (default 'conversation').

    Returns:
        Decision: Immutable Decision object containing mode, reason, is_answer, and emotion.
    """

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
    if _has(t, TOPIC_CHANGE_WORDS):
        return Decision(CONVERSATION, "change_topic")
    if _has(t, FRIENDLY_CHECK_IN_WORDS):
        return Decision(CONVERSATION, "friendly_check_in")
    if words in GREETINGS:
        return Decision(CONVERSATION, GREETING)
    if words in CHAT_OPENERS:
        return Decision(CONVERSATION, CHAT_OPENER)
    if "?" in text or (tokens and tokens[0] in QUESTION_WORDS):
        return Decision(CONVERSATION, "child_question")
    if _has(t, POSITIVE):
        return Decision(CONVERSATION, "emotion:happy", emotion="happy")

    # 5. Pending question er somoy ek-word/dui-word response answer hote pare.
    # Boro message ke vul kore answer dhorle "are you there?"-er moto normal chat haray jay.
    if q and t and len(t.split()) <= 2:
        return _answer(state, previous_mode)

    return Decision(CONVERSATION, "general_chat")
