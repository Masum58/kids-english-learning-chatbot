"""Pedagogical Curriculum & Lesson Bank (Levels 1, 2, 3).

What this file does:
    Stores the structured early-childhood English curriculum data for children under 7.
    Contains vocabulary, visual emoji cues, hints, options, and accepted answers
    separated into Level 1 (Single words), Level 2 (Mini fill-in sentences), and
    Level 3 (Conversational responses & basic syntax).

Connections with other files:
    - app/services/learning_engine.py: Uses QUESTIONS_BY_LEVEL to select next questions,
      re-introduce weak words, and evaluate child answers.
    - app/services/orchestrator.py: Uses QUESTIONS_BY_ID to look up hints when a child
      struggles or asks for help in Support mode.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Question:
    """Represents a single pedagogical lesson question.

    Attributes:
        id: Unique identifier string for the question (e.g., 'l1_cat').
        level: Pedagogical level (1 = single words, 2 = cloze sentences, 3 = conversational).
        word: The core vocabulary word being taught (used for weak-word tracking).
        prompt: Display question asked to the child.
        options: Choices presented as clickable buttons or emojis.
        answer: The exact primary correct answer string matching one of the options.
        hint: Encouraging clue shown if the child answers incorrectly or asks for help.
        also_accept: Alternative acceptable strings if the child types words instead of clicking.
    """
    id: str
    level: int
    word: str                       # weak-word tracking er jonno
    prompt: str
    options: tuple[str, ...]
    answer: str                     # options er moddhe thakte hobe
    hint: str
    also_accept: tuple[str, ...] = ()   # shishu type korle onno je uttor gulo thik



# L1: shobdo chena (emoji dekhe)
L1 = [
    Question("l1_cat", 1, "cat", "Which one is a cat?", ("🐱", "🐶", "🍎"), "🐱", "It says meow! Find the kitty.", ("cat",)),
    Question("l1_dog", 1, "dog", "Which one is a dog?", ("🐶", "🐱", "⚽"), "🐶", "It says woof woof! Find the puppy.", ("dog",)),
    Question("l1_apple", 1, "apple", "Which one is an apple?", ("🍎", "🐟", "🐱"), "🍎", "It is a red fruit. Yum!", ("apple",)),
    Question("l1_ball", 1, "ball", "Which one is a ball?", ("⚽", "🍎", "🐶"), "⚽", "You can kick it and play with it!", ("ball",)),
    Question("l1_sun", 1, "sun", "Which one is the sun?", ("☀️", "🐟", "🍌"), "☀️", "It is up in the sky. It is bright and warm.", ("sun",)),
    Question("l1_fish", 1, "fish", "Which one is a fish?", ("🐟", "🐦", "☀️"), "🐟", "It lives in the water and can swim.", ("fish",)),
    Question("l1_banana", 1, "banana", "Which one is a banana?", ("🍌", "🍎", "🐶"), "🍌", "It is a yellow fruit. Monkeys love it!", ("banana",)),
    Question("l1_bird", 1, "bird", "Which one is a bird?", ("🐦", "🐱", "⚽"), "🐦", "It has wings and it can fly.", ("bird",)),
]

# L2: chhoto sentence complete kora
L2 = [
    Question("l2_cat", 2, "cat", "🐱 This is a ___.", ("cat", "dog", "ball"), "cat", "Look at the picture. It says meow!"),
    Question("l2_dog", 2, "dog", "🐶 I see a ___.", ("dog", "cat", "fish"), "dog", "Look at the picture. It says woof!"),
    Question("l2_apple", 2, "apple", "🍎 I eat an ___.", ("apple", "ball", "sun"), "apple", "Which one can you eat? It is red!"),
    Question("l2_ball", 2, "ball", "⚽ I kick the ___.", ("ball", "apple", "bird"), "ball", "What do we kick when we play?"),
    Question("l2_sun", 2, "sun", "☀️ The ___ is hot.", ("sun", "fish", "dog"), "sun", "It is in the sky and it is warm."),
    Question("l2_fish", 2, "fish", "🐟 The ___ can swim.", ("fish", "bird", "ball"), "fish", "Who lives in the water?"),
    Question("l2_bird", 2, "bird", "🐦 The ___ can fly.", ("bird", "dog", "apple"), "bird", "Who has wings?"),
    Question("l2_banana", 2, "banana", "🍌 I like the yellow ___.", ("banana", "cat", "ball"), "banana", "It is a yellow fruit."),
]

# L3: shoja communication (MVP te multiple choice)
L3 = [
    Question("l3_hello", 3, "hello", "Your friend says: Hello! 👋 What do you say?", ("Hello!", "Goodbye!", "I am a dog."), "Hello!", "When we meet a friend, we say hi!", ("hi",)),
    Question("l3_what", 3, "cat", "What is this? 🐱", ("It is a cat.", "It is a dog.", "It is an apple."), "It is a cat.", "Look at the picture. It says meow!"),
    Question("l3_feel", 3, "feelings", "How are you? 😊", ("I am happy.", "I am a cat.", "I am an apple."), "I am happy.", "Tell me how you feel!", ("happy", "i am good", "i am fine")),
    Question("l3_thanks", 3, "thanks", "Your friend says: Thank you! 🎁 What do you say?", ("You are welcome!", "Goodbye!", "I am a dog."), "You are welcome!", "When someone says thank you, we say something kind.", ("welcome",)),
    Question("l3_sun", 3, "sun", "What color is the sun? ☀️", ("Yellow", "Blue", "Green"), "Yellow", "It is bright, like a banana!"),
    Question("l3_dog", 3, "dog", "Which one is right? 🐶", ("I like dogs.", "Like dogs I.", "Dogs I am like."), "I like dogs.", "Say it in order: I... like... dogs."),
    Question("l3_apple", 3, "apple", "What color is an apple? 🍎", ("Red", "Blue", "Black"), "Red", "Think of a strawberry!"),
]

QUESTIONS_BY_LEVEL = {1: L1, 2: L2, 3: L3}
QUESTIONS_BY_ID = {q.id: q for qs in QUESTIONS_BY_LEVEL.values() for q in qs}