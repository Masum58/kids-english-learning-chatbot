"""Social and Emotional Learning (SEL) & Deterministic Fallback Templates.

What this file does:
    Provides curated, pedagogically sound SEL responses for children under 7:
        - Emotional awareness, validation, and calming deep breaths (sad, angry, scared).
        - Non-punitive encouragement when stuck or struggling ("That's okay! Learning takes time").
        - Playful engagement activities (animal sounds, clapping, rhymes).
        - Ultra-fast fallback replies if the LLM times out or is offline.

Connections with other files:
    - app/services/orchestrator.py: Uses these templates for Support and Engagement modes,
      and as the deterministic fallback whenever LLM generation exceeds 1.3s.
"""

GREETING = "Hi! 👋 I'm Teddy, your English friend! 🧸\nWhat do you want to do?"
CHAT_OPENER = "Let's chat! 💬 Ask me anything. Try: \"Why is the sky blue?\""
BACK_TO_QUESTION = "Ready to go back to our question? 😊"
CONVERSATION_FALLBACK = "That's a great question! 🌟 Let's ask a grown-up together too. Do you want to learn or play?"

MENU = ["📚 Learn", "🎮 Play", "💬 Chat"]
MENU_WITH_QUESTION = ["📚 Keep learning", "🎮 Play"]
ENGAGEMENT_BUTTONS = ["🔁 Again", "📚 Learn", "💬 Chat"]


def menu(has_question: bool) -> list[str]:
    """Generates the appropriate quick reply menu for the child.

    What it does:
        Returns a simplified button menu. If a quiz question is currently paused,
        prioritizes 'Keep learning' so the child can smoothly resume.

    Args:
        has_question (bool): True if there is a pending quiz question waiting.

    Returns:
        list[str]: Array of button label strings to present to the user.
    """
    return list(MENU_WITH_QUESTION if has_question else MENU)



# Emotion naming + validation + ekta chhoto kaj (breathing / boro keu / khela)
EMOTION_REPLIES = {
    "sad": "I'm sorry you feel sad 💛 It's okay to feel sad. Let's take a big breath together: in... and out. 🌬️ I'm here with you!",
    "angry": "It's okay to feel angry 💛 Angry is a big feeling. Let's breathe: in... and out. 🌬️ Do you want to tell me what happened?",
    "scared": "It's okay to feel scared 💛 You are safe here with me. Let's breathe: in... and out. 🌬️ You can tell a grown-up you love, too.",
    "tired": "You sound tired 😴 It's okay to rest. Let's take a big breath: in... and out. 🌬️ Do you want a small, easy game?",
    "lonely": "I'm sorry you feel lonely 💛 I'm your friend and I'm here! 🧸 Do you want to play with me?",
    "happy": "Yay! I'm happy that you are happy! 🎉 Happy is a great feeling! 😊 What makes you happy?",
}

STUCK = [
    "That's okay! 🌟 Everyone needs help sometimes.",
    "No problem! 💛 Let's try together.",
    "It's okay not to know! 🌈 Learning takes time.",
]
STRUGGLING = [
    "You are working so hard! 💪 Let's look at a hint together.",
    "I'm proud of you for trying! 🌟 Here is a little help.",
]
STUCK_NO_QUESTION = "I'm here to help! 💛 What do you want to do?"

ENGAGEMENT = [
    "🎵 Let's clap and count! 👏 1... 2... 3! Clap with me! Great clapping! 🎉",
    "🐮 Animal sound game! The cow says moo! The duck says quack! 🦆 Can you say quack like a duck?",
    "🌈 Colors time! Red 🍎, yellow 🍌, blue 🐳, green 🐸. Can you find something red near you?",
    "🦁 Let's pretend! Roar like a lion! 🦁 Now hop like a bunny! 🐰 Hop, hop, hop!",
    "🎶 Let's sing a happy song! La la la! 🎶 Clap your hands and dance! 💃",
]