"""Child Safety & Privacy Filter (COPPA Guardrails).

What this file does:
    Acts as a zero-latency safety firewall (<1ms) running before any LLM invocation
    or database storage. Intercepts three critical categories:
        1. 'unsafe': Self-harm, physical harm, or abuse indicators. Provides immediate
           compassionate escalation instructing the child to notify a trusted grown-up.
        2. 'personal_info': Phone numbers, emails, addresses, or personal names.
           Redacts private data to protect young children's identity.
        3. 'memory_question': Questions asking if Teddy remembers names or private data.
           Reassures the child that private details are never stored.

Connections with other files:
    - app/services/orchestrator.py: Calls safety.check() as the very first step
      of message handling. If flagged, returns safe pre-approved canned replies.
"""
import re

UNSAFE_PATTERNS = [re.compile(p) for p in (
    r"\b(hurt|hurts|hurting|hit|hits|hitting|touch|touches|touched|slap|slaps)\s+me\b",
    r"\b(kill|hurt)\s+myself\b",
    r"\bwant\s+to\s+die\b",
    r"\b(not|isnt|isn't)\s+safe\b",
    r"\b(scared|afraid)\s+to\s+go\s+home\b",
)]

PERSONAL_PATTERNS = [re.compile(p) for p in (
    r"\d{6,}",                                   # Looks like a phone number
    r"\bmy\s+(home\s+)?address\b",
    r"\bi\s+live\s+(at|in)\b",
    r"\bmy\s+phone\b",
    r"\bmy\s+name\s+is\b",
    r"\bmy\s+school\b",
    r"\S+@\S+\.\S+",                             # Email pattern
)]

MEMORY_QUESTION_PATTERNS = [re.compile(p) for p in (
    r"\bwhat(?:'s| is| was) my name\b",
    r"\bdo you remember my name\b",
    r"\bdo you (?:remember|memorize) (?:anything|something)\b",
    r"\bare you (?:remembering|memorizing|memorize) (?:anything|something)\b",
)]

UNSAFE_REPLY = (
    "I'm so glad you told me 💛 You are important.\n"
    "Please tell a grown-up you trust, like Mum, Dad or your teacher, right now. They can help you."
)
PRIVACY_REPLY = (
    "Thank you for telling me! 😊 But let's keep names, phone numbers and addresses a secret. 🤫\n"
    "Let's learn or play!"
)
MEMORY_REPLY = (
    "I don't remember names or private things. 🤫 That helps keep you safe!\n"
    "Would you like to learn or play?"
)


def check(text: str) -> str | None:
    """Scans incoming text against pre-compiled child safety and privacy regex patterns.

    What it does:
        Normalizes apostrophes and lowercases text, then tests against unsafe,
        personal info, and memory probing patterns.

    Args:
        text (str): Raw string message sent by the child.

    Returns:
        str | None:
            - 'unsafe' if distress, self-harm, or abuse is detected.
            - 'personal_info' if PII (phone, address, email, name) is detected.
            - 'memory_question' if the child asks whether the bot remembers private data.
            - None if the message passed all safety checks.
    """
    t = text.lower().replace("’", "'")
    if any(p.search(t) for p in UNSAFE_PATTERNS):
        return "unsafe"
    if any(p.search(t) for p in PERSONAL_PATTERNS):
        return "personal_info"
    if any(p.search(t) for p in MEMORY_QUESTION_PATTERNS):
        return "memory_question"
    return None

