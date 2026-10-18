/**
 * Teddy English Frontend Application Controller.
 *
 * What this file does:
 *   Manages the interactive child web interface:
 *     - Communicates with the backend POST /chat endpoint.
 *     - Maintains client-side session identity in localStorage.
 *     - Displays child-friendly picture cards and emoji options for Levels 1-3.
 *     - Triggers celebration effects (star progress bar, confetti animations).
 *     - Provides voice read-aloud functionality using the HTML5 SpeechSynthesis API.
 *
 * Connections with other files:
 *   - frontend/index.html: Provides the DOM elements manipulated by this script.
 *   - frontend/styles.css: Supplies styling, bear animations, and layout classes.
 *   - app/api/chat.py: The backend REST endpoint this script communicates with.
 */

// Dynamically use same-origin relative path when served over http/https; fallback to localhost for file://
const API_URL = window.TEDDY_API_URL || (window.location.protocol.startsWith("http") ? "" : "http://localhost:8000");
const sessionKey = "teddy-english-session";
let sessionId = localStorage.getItem(sessionKey) || null;

const messages = document.querySelector("#messages");
const quickReplies = document.querySelector("#quick-replies");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const sendButton = document.querySelector(".send-button");
const toast = document.querySelector("#toast");
const listenButton = document.querySelector("#listen-button");
const teddyAvatar = document.querySelector("#teddy-avatar");
const heroBear = document.querySelector("#hero-bear");
const teddyStatus = document.querySelector("#teddy-status");
const confetti = document.querySelector("#confetti");
const freshButton = document.querySelector("#fresh-button");
const activityStage = document.querySelector("#activity-stage");
const activityCopy = document.querySelector("#activity-copy");
const activityChoices = document.querySelector("#activity-choices");
let lastTeddyReply = "Hi, friend! I’m Teddy. What would you like to do today?";

/**
 * Appends a chat message bubble to the messages container.
 *
 * @param {string} text - Message text to display.
 * @param {string} [kind="teddy"] - Message sender type ("teddy", "user", or "typing").
 * @returns {HTMLElement} The created article element.
 */
function addMessage(text, kind = "teddy") {
  const item = document.createElement("article");
  item.className = `message ${kind}-message`;
  item.textContent = text;
  messages.append(item);
  messages.scrollTop = messages.scrollHeight;
  return item;
}

/**
 * Renders quick reply buttons below the chat log for one-tap interaction.
 *
 * @param {string[]} items - Array of button label strings or emojis.
 * @returns {void}
 */
function setQuickReplies(items) {

  quickReplies.replaceChildren();
  const isPictureQuestion = items.length >= 2 && items.length <= 4
    && items.every((item) => !/[A-Za-z0-9]/.test(item));
  quickReplies.classList.toggle("emoji-options", isPictureQuestion);
  items.forEach((item) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = item;
    if (isPictureQuestion) {
      button.classList.add("emoji-choice");
      button.setAttribute("aria-label", `Choose ${item}`);
    }
    button.addEventListener("click", () => sendMessage(item));
    quickReplies.append(button);
  });
}

/**
 * Renders the prominent visual learning card for Levels 1-3.
 *
 * @param {object} data - ChatResponse JSON payload containing reply and quick_replies.
 * @returns {void}
 */
function renderLesson(data) {
  activityStage.hidden = false;
  activityCopy.textContent = data.reply;
  activityChoices.replaceChildren();
  activityChoices.classList.toggle("picture-choices", data.quick_replies.every((choice) => !/[A-Za-z0-9]/.test(choice)));
  data.quick_replies.forEach((choice) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = choice;
    button.setAttribute("aria-label", `Choose ${choice}`);
    button.addEventListener("click", () => sendMessage(choice, true));
    activityChoices.append(button);
  });
  quickReplies.replaceChildren();
  quickReplies.classList.add("hidden");
}

/**
 * Hides the lesson activity card when switching out of learning mode.
 *
 * @returns {void}
 */
function hideLesson() {
  activityStage.hidden = true;
  quickReplies.classList.remove("hidden");
}

/**
 * Updates the 5-star progress meter and level badge on the UI.
 *
 * @param {object} progress - Contains { level, answered, correct, target }.
 * @returns {void}
 */
function updateProgress(progress) {
  if (!progress) return;
  document.querySelector("#level-label").textContent = `Level ${progress.level}`;
  document.querySelector("#progress-label").textContent = `${progress.correct} / ${progress.target}`;
  document.querySelector("#progress-bar").style.width = `${(progress.correct / progress.target) * 100}%`;
  document.querySelectorAll("#stars span").forEach((star, index) => star.classList.toggle("earned", index < progress.correct));
}

/**
 * Updates the animated mood state and status subtitle of the teddy bear avatar.
 *
 * @param {string} mood - Animation class ("happy", "caring", or "playful").
 * @param {string} status - Subtitle text displayed below Teddy's name.
 * @returns {void}
 */
function setTeddyMood(mood, status) {
  [teddyAvatar, heroBear].forEach((bear) => {
    bear.classList.remove("happy", "caring", "playful");
    void bear.offsetWidth;
    bear.classList.add(mood);
  });
  teddyStatus.innerHTML = `<i></i> ${status}`;
}

/**
 * Creates celebratory confetti animations when a child succeeds or levels up.
 *
 * @returns {void}
 */
function celebrate() {
  const colors = ["#ff7fad", "#ffc94b", "#61c7e8", "#8b70f1", "#65d7a4"];
  for (let index = 0; index < 42; index += 1) {
    const piece = document.createElement("span");
    piece.className = "confetti-piece";
    piece.style.left = `${Math.random() * 100}%`;
    piece.style.background = colors[index % colors.length];
    piece.style.setProperty("--drift", `${(Math.random() - .5) * 240}px`);
    piece.style.animationDelay = `${Math.random() * .25}s`;
    confetti.append(piece);
    piece.addEventListener("animationend", () => piece.remove());
  }
}

/**
 * Inspects bot response text and operational mode to determine the appropriate mood.
 *
 * @param {object} data - The ChatResponse object from the server.
 * @returns {[string, string]} Tuple of [moodClass, statusText].
 */
function responseMood(data) {
  const reply = data.reply.toLowerCase();
  if (data.mode === "support") return ["caring", "I’m here with you 💛"];
  if (data.mode === "engagement") return ["playful", "Let’s play together! 🎮"];
  if (/(great job|wow, you got it|super|yay, that's right|you got it this time|level up|english star)/.test(reply)) {
    celebrate();
    return ["happy", "You did something amazing! ⭐"];
  }
  return ["happy", "Ready to learn with you"];
}

/**
 * Reads Teddy's most recent reply out loud using the browser SpeechSynthesis API.
 *
 * @returns {void}
 */
function speakLastReply() {
  if (!("speechSynthesis" in window)) {
    showError("Listening is not available in this browser.");
    return;
  }
  window.speechSynthesis.cancel();
  const speech = new SpeechSynthesisUtterance(lastTeddyReply.replace(/[🧸⭐🎉🌟💛🌈💪🌬️😊👋]/gu, ""));
  const voices = window.speechSynthesis.getVoices();
  const preferredVoice = voices.find((voice) => /samantha|ava|zira|google us english|karen/i.test(voice.name))
    || voices.find((voice) => /^en(-|_)(us|gb|au)/i.test(voice.lang))
    || voices.find((voice) => /^en/i.test(voice.lang));
  if (preferredVoice) speech.voice = preferredVoice;
  speech.rate = 0.76;
  speech.pitch = 1.08;
  speech.onstart = () => listenButton.classList.add("speaking");
  speech.onend = speech.onerror = () => listenButton.classList.remove("speaking");
  window.speechSynthesis.speak(speech);
}

/**
 * Displays a temporary error or warning notification toast at the bottom of the screen.
 *
 * @param {string} message - Text notification to display.
 * @returns {void}
 */
function showError(message) {
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 3500);
}

/**
 * Submits user input to the backend POST /chat endpoint and updates interface state.
 *
 * @param {string} rawMessage - Message text or option selected by the user.
 * @param {boolean} [isLessonChoice=false] - True if clicked from visual activity stage.
 * @returns {Promise<void>}
 */
async function sendMessage(rawMessage, isLessonChoice = false) {
  const message = rawMessage.trim();
  if (!message || sendButton.disabled) return;
  input.value = "";
  if (!isLessonChoice) addMessage(message, "user");
  sendButton.disabled = true;
  const typing = addMessage("Teddy is thinking...", "typing");
  try {
    const response = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message }),
    });
    if (!response.ok) throw new Error("Could not reach Teddy");
    const data = await response.json();
    sessionId = data.session_id;
    localStorage.setItem(sessionKey, sessionId);
    typing.remove();
    lastTeddyReply = data.reply;
    if (data.mode === "learning") {
      renderLesson(data);
    } else {
      hideLesson();
      addMessage(data.reply, "teddy");
      setQuickReplies(data.quick_replies);
    }
    updateProgress(data.progress);
    const [mood, status] = responseMood(data);
    setTeddyMood(mood, status);
  } catch (error) {
    typing.remove();
    showError("Teddy needs a moment. Is the server running?");
  } finally {
    sendButton.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (event) => { event.preventDefault(); sendMessage(input.value); });
listenButton.addEventListener("click", speakLastReply);
freshButton.addEventListener("click", () => {
  sessionId = null;
  localStorage.removeItem(sessionKey);
  window.location.reload();
});
if ("speechSynthesis" in window) window.speechSynthesis.getVoices();
