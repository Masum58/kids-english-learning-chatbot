"""Child safety: bipodjonok kotha ar personal info LLM e jawar age-i atkano."""
import re

UNSAFE_PATTERNS = [re.compile(p) for p in (
    r"\b(hurt|hurts|hurting|hit|hits|hitting|touch|touches|touched|slap|slaps)\s+me\b",
    r"\b(kill|hurt)\s+myself\b",
    r"\bwant\s+to\s+die\b",
    r"\b(not|isnt|isn't)\s+safe\b",
    r"\b(scared|afraid)\s+to\s+go\s+home\b",
)]

PERSONAL_PATTERNS = [re.compile(p) for p in (
    r"\d{6,}",                                   # phone number moto
    r"\bmy\s+(home\s+)?address\b",
    r"\bi\s+live\s+(at|in)\b",
    r"\bmy\s+phone\b",
    r"\bmy\s+name\s+is\b",
    r"\bmy\s+school\b",
    r"\S+@\S+\.\S+",                             # email
)]

UNSAFE_REPLY = (
    "I'm so glad you told me 💛 You are important.\n"
    "Please tell a grown-up you trust, like Mum, Dad or your teacher, right now. They can help you."
)
PRIVACY_REPLY = (
    "Thank you for telling me! 😊 But let's keep names, phone numbers and addresses a secret. 🤫\n"
    "Let's learn or play!"
)


def check(text: str) -> str | None:
    """'unsafe' | 'personal_info' | None"""
    t = text.lower().replace("’", "'")
    if any(p.search(t) for p in UNSAFE_PATTERNS):
        return "unsafe"
    if any(p.search(t) for p in PERSONAL_PATTERNS):
        return "personal_info"
    return None