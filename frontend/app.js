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

function addMessage(text, kind = "teddy") {
  const item = document.createElement("article");
  item.className = `message ${kind}-message`;
  item.textContent = text;
  messages.append(item);
  messages.scrollTop = messages.scrollHeight;
  return item;
}

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

function hideLesson() {
  activityStage.hidden = true;
  quickReplies.classList.remove("hidden");
}

function updateProgress(progress) {
  if (!progress) return;
  document.querySelector("#level-label").textContent = `Level ${progress.level}`;
  document.querySelector("#progress-label").textContent = `${progress.correct} / ${progress.target}`;
  document.querySelector("#progress-bar").style.width = `${(progress.correct / progress.target) * 100}%`;
  document.querySelectorAll("#stars span").forEach((star, index) => star.classList.toggle("earned", index < progress.correct));
}

function setTeddyMood(mood, status) {
  [teddyAvatar, heroBear].forEach((bear) => {
    bear.classList.remove("happy", "caring", "playful");
    void bear.offsetWidth;
    bear.classList.add(mood);
  });
  teddyStatus.innerHTML = `<i></i> ${status}`;
}

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

function showError(message) {
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 3500);
}

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
